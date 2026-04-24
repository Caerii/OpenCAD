from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter

load_dotenv()
router = APIRouter()

from opencad.api_app import create_api_app
from opencad.version import __version__
from opencad_agent.models import ChatRequest, ChatResponse
from opencad_agent.service import OpenCadAgentService

app: FastAPI = create_api_app(title="OpenCAD Agent", version=__version__)
_service = OpenCadAgentService()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return _service.chat(request)


app.include_router(router)
