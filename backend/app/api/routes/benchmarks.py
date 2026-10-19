"""Benchmark dataset and task catalog endpoints."""

from backend.app.db.database import get_db
from backend.app.services.benchmark_service import BenchmarkService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/v1/benchmarks", tags=["Benchmarks"])


@router.get("")
def list_benchmarks(db: Session = Depends(get_db)):
    """List available evaluation benchmark tasks and case counts."""
    service = BenchmarkService(db)
    return service.list_available_tasks()


@router.get("/{task_id}")
def get_benchmark_detail(task_id: str, db: Session = Depends(get_db)):
    """Fetch benchmark details and test cases."""
    service = BenchmarkService(db)
    try:
        cases = service.load_task_cases(task_id)
        return {
            "task_id": task_id,
            "total_cases": len(cases),
            "cases": [c.model_dump() for c in cases],
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
