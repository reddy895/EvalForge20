"""Multi-model benchmark comparator running identical dataset snapshots."""

from src.evalforge.core.logging import get_logger
from src.evalforge.experiments.case_runner import CaseRunner
from src.evalforge.experiments.concurrency import BoundedConcurrencyPool
from src.evalforge.experiments.snapshot import DatasetSnapshot
from src.evalforge.providers.base import BaseProvider
from src.evalforge.schemas.evaluation import EvaluationConfig
from src.evalforge.storage.models.evaluation import CaseResult

logger = get_logger("evalforge.benchmarks.comparator")


class MultiModelComparator:
    """Executes identical frozen test cases across multiple models under strictly controlled conditions."""

    def __init__(self, provider: BaseProvider, config: EvaluationConfig):
        self.provider = provider
        self.config = config

    async def benchmark_model(
        self,
        model_id: str,
        snapshot: DatasetSnapshot,
        evaluation_id: str,
    ) -> list[CaseResult]:
        """Run all test cases in the snapshot against the specified model."""
        runner = CaseRunner(
            provider=self.provider,
            model_id=model_id,
            config=self.config,
        )
        pool = BoundedConcurrencyPool(max_concurrency=self.config.concurrency)

        logger.info(
            "Benchmarking model '%s' across %d snapshot cases",
            model_id,
            snapshot.total_cases,
        )

        results = await pool.map(
            lambda case: runner.execute_case(case, evaluation_id),
            snapshot.cases,
        )

        return results
