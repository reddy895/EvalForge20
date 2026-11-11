"""Modular API routes for experiment tracking, multi-model comparison, and exports."""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from src.evalforge.experiments.repository import ExperimentRepository
from src.evalforge.experiments.service import ExperimentService
from src.evalforge.schemas.main import ExperimentCompareRequest

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
async def list_experiments(
    limit: int = 50, offset: int = 0, model_identifier: str | None = None
) -> dict[str, Any]:
    items = await ExperimentService.list_experiments(
        limit=limit, offset=offset, model_identifier=model_identifier
    )
    return {"total": len(items), "experiments": items}


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str) -> dict[str, Any]:
    exp = await ExperimentService.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
    return exp


@router.delete("/{experiment_id}")
async def delete_experiment(experiment_id: str) -> dict[str, Any]:
    ok = await ExperimentService.delete_experiment(experiment_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
    return {"success": True, "deleted_id": experiment_id}


@router.post("/compare")
async def compare_experiments(payload: ExperimentCompareRequest) -> dict[str, Any]:
    return await ExperimentService.compare_experiments(payload.experiment_ids)


@router.get("/{experiment_id}/export")
async def export_experiment(experiment_id: str, format: str = "json") -> Any:
    if format.lower() == "csv":
        csv_data = await ExperimentRepository.export_csv(experiment_id)
        if not csv_data:
            raise HTTPException(status_code=404, detail="Experiment not found.")
        return PlainTextResponse(content=csv_data, media_type="text/csv")

    data = await ExperimentRepository.export_json(experiment_id)
    if not data:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    return data
