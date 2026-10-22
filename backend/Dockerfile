# EvalForge20 — Production Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and dependency specs
COPY pyproject.toml alembic.ini .env.example ./

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy backend source code and migrations
COPY src/ ./src/
COPY migrations/ ./migrations/

# Expose FastAPI port
EXPOSE 8000

# Default environment configuration
ENV HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start Uvicorn production server
CMD ["uvicorn", "src.evalforge.main:app", "--host", "0.0.0.0", "--port", "8000"]
