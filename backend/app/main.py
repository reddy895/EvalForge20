"""
Backend application entry point.
Exposes the FastAPI instance for direct startup:
    cd backend && uvicorn app.main:app --port 8000
Or from root:
    uvicorn backend.app.main:app --port 8000
"""

from app.main import app, create_app

__all__ = ["app", "create_app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
