from __future__ import annotations

from fastapi.testclient import TestClient

from opencad_agent.api import app
from opencad_agent.models import ChatRequest
from opencad_agent.prompting import build_system_prompt
from opencad_agent.service import OpenCadAgentService
from opencad_agent.tools import ToolRuntime
from opencad_kernel.core.models import Success
from opencad_kernel.operations.handlers import OpenCadKernel
from opencad_kernel.operations.registry import OperationRegistry
from opencad_tree.models import FeatureNode, FeatureTree


def _seed_tree() -> FeatureTree:
    return FeatureTree(
        root_id="root",
        nodes={
            "root": FeatureNode(
                id="root",
                name="Root",
                operation="seed",
                parameters={},
                depends_on=[],
                status="built",
                shape_id=None,
            )
        },
    )


def test_system_prompt_contains_required_instructions() -> None:
    prompt = build_system_prompt(_seed_tree())
    assert "Current feature tree state (JSON)" in prompt
    assert "Available operations and their schemas" in prompt
    assert "always name features descriptively" in prompt
    assert "verify shapes exist and are not suppressed before referencing them" in prompt
    assert "plan the full sequence before executing" in prompt


def test_mounting_bracket_prompt_generates_minimum_operations() -> None:
    service = OpenCadAgentService()
    request = ChatRequest(
        message="Create a mounting bracket with 4 standoffs, a central cutout, and counterbored mounting ears",
        tree_state=_seed_tree(),
        conversation_history=[],
        reasoning=False,
    )

    response = service.chat(request)

    assert len(response.operations_executed) >= 8
    assert all(op.status == "ok" for op in response.operations_executed)

    node_ids = set(response.new_tree_state.nodes.keys())
    for op in response.operations_executed:
        if op.tool == "boolean_cut":
            assert str(op.arguments["base_id"]) in node_ids
            assert str(op.arguments["tool_id"]) in node_ids
        if op.tool == "fillet_edges":
            assert str(op.arguments["shape_id"]) in node_ids


def test_reasoning_toggle_changes_response_style() -> None:
    service = OpenCadAgentService()
    low = service.chat(
        ChatRequest(
            message="Create a mounting bracket with 4 standoffs, a central cutout, and counterbored mounting ears",
            tree_state=_seed_tree(),
            conversation_history=[],
            reasoning=False,
        )
    )
    high = service.chat(
        ChatRequest(
            message="Create a mounting bracket with 4 standoffs, a central cutout, and counterbored mounting ears",
            tree_state=_seed_tree(),
            conversation_history=[],
            reasoning=True,
        )
    )

    assert low.response != high.response
    assert "Plan:" in high.response


def test_chat_api_round_trip() -> None:
    client = TestClient(app)
    payload = {
        "message": "Create a mounting bracket with 4 standoffs, a central cutout, and counterbored mounting ears",
        "tree_state": _seed_tree().model_dump(),
        "conversation_history": [],
        "reasoning": True,
    }

    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert len(body["operations_executed"]) >= 8
    assert body["new_tree_state"]["root_id"] == "root"


def test_healthz() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_planner_emits_line_entities_for_base_sketch() -> None:
    service = OpenCadAgentService()
    response = service.chat(
        ChatRequest(
            message="Create a mounting bracket with 4 standoffs, a central cutout, and counterbored mounting ears",
            tree_state=_seed_tree(),
            conversation_history=[],
            reasoning=False,
        )
    )

    add_sketch_ops = [op for op in response.operations_executed if op.tool == "add_sketch"]
    assert add_sketch_ops
    first = add_sketch_ops[0]
    entities = first.arguments["entities"]
    assert any(str(v.get("type", "")).lower() == "line" for v in entities.values())
    assert first.arguments.get("profile_order") == ["l1", "l2", "l3", "l4"]


def test_tool_runtime_supports_in_process_kernel_calls() -> None:
    kernel = OpenCadKernel(id_strategy="readable")
    registry = OperationRegistry(kernel)

    def kernel_call(operation: str, payload: dict[str, object]) -> dict[str, object]:
        result = registry.call(operation, payload)
        if isinstance(result, Success):
            return {"ok": True, "shape_id": result.shape_id}
        return {"ok": False, "message": result.message}

    runtime = ToolRuntime(_seed_tree(), kernel_call=kernel_call)
    sketch_id = runtime.add_sketch(
        name="Profile",
        entities={"p1": {"id": "p1", "type": "point", "x": 0.0, "y": 0.0}},
        constraints=[],
    )
    feature_id = runtime.extrude(sketch_id=sketch_id, depth=12.0, name="Base")

    tree = runtime.get_tree_state()
    shape_id = tree.nodes[feature_id].shape_id
    assert shape_id is not None
    assert not shape_id.startswith("shape-")
    assert shape_id.startswith("extrude-") or shape_id.startswith("box-")
