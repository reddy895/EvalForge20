# EvalForge20 AI Agent Evaluation

## 1. Overview

EvalForge20 evaluates AI agents as multi-step decision and tool execution systems rather than simple single-turn text generators.

## 2. Agent Execution Traces

Agents generate an `AgentExecutionTrace` comprising:
- Ordered execution steps (`AgentStepTrace`)
- Tool invocation specs (`AgentToolCall`)
- Tool outputs and error status (`AgentToolResult`)
- Step-by-step reasoning or thought logs
- Final response and completion status

## 3. Metrics

1. **`agent_task_completion`**:
   Verifies whether the agent reached completion without unhandled exceptions and whether the final answer satisfies expected output references.

2. **`tool_selection_accuracy`**:
   Evaluates whether the tools invoked match the expected trajectory order (`strict_order=True`) or set overlap (`strict_order=False`).

3. **`tool_argument_validity`**:
   Validates that tool calls contained all required arguments according to defined argument schemas.

4. **`step_efficiency`**:
   Compares the actual step count against optimal and maximum permitted steps.

## 4. Deterministic Mock Agent

For CI pipelines and zero-cost offline testing, EvalForge20 includes `DeterministicMockAgent`:
- Explicit tool allowlist: `{"calculator", "search_kb", "format_output"}`.
- Hard rejection for unpermitted tools (e.g. arbitrary code or shell commands).
- Strict maximum step bounds preventing runaway loops.
