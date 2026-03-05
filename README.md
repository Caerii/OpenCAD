# OpenCAD

OpenCAD is an open-source, modular CAD. It combines a geometry kernel, constraint solver, parametric feature tree, 3D viewport, and an AI assistant — each running as an independent service that can be developed and deployed separately.

## What It Does

| # | Service | What it handles |
|---|---------|-----------------|
| 1 | **Geometry Kernel** (`opencad_kernel`) | Primitive creation (box, cylinder, …), booleans, fillets, and other shape operations via a typed registry |
| 2 | **Constraint Solver** (`opencad_solver`) | 2D sketch constraints (coincident, distance, angle, …) with pluggable solver backend (Python/NumPy fallback, SolveSpace primary), full constraint-graph introspection (DOF, Jacobian, variable/constraint mapping), and solve/check/diagnose feedback |
| 3 | **Feature Tree** (`opencad_tree`) | Directed acyclic graph of modeling features — CRUD, dependency tracking, stale propagation, rebuild, and assembly-mate-aware invalidation |
| 4 | **3D Viewport** (`opencad_viewport`) | React + Three.js UI — mesh viewer, feature tree panel, sketch editor, and chat panel |
| 5 | **AI Chat Agent** (`opencad_agent`) | Natural-language modeling assistant that plans and executes multi-step operation sequences |

## Repository Layout

```text
opencad_kernel/      # 1 – Geometry Kernel
opencad_solver/      # 2 – Constraint Solver
opencad_tree/        # 3 – Feature Tree
opencad_viewport/    # 4 – 3D Viewport (frontend)
opencad_agent/       # 5 – AI Chat Agent
scripts/             # Backend smoke tests
```

## Quickstart

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[full]"
cp .env.example .env
```

### 2. Start backend services

Each service runs on its own port:

```bash
python -m uvicorn opencad_kernel.api:app --reload --port 8000   # 1 – Kernel
python -m uvicorn opencad_solver.api:app --reload --port 8001   # 2 – Solver
python -m uvicorn opencad_tree.api:app   --reload --port 8002   # 3 – Tree
python -m uvicorn opencad_agent.api:app  --reload --port 8003   # 5 – Agent
```

### 3. Check health

```bash
curl -s http://127.0.0.1:8000/healthz   # → {"status":"ok"}
curl -s http://127.0.0.1:8001/healthz
curl -s http://127.0.0.1:8002/healthz
curl -s http://127.0.0.1:8003/healthz
```

### 4. Start the frontend

```bash
cd opencad_viewport
npm install --legacy-peer-deps
npm run dev                              # → http://localhost:5173
```

The viewport runs in **mock mode** by default (no backend required).
Set `VITE_USE_MOCK=false` to connect to the live services above.

## Environment Configuration

Runtime defaults are documented in `.env.example`.

- `OPENCAD_ENABLE_DOCS=true|false` toggles OpenAPI/docs route exposure.
- `OPENCAD_CORS_ALLOW_ORIGINS` sets a comma-separated browser origin allowlist.
- `OPENCAD_KERNEL_BACKEND=analytic|occt` selects the kernel backend.
- `OPENCAD_SOLVER_BACKEND=auto|solvespace|python` selects the solver backend.

For production, disable docs and set a strict CORS origin list.

## Security

Use TLS + authentication at your reverse proxy/API gateway.
Do not commit `.env` files, tokens, or private datasets.
See `SECURITY.md` for coordinated vulnerability reporting.

## Testing

```bash
pytest
```

## Headless Scripting (Single Process)

OpenCAD now includes a first-class in-process API for scripting workflows with automatic feature-tree logging.

```python
from opencad import Part, Sketch

part = Part()
sketch = Sketch().rect(10, 20).circle(3, subtract=True)
part.extrude(sketch, depth=5).fillet(edges="top", radius=0.5)
part.export("output.step")
```

Every fluent call appends a built `FeatureNode` to the in-memory DAG, so headless runs are recoverable.
Fluent sketches also persist `entities` + `profile_order` metadata in the sketch node, matching agent-path ordering semantics for deterministic profile reconstruction.

## CLI

```bash
opencad build model.json --output model.built.json
opencad run model.py --export output.step --tree-output output-tree.json
```

## Roadmap

### Phase 1 (current)

- **Pluggable solver backend** — SolveSpace primary (`pip install python-solvespace`), Python/NumPy fallback.
  Set `OPENCAD_SOLVER_BACKEND=solvespace|python|auto`.
- **Constraint-graph introspection** — `POST /sketch/diagnose` returns DOF, Jacobian sparse structure, variable ↔ constraint mapping, and over/under-determined classification.
- **3-D assembly mates** — `create_assembly_mate`, `delete_assembly_mate`, `list_assembly_mates` operations in the kernel. Supported types: coincident, concentric, distance, angle, parallel, perpendicular.
- **Tree integration** — mate-aware feature nodes that go stale when constrained shapes rebuild.

### Phase 2 (planned)

- **Part-level 3-D constraints** — constrain specific faces/edges that survive parametric rebuilds. Requires a topology reference stability strategy. See [TOPOLOGY.md](TOPOLOGY.md).
- **Topology reference stability** is an open research question. We are evaluating persistent face IDs (TNaming), hash-based tracking (Build123d), parametric graph position (Fusion 360), and occurrence paths (STEP). Community proposals welcome — see [TOPOLOGY.md](TOPOLOGY.md) for the problem statement, prior-art analysis, and proposal template.
- **Agent and viewport integration** — propagate solver diagnostics and assembly mate state to the AI agent and 3D viewport.

> **Note:** Part-level 3-D constraints require a topology reference strategy.
> We are evaluating persistent face IDs vs. hash-based tracking.
> See [TOPOLOGY.md](TOPOLOGY.md). This is an open contribution opportunity —
> a working proposal with implementation sketch will unblock Phase 2.

## Additional Documentation

- [PRODUCTION.md](PRODUCTION.md) — deployment, routes, and verification
- [ARCHITECTURE.md](ARCHITECTURE.md) — component design and API contracts
- [TOPOLOGY.md](TOPOLOGY.md) — topology reference stability (open research question)
- [SECURITY.md](SECURITY.md) — vulnerability reporting and hardening baseline
