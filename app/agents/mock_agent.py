"""Deterministic mock agent runtime for safe CI evaluation and testing."""

import time
from typing import Any

from app.agents.models import (
    AgentExecutionTrace,
    AgentStepTrace,
    AgentToolCall,
    AgentToolResult,
)


class DeterministicMockAgent:
    """Safe, controlled mock agent runtime with explicit tool allowlists and step limits."""

    PERMITTED_TOOLS = {"calculator", "search_kb", "format_output"}

    def __init__(self, name: str = "MockAgent", max_steps: int = 5) -> None:
        self.name = name
        self.max_steps = max_steps

    def _execute_tool(self, tool_name: str, args: dict[str, Any]) -> AgentToolResult:
        """Execute a tool strictly from the safe allowlist."""
        if tool_name not in self.PERMITTED_TOOLS:
            return AgentToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Tool '{tool_name}' is not in the permitted allowlist {sorted(self.PERMITTED_TOOLS)}",
            )

        if tool_name == "calculator":
            a = float(args.get("a", 0))
            b = float(args.get("b", 0))
            op = str(args.get("op", "add"))
            if op == "add":
                val = a + b
            elif op == "multiply":
                val = a * b
            elif op == "subtract":
                val = a - b
            else:
                return AgentToolResult(
                    tool_name=tool_name, success=False, error=f"Unsupported op '{op}'"
                )
            return AgentToolResult(tool_name=tool_name, success=True, output=val)

        elif tool_name == "search_kb":
            query = str(args.get("query", "")).lower()
            kb = {
                "python": "Python was created by Guido van Rossum.",
                "evalforge20": "EvalForge20 is a local-first LLM evaluation platform.",
            }
            res = kb.get(query, f"No documents found for '{query}'")
            return AgentToolResult(tool_name=tool_name, success=True, output=res)

        elif tool_name == "format_output":
            text = str(args.get("text", ""))
            prefix = str(args.get("prefix", "Result: "))
            return AgentToolResult(tool_name=tool_name, success=True, output=f"{prefix}{text}")

        return AgentToolResult(tool_name=tool_name, success=False, error="Unknown execution path")

    def run_task(
        self,
        task_id: str,
        query: str,
        scripted_steps: list[dict[str, Any]] | None = None,
    ) -> AgentExecutionTrace:
        """Run the mock agent on a task, optionally following a scripted sequence or default behavior."""
        start_time = time.perf_counter()
        steps: list[AgentStepTrace] = []
        errors: list[str] = []

        # If scripted steps provided (for reproducible deterministic tests)
        if scripted_steps:
            for idx, step_spec in enumerate(scripted_steps):
                if idx >= self.max_steps:
                    errors.append(f"Exceeded max_steps limit of {self.max_steps}")
                    break

                t_name = step_spec.get("tool")
                t_args = step_spec.get("args", {})
                thought = step_spec.get("thought", f"Step {idx}: invoking {t_name}")

                if t_name:
                    tool_call = AgentToolCall(tool_name=t_name, arguments=t_args)
                    tool_res = self._execute_tool(t_name, t_args)
                    if not tool_res.success and tool_res.error:
                        errors.append(tool_res.error)

                    steps.append(
                        AgentStepTrace(
                            step_index=idx,
                            action_type="tool_call",
                            thought=thought,
                            tool_call=tool_call,
                            tool_result=tool_res,
                            duration_ms=5.0,
                        )
                    )
                else:
                    # Thought or final answer step
                    steps.append(
                        AgentStepTrace(
                            step_index=idx,
                            action_type=step_spec.get("action_type", "thought"),
                            thought=thought,
                            duration_ms=1.0,
                        )
                    )

            final_ans = scripted_steps[-1].get("final_answer") if scripted_steps else None
            completed = len(errors) == 0
        else:
            # Default auto behavior: search kb if query matches keyword, otherwise simple answer
            tool_call = AgentToolCall(
                tool_name="search_kb", arguments={"query": query.strip().lower()}
            )
            tool_res = self._execute_tool("search_kb", {"query": query.strip().lower()})
            steps.append(
                AgentStepTrace(
                    step_index=0,
                    action_type="tool_call",
                    thought=f"Looking up query in knowledge base: {query}",
                    tool_call=tool_call,
                    tool_result=tool_res,
                    duration_ms=10.0,
                )
            )
            final_ans = str(tool_res.output)
            completed = tool_res.success

        total_ms = (time.perf_counter() - start_time) * 1000.0

        return AgentExecutionTrace(
            agent_name=self.name,
            task_id=task_id,
            steps=steps,
            final_answer=final_ans,
            completed=completed,
            total_duration_ms=round(total_ms, 2),
            errors=errors,
        )
