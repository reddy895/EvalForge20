# EvalForge20 Configuration Reference

## Environment Variables

All settings use the `EVALFORGE20_` prefix and can be provided via `.env` or system environment variables:

| Variable | Default | Description |
|---|---|---|
| `EVALFORGE20_ENV` | `development` | Environment mode (`development`, `testing`, `production`). |
| `EVALFORGE20_DEBUG` | `false` | Enable verbose debugging. |
| `EVALFORGE20_DATABASE_URL` | `sqlite:///./data/evalforge20.db` | SQLAlchemy database connection URI. |
| `EVALFORGE20_DATA_DIR` | `./data` | Directory where databases, datasets, and cache files reside. |
| `EVALFORGE20_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `EVALFORGE20_LOG_PROMPTS` | `false` | When false, raw prompts and model outputs are not logged to stdout. |
| `EVALFORGE20_MAX_CONCURRENCY` | `5` | Maximum concurrent test case evaluation tasks (1 to 50). |
| `EVALFORGE20_DEFAULT_TIMEOUT_SECONDS` | `60.0` | Default per-case execution timeout in seconds. |
| `EVALFORGE20_MAX_OUTPUT_BYTES` | `524288` | Maximum output size allowed before truncation (512 KB). |
| `EVALFORGE20_OLLAMA_BASE_URL` | `http://localhost:11434` | Base URL for the local Ollama instance. |
| `EVALFORGE20_OLLAMA_TIMEOUT_SECONDS` | `120.0` | HTTP timeout for Ollama inference requests. |

## LangSmith Environment Variables

Standard LangSmith variables are recognized directly:

| Variable | Default | Description |
|---|---|---|
| `LANGSMITH_TRACING` | `false` | Master toggle to enable LangSmith tracing. |
| `LANGSMITH_API_KEY` | `None` | LangSmith API key (`lsv2_pt_...`). |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | LangSmith API endpoint URL. |
| `LANGSMITH_PROJECT` | `evalforge20-default` | Default project for runs and traces. |
| `LANGSMITH_AUTO_SYNC_DATASETS` | `false` | Automatically mirror local datasets to LangSmith. |
