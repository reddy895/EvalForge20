.PHONY: help install test test-backend test-frontend build lint lint-backend lint-frontend dev-backend dev-frontend run clean

help:
	@echo "EvalForge20 - Local-first LLM Intelligence & Evaluation Platform"
	@echo ""
	@echo "Targets:"
	@echo "  make install         Install backend Python and frontend Node dependencies"
	@echo "  make test            Run all backend and frontend automated tests"
	@echo "  make test-backend    Run pytest test suite"
	@echo "  make test-frontend   Run vitest test suite"
	@echo "  make lint            Run ruff checks on backend and oxlint on frontend"
	@echo "  make build           Compile frontend production bundle"
	@echo "  make dev-backend     Start FastAPI backend with uvicorn on :8000"
	@echo "  make dev-frontend    Start Vite frontend on :5173"
	@echo "  make clean           Remove caches, build artifacts, and databases"

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

test: test-backend test-frontend

test-backend:
	pytest tests/ backend/app/tests/ -v

test-frontend:
	cd frontend && npm test

build:
	cd frontend && npm run build

lint: lint-backend lint-frontend

lint-backend:
	python3 -m py_compile backend/app/main.py tests/test_end_to_end_flow.py

lint-frontend:
	cd frontend && npm run lint

dev-backend:
	python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

clean:
	rm -rf frontend/dist .pytest_cache backend/**/__pycache__ tests/**/__pycache__ evalforge20.db
