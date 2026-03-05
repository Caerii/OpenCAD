from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from opencad_tree.models import FeatureTree


class ChatHistoryItem(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    tree_state: FeatureTree
    conversation_history: list[ChatHistoryItem] = Field(default_factory=list)
    reasoning: bool = False


class OperationExecution(BaseModel):
    tool: str
    status: Literal["ok", "error"] = "ok"
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    response: str
    operations_executed: list[OperationExecution] = Field(default_factory=list)
    new_tree_state: FeatureTree
