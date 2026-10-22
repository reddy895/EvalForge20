# Sandboxed AI Agent Evaluation

EvalForge20 includes a sandboxed execution harness for multi-step autonomous agents:
- **Tool Selection Accuracy**: Measures whether the agent chose the appropriate tool.
- **Schema Validation**: Validates arguments passed to tool definitions.
- **Step Count & Timeout**: Limits recursion depth and prevents runaway loops.
- **Trace Auditing**: Full step-by-step trace capture with latency tracking.
