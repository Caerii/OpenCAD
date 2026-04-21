from fastapi import FastAPI
from opencad_kernel import api as kernel_api
from opencad_agent import api as agent_api
from opencad_solver import api as solver_api
from opencad_tree import api as tree_api

app = FastAPI(title="OpenCAD API")

# Mount each sub-module with a clear namespace
app.include_router(kernel_api.router, prefix="/kernel", tags=["Kernel"])
app.include_router(agent_api.router, prefix="/agent", tags=["AI Agent"])
app.include_router(solver_api.router, prefix="/solver", tags=["Constraint Solver"])
app.include_router(tree_api.router, prefix="/tree", tags=["Feature Tree"])

@app.get("/")
async def health_check():
    return {"status": "online", "engine": "OpenCAD"}