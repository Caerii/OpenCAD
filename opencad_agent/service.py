from __future__ import annotations

from opencad_agent.llm import LiteLlmProvider
from opencad_agent.models import ChatRequest, ChatResponse
from opencad_agent.planner import OpenCadPlanner
from opencad_agent.prompting import build_code_generation_prompt, build_system_prompt
from opencad_agent.tools import KernelCall, ToolRuntime


class OpenCadAgentService:
    def __init__(
        self,
        planner: OpenCadPlanner | None = None,
        *,
        kernel_call: KernelCall | None = None,
        live_kernel: bool | None = None,
        llm_client: LiteLlmProvider | None = None,
    ) -> None:
        self.planner = planner or OpenCadPlanner()
        self.kernel_call = kernel_call
        self.live_kernel = live_kernel
        self.llm_client = llm_client or LiteLlmProvider()

    def chat(self, request: ChatRequest) -> ChatResponse:
        _system_prompt = build_system_prompt(request.tree_state)
        runtime = ToolRuntime(
            request.tree_state,
            kernel_call=self.kernel_call,
            live_kernel=self.live_kernel,
        )

        if request.generate_code:
            generated_code = self._generate_code(request)
            return ChatResponse(
                response=generated_code,
                generated_code=generated_code,
                operations_executed=[],
                new_tree_state=runtime.get_tree_state(),
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

    def _generate_code(self, request: ChatRequest) -> str:
        use_llm = request.llm_model is not None
        if use_llm:
            return self.llm_client.generate_code(
                provider=request.llm_provider,
                model=request.llm_model,
                system_prompt=build_code_generation_prompt(request.tree_state),
                user_message=request.message,
                conversation_history=request.conversation_history,
                reasoning=request.reasoning,
            )
        return self.planner.generate_code(request.message)
