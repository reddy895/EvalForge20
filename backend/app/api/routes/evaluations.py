"""Evaluation execution, listing, and detailed results inspection endpoints."""

from backend.app.core.errors import EvalForgeError
from backend.app.db.database import get_db
from backend.app.repositories.evaluation_repository import EvaluationRepository
from backend.app.schemas.evaluations import (
    EvaluationRunCreate,
    EvaluationRunDetail,
    EvaluationRunSummary,
)
from backend.app.services.benchmark_service import BenchmarkService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/v1/evaluations", tags=["Evaluations"])


@router.post("", response_model=EvaluationRunDetail, status_code=status.HTTP_201_CREATED)
async def create_and_run_evaluation(
    payload: EvaluationRunCreate,
    db: Session = Depends(get_db),
):
    """Execute reproducible evaluation run across benchmark cases."""
    service = BenchmarkService(db)
    try:
        return await service.run_evaluation(payload)
    except EvalForgeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from None


@router.get("", response_model=list[EvaluationRunSummary])
def list_evaluations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve history of completed and past evaluation runs."""
    repo = EvaluationRepository(db)
    return repo.list_runs(limit=limit, offset=offset)


@router.get("/{run_id}", response_model=EvaluationRunDetail)
def get_evaluation_detail(run_id: str, db: Session = Depends(get_db)):
    """Fetch complete execution details and case traces for a specific run."""
    repo = EvaluationRepository(db)
    detail = repo.get_run_detail(run_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run '{run_id}' not found.",
        )
    return detail
