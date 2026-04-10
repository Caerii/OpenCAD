from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from opencad.api_app import create_api_app
from opencad_kernel.core.errors import Failure
from opencad_kernel.core.models import MeshData, OperationResult, Success
from opencad_kernel.core.snapshot import SnapshotV1
from opencad_kernel.operations.handlers import OpenCadKernel
from opencad_kernel.operations.registry import OperationRegistry
from opencad_kernel.operations.schemas import SelectorQuery

logger = logging.getLogger(__name__)

# ── Backend selection ───────────────────────────────────────────────

_BACKEND_NAME = os.environ.get("OPENCAD_KERNEL_BACKEND", "analytic")


def _build_kernel() -> OpenCadKernel:
    if _BACKEND_NAME == "occt":
        try:
            from opencad_kernel.core.occt_backend import OcctBackend
        except ImportError as exc:
            raise RuntimeError(
                "OPENCAD_KERNEL_BACKEND=occt but CadQuery/OCP is not installed.  "
                "Install with:  pip install -e '.[occt]'"
            ) from exc
        backend = OcctBackend()
        logger.info("Kernel started with OCCT backend")
        return OpenCadKernel(backend=backend)
    else:
        logger.info("Kernel started with analytic (stub) backend")
        return OpenCadKernel()


app: FastAPI = create_api_app(title="OpenCAD Kernel", version="0.2.0")
_KERNEL = _build_kernel()
_REGISTRY = OperationRegistry(_KERNEL)


class OperationCallRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


# ── Health ──────────────────────────────────────────────────────────


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "backend": _BACKEND_NAME}


# ── Operations ──────────────────────────────────────────────────────


@app.get("/operations", response_model=list[str])
def list_operations() -> list[str]:
    return _REGISTRY.list_operations()


# ── Operation log (must be before /operations/{name} to avoid capture) ──


@app.get("/operations/log")
def get_operation_log(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    entries = _REGISTRY.get_log(offset=offset, limit=limit)
    return [e.model_dump() for e in entries]


@app.get("/operations/log/{entry_id}")
def get_log_entry(entry_id: str) -> dict[str, Any]:
    entry = _REGISTRY.get_log_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Log entry '{entry_id}' not found.")
    return entry.model_dump()


# ── Snapshot ────────────────────────────────────────────────────────


@app.get("/snapshot", response_model=SnapshotV1)
def get_snapshot() -> SnapshotV1:
    """Return a versioned snapshot of the current kernel state."""
    return SnapshotV1(
        entries=_REGISTRY.get_log(offset=0, limit=len(_REGISTRY.log)),
        shape_ids=_KERNEL.store.all_ids(),
    )


# ── Replay (must be before /operations/{name} to avoid capture) ─────


class ReplayRequest(BaseModel):
    entries: list[dict[str, Any]]


@app.post("/operations/replay")
def replay_operations(request: ReplayRequest) -> dict[str, Any]:
    """Replay operation log entries against a fresh kernel.

    Each entry may carry ``id``, ``timestamp``, and ``result_shape_id``
    fields.  When present they are forwarded to the registry so the
    replayed state is identity-identical to the original.
    """
    fresh_kernel = _build_kernel()
    fresh_registry = OperationRegistry(fresh_kernel)
    results: list[dict[str, Any]] = []

    for entry in request.entries:
        op_name = entry.get("operation", "")
        params = entry.get("params", {})
        result = fresh_registry.call(
            op_name,
            params,
            replay_entry_id=entry.get("id"),
            replay_timestamp=entry.get("timestamp"),
            replay_shape_id=entry.get("result_shape_id"),
        )
        if isinstance(result, Success):
            results.append({"ok": True, "shape_id": result.shape_id, "operation": op_name})
        else:
            results.append({"ok": False, "code": result.code, "message": result.message, "operation": op_name})

    return {
        "replayed": len(results),
        "results": results,
        "shape_ids": fresh_kernel.store.all_ids(),
    }


# ── Operation call (wildcard — must come after specific routes) ─────


@app.get("/operations/{name}/schema")
def get_operation_schema(name: str) -> dict[str, Any]:
    try:
        return _REGISTRY.get_json_schema(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/operations/{name}", response_model=Success | Failure)
def call_operation(name: str, request: OperationCallRequest) -> OperationResult:
    return _REGISTRY.call(name, request.payload)


# ── Topology endpoints ──────────────────────────────────────────────


@app.get("/shapes/{shape_id}/topology")
def get_topology(shape_id: str) -> dict[str, Any]:
    """Return the full topology map (faces + edges with stable refs)."""
    try:
        topo = _KERNEL.get_topology(shape_id)
        return topo.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/shapes/{shape_id}/faces")
def get_faces(shape_id: str) -> list[dict[str, Any]]:
    """List all face refs for a shape."""
    try:
        topo = _KERNEL.get_topology(shape_id)
        return [f.model_dump() for f in topo.faces]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/shapes/{shape_id}/edges")
def get_edges(shape_id: str) -> list[dict[str, Any]]:
    """List all edge refs for a shape."""
    try:
        topo = _KERNEL.get_topology(shape_id)
        return [e.model_dump() for e in topo.edges]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/shapes/{shape_id}/select")
def select_subshapes(shape_id: str, query: SelectorQuery) -> list[dict[str, Any]]:
    """Run a selector query against the shape's topology."""
    try:
        results = _KERNEL.select_subshapes(shape_id, query)
        return [r.model_dump() for r in results]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Mesh endpoints ──────────────────────────────────────────────────


@app.get("/shapes/{shape_id}/mesh", response_model=MeshData)
def get_mesh(
    shape_id: str,
    deflection: float = Query(default=0.1, gt=0.0),
) -> MeshData:
    try:
        return _KERNEL.tessellate(shape_id, deflection)
    except NotImplementedError as exc:
        print(exc)
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/shapes/{shape_id}/mesh/stream")
async def stream_mesh(
    shape_id: str,
    deflection: float = Query(default=0.1, gt=0.0),
) -> StreamingResponse:
    """Stream tessellated mesh face-by-face as Server-Sent Events."""
    backend = _KERNEL.backend
    if backend is None:
        raise HTTPException(
            status_code=501,
            detail="Streaming tessellation requires an OCCT backend.",
        )

    # Verify shape exists before starting the stream
    if backend.store.get(shape_id) is None:
        raise HTTPException(status_code=404, detail=f"Shape '{shape_id}' not found.")

    async def _event_generator():
        try:
            from opencad_kernel.core.occt_backend import OcctBackend

            if not isinstance(backend, OcctBackend):
                yield f"data: {json.dumps({'error': 'Backend does not support face streaming'})}\n\n"
                return

            total = backend.count_faces(shape_id)
            for face_idx in range(total):
                mesh, _ = backend.tessellate_face(shape_id, face_idx, deflection)
                chunk = {
                    "vertices": mesh.vertices,
                    "faces": mesh.faces,
                    "normals": mesh.normals,
                    "faceIndex": face_idx,
                    "totalFaces": total,
                    "done": face_idx == total - 1,
                }
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
