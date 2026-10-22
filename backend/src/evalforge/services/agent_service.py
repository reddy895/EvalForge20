"""Agent evaluation application service managing agent runs and step auditing."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.evalforge.agents.agent_metrics import compute_agent_metrics
from src.evalforge.agents.agent_runner import AgentExecutionRunner
from src.evalforge.core.errors import NotFoundError
from src.evalforge.core.logging import get_logger
from src.evalforge.providers.registry import get_provider_registry
from src.evalforge.schemas.agent import AgentEvaluationCreateRequest
from src.evalforge.storage.models.agent import AgentEvaluation, AgentTrace
from src.evalforge.storage.repositories.agent_repo import AgentRepository

logger = get_logger("evalforge.services.agent")


class AgentService:
    """Orchestrates controlled agent evaluations and persists full trace evidence."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AgentRepository(session)
        self.registry = get_provider_registry()

    async def run_evaluation(self, request: AgentEvaluationCreateRequest) -> AgentEvaluation:
        """Execute a controlled agent test case with strict allowlist and full step auditing."""
        provider = self.registry.get(request.provider)

        eval_name = request.name or f"Agent Eval — {request.model_id}: {request.task[:40]}"

        # Create evaluation entity
        evaluation = AgentEvaluation(
            name=eval_name,
            model_id=request.model_id,
            provider=request.provider,
            task=request.task,
            status="running",
            max_steps=request.max_steps,
        )
        await self.repo.add(evaluation)

        # Run agent loop
        runner = AgentExecutionRunner(provider=provider)
        try:
            traces, final_output, raw_completed, violations = await runner.execute_agent_loop(
                model_id=request.model_id,
                task=request.task,
                tool_specs=request.tools,
                max_steps=request.max_steps,
                timeout_seconds=request.timeout_seconds,
            )

            # Compute quantitative scorecard
            scorecard = compute_agent_metrics(
                traces=traces,
                expected_tools=request.expected_tools,
                expected_outcome=request.expected_outcome,
                final_output=final_output,
                policy_violations=violations,
                raw_task_completed=raw_completed,
            )

            # Persist trace records
            orm_traces = [
                AgentTrace(
                    evaluation_id=evaluation.id,
                    step_number=t.step_number,
                    tool_name=t.tool_name,
                    tool_args_json=str(t.tool_args) if t.tool_args else None,
                    tool_result_json=str(t.tool_result) if t.tool_result else None,
                    thought=t.thought,
                    duration_ms=t.duration_ms,
                    is_valid_call=t.is_valid_call,
                )
                for t in traces
            ]
            await self.repo.add_traces(evaluation.id, orm_traces)

            # Update evaluation record
            evaluation.status = "completed"
            evaluation.total_steps = scorecard.total_steps
            evaluation.task_completed = scorecard.task_completed
            evaluation.tool_accuracy = scorecard.tool_accuracy
            evaluation.schema_validity = scorecard.schema_validity
            evaluation.policy_violations = scorecard.policy_violations
            evaluation.final_output = final_output

            await self.repo.flush()

        except Exception as exc:
            logger.exception("Agent evaluation '%s' crashed: %s", evaluation.id, exc)
            evaluation.status = "failed"
            evaluation.error_message = str(exc)
            await self.repo.flush()

        return evaluation

    async def get_evaluation(self, evaluation_id: str) -> AgentEvaluation:
        """Fetch agent evaluation by ID."""
        return await self.repo.get_or_fail(evaluation_id, "AgentEvaluation")

    async def get_evaluation_with_traces(self, evaluation_id: str) -> AgentEvaluation:
        """Fetch agent evaluation eager-loading all step traces."""
        entity = await self.repo.get_with_traces(evaluation_id)
        if not entity:
            raise NotFoundError("AgentEvaluation", evaluation_id)
        return entity

    async def get_traces(self, evaluation_id: str) -> list[AgentTrace]:
        """Fetch ordered step traces for an agent evaluation."""
        return await self.repo.list_traces(evaluation_id)

    async def list_evaluations(self, offset: int = 0, limit: int = 50) -> list[AgentEvaluation]:
        """List historical agent evaluations with pagination."""
        return await self.repo.list(offset=offset, limit=limit)
