"""Agent execution loop with step bounds, timeouts, and trace recording."""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from src.evalforge.agents.tool_harness import SafeToolHarness
from src.evalforge.core.logging import get_logger
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import (
    ChatMessage,
    InferenceRequest,
    ToolDefinition,
)
from src.evalforge.schemas.agent import AgentStepTrace, AgentToolSpec

logger = get_logger("evalforge.agents.runner")


class AgentExecutionRunner:
    """Orchestrates an agent loop: prompt -> model -> tool call -> tool result -> final outcome."""

    def __init__(self, provider: BaseProvider, harness: Optional[SafeToolHarness] = None):
        self.provider = provider
        self.harness = harness or SafeToolHarness()

    async def execute_agent_loop(
        self,
        model_id: str,
        task: str,
        tool_specs: List[AgentToolSpec],
        max_steps: int = 8,
        timeout_seconds: float = 30.0,
    ) -> Tuple[List[AgentStepTrace], Optional[str], bool, int]:
        """Execute the multi-turn agent interaction loop with step limits and timeout enforcement."""
        start_time = time.perf_counter()

        # Convert tool specs to provider definitions
        provider_tools = [
            ToolDefinition(
                name=t.name,
                description=t.description,
                parameters=t.parameters,
            )
            for t in tool_specs
        ]
        allowed_tool_names: Set[str] = {t.name.lower() for t in tool_specs}

        messages: List[ChatMessage] = [ChatMessage(role="user", content=task)]
        traces: List[AgentStepTrace] = []
        final_output: Optional[str] = None
        task_completed = False
        policy_violations_count = 0

        async def _run_loop() -> None:
            nonlocal final_output, task_completed, policy_violations_count

            for step in range(1, max_steps + 1):
                step_start = time.perf_counter()

                # Inference request
                req = InferenceRequest(
                    model=model_id,
                    messages=messages,
                    tools=provider_tools,
                    temperature=0.1,
                )

                resp = await self.provider.generate(req)
                step_duration = (time.perf_counter() - step_start) * 1000

                if resp.tool_calls:
                    for tc in resp.tool_calls:
                        # Safe tool execution
                        exec_res = self.harness.execute(
                            tool_name=tc.name,
                            args=tc.arguments,
                            allowed_tools=allowed_tool_names,
                        )

                        if exec_res.policy_violation:
                            policy_violations_count += 1

                        trace = AgentStepTrace(
                            step_number=len(traces) + 1,
                            tool_name=tc.name,
                            tool_args=tc.arguments,
                            tool_result=exec_res.output if exec_res.success else {"error": exec_res.error},
                            thought=resp.text or None,
                            duration_ms=round(step_duration + exec_res.duration_ms, 2),
                            is_valid_call=exec_res.success,
                        )
                        traces.append(trace)

                        # Append to conversation history
                        messages.append(
                            ChatMessage(
                                role="assistant",
                                content=f"Called tool {tc.name} with args {json.dumps(tc.arguments)}",
                            )
                        )
                        messages.append(
                            ChatMessage(
                                role="tool",
                                content=json.dumps(exec_res.output if exec_res.success else {"error": exec_res.error}),
                            )
                        )
                else:
                    # Model provided text answer without requesting more tools
                    final_output = resp.text
                    task_completed = True
                    trace = AgentStepTrace(
                        step_number=len(traces) + 1,
                        tool_name=None,
                        tool_args={},
                        tool_result=None,
                        thought=resp.text,
                        duration_ms=round(step_duration, 2),
                        is_valid_call=True,
                    )
                    traces.append(trace)
                    break

        try:
            await asyncio.wait_for(_run_loop(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning("Agent execution exceeded timeout of %s seconds", timeout_seconds)
            final_output = f"Execution timed out after {timeout_seconds}s"
            task_completed = False

        return traces, final_output, task_completed, policy_violations_count
