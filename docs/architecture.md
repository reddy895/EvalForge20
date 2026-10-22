# EvalForge20 Architecture Documentation

## System Architecture

EvalForge20 is structured with strict separation of concerns:

- **Frontend (`frontend/`)**: React 19 + TypeScript + Vite SPA. Provides responsive dark-mode analytics, model exploration, and evaluation workspaces.
- **Backend (`backend/`)**: FastAPI 0.115 asynchronous application. Exposes dual `/api` and `/api/v1` routes with Pydantic validation.
- **Inference Layer (`backend/src/evalforge/providers/`)**: Extensible adapter registry supporting 15 providers with local Ollama as the default.
- **Database Layer (`backend/src/evalforge/storage/`)**: SQLAlchemy 2.0 with async SQLite/PostgreSQL managed via Alembic migrations.
