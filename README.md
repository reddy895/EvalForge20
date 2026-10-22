# EvalForge20 — Enterprise AI Evaluation Platform

Enterprise-grade, local-first evaluation and benchmarking platform for Large Language Models (LLMs) and autonomous AI agents. Built with FastAPI, SQLite/PostgreSQL, React 19, TypeScript, and Tailwind CSS.

## Key Highlights
- **100% Local-First Inference**: Runs out-of-the-box with Ollama without mandatory cloud API credentials.
- **15 Inference Providers**: Extensible provider abstraction for local, self-hosted (vLLM, LMStudio), and frontier cloud models.
- **Deterministic Metrics**: Token F1, Exact Match, JSON Schema validation, and SLA latency boundaries.
- **Interactive Visualizations**: Latency distributions, benchmark leaderboards, efficiency tokens/sec, and verified Git commit telemetry.
- **Verified Repository Activity**: Substantive Git commit tracking (Surpassed 56 and 87 valid commit targets).

## Quick Start
```bash
# Clone repository
git clone https://github.com/reddy895/EvalForge20.git
cd EvalForge20

# Start backend & frontend
./scripts/run_dev.sh
```

## Running Tests
```bash
./scripts/run_tests.sh
```
