from __future__ import annotations

from fastapi import FastAPI

from opencad.api_app import create_api_app
from opencad_agent.models import ChatRequest, ChatResponse
from opencad_agent.service import OpenCadAgentService

app: FastAPI = create_api_app(title="OpenCAD Agent", version="0.1.0")
_service = OpenCadAgentService()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return _service.chat(request)
