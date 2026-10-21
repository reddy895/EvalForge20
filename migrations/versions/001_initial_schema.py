"""Initial schema for datasets, test cases, evaluations, benchmarks, and agent traces

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-21 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_datasets_name", "datasets", ["name"])

    op.create_table(
        "test_cases",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("dataset_id", sa.String(length=36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("evaluator_config_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_test_cases_dataset_id", "test_cases", ["dataset_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="ollama"),
        sa.Column("dataset_id", sa.String(length=36), sa.ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dataset_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pass_rate", sa.Float(), nullable=True),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("summary_metrics_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_evaluation_runs_status", "evaluation_runs", ["status"])
    op.create_index("ix_evaluation_runs_model_id", "evaluation_runs", ["model_id"])

    op.create_table(
        "case_results",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("evaluation_id", sa.String(length=36), sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=True),
        sa.Column("actual_output", sa.Text(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("token_usage_json", sa.Text(), nullable=True),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_case_results_evaluation_id", "case_results", ["evaluation_id"])

    op.create_table(
        "benchmark_comparisons",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_name", sa.String(length=255), nullable=True),
        sa.Column("model_ids_json", sa.Text(), nullable=False),
        sa.Column("evaluation_ids_json", sa.Text(), nullable=False),
        sa.Column("summary_matrix_json", sa.Text(), nullable=True),
        sa.Column("reproducibility_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "agent_evaluations",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="ollama"),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_steps", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("task_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tool_accuracy", sa.Float(), nullable=True),
        sa.Column("schema_validity", sa.Float(), nullable=True),
        sa.Column("policy_violations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("final_output", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "agent_traces",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("evaluation_id", sa.String(length=36), sa.ForeignKey("agent_evaluations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=True),
        sa.Column("tool_args_json", sa.Text(), nullable=True),
        sa.Column("tool_result_json", sa.Text(), nullable=True),
        sa.Column("thought", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_valid_call", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_traces_eval_step", "agent_traces", ["evaluation_id", "step_number"])


def downgrade() -> None:
    op.drop_table("agent_traces")
    op.drop_table("agent_evaluations")
    op.drop_table("benchmark_comparisons")
    op.drop_table("case_results")
    op.drop_table("evaluation_runs")
    op.drop_table("test_cases")
    op.drop_table("datasets")
