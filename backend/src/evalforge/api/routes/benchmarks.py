"""Modular API route for benchmark suites and comparative matrices."""

from typing import Any

from fastapi import APIRouter

from src.evalforge.datasets.registry import get_benchmark_registry

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.get("")
async def list_benchmarks() -> dict[str, Any]:
    registry = get_benchmark_registry()
    suites = registry.list_suites()
    return {
        "total": len(suites),
        "benchmarks": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "description": s.description,
                "source": s.source,
                "license": s.license,
                "version": s.version,
                "default_evaluators": s.default_evaluators,
                "cases_count": len(s.cases),
            }
            for s in suites
        ],
    }


@router.get("/{suite_id}")
async def get_benchmark_suite(suite_id: str) -> dict[str, Any]:
    from fastapi import HTTPException
    registry = get_benchmark_registry()
    suite = registry.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail=f"Benchmark suite '{suite_id}' not found.")
    return {
        "id": suite.id,
        "name": suite.name,
        "category": suite.category,
        "description": suite.description,
        "source": suite.source,
        "license": suite.license,
        "version": suite.version,
        "default_evaluators": suite.default_evaluators,
        "cases": suite.cases,
    }
