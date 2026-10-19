"""
Backend entry point proxy.
Allows starting the FastAPI application directly from the `backend/` directory:
    cd backend && uvicorn app.main:app --reload --port 8000
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
for p in (PROJECT_ROOT, BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from backend.app.main import app
except ImportError:
    from app.main import app  # type: ignore

__all__ = ["app"]
