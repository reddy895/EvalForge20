"""
Backend entry point proxy.
Allows starting the FastAPI application directly from the `backend/` directory:
    cd backend && uvicorn main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Add project root to sys.path so `app` can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402

__all__ = ["app"]
