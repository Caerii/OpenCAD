from __future__ import annotations

from opencad_agent.models import ChatRequest, ChatResponse
from opencad_agent.planner import OpenCadPlanner
from opencad_agent.prompting import build_system_prompt
from opencad_agent.tools import KernelCall, ToolRuntime


class OpenCadAgentService:
    def __init__(
        self,
        planner: OpenCadPlanner | None = None,
        *,
        kernel_call: KernelCall | None = None,
        live_kernel: bool | None = None,
    ) -> None:
        self.planner = planner or OpenCadPlanner()
        self.kernel_call = kernel_call
        self.live_kernel = live_kernel

    def chat(self, request: ChatRequest) -> ChatResponse:
        _system_prompt = build_system_prompt(request.tree_state)
        runtime = ToolRuntime(
            request.tree_state,
            kernel_call=self.kernel_call,
            live_kernel=self.live_kernel,
        )

        response_text, operations = self.planner.execute(
            message=request.message,
            runtime=runtime,
            reasoning=request.reasoning,
        )

        return ChatResponse(
            response=response_text,
            operations_executed=operations,
            new_tree_state=runtime.get_tree_state(),
        )
