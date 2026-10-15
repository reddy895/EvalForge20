# EvalForge20 LangSmith Integration

## 1. Overview & Guiding Principles

LangSmith in EvalForge20 is a **first-class optional integration**:
- **Offline First**: All local benchmarks, runner executions, SQLite persistence, and CLI commands function 100% offline without LangSmith credentials.
- **Explicit Synchronization**: Local datasets and evaluation runs are never uploaded without explicit configuration or CLI/API commands.
- **Fail-Safe**: If LangSmith is unreachable, misconfigured, or experiences network errors, local evaluation continues uninterrupted.

## 2. Configuration

Set standard LangSmith environment variables:

```bash
# Enable LangSmith tracing
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="lsv2_pt_..."
export LANGSMITH_PROJECT="my-evalforge20-project"
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
```

## 3. CLI Commands

Check connectivity and diagnostics:
```bash
evalforge20 langsmith status
```

Synchronize a local dataset to LangSmith:
```bash
evalforge20 langsmith sync-dataset --path examples/datasets/basic.jsonl --name "benchmark-dataset-v1"
```

Sync an evaluation run to a LangSmith experiment:
```bash
evalforge20 langsmith sync-run <run-id>
```

## 4. REST API Endpoints

- `GET /v1/integrations/langsmith/status`: Diagnostic health check returning SDK availability, configured project, and network connectivity.
- `POST /v1/integrations/langsmith/sync-dataset`: Registers a dataset in LangSmith.
- `POST /v1/integrations/langsmith/sync-run`: Logs a completed local evaluation run as a LangSmith experiment.
