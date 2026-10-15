"""Initial EvalForge20 schema.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-15 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. datasets
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=100), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latest_version", sa.Integer(), server_default="1"),
    )

    # 2. dataset_versions
    op.create_table(
        "dataset_versions",
        sa.Column("version_id", sa.String(length=100), primary_key=True),
        sa.Column("dataset_id", sa.String(length=100), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("cases_json", sa.Text(), nullable=False),
        sa.Column("stats_json", sa.Text(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_dataset_versions_dataset_id", "dataset_versions", ["dataset_id"])
    op.create_index("idx_dataset_versions_hash", "dataset_versions", ["content_hash"])

    # 3. evaluation_runs
    op.create_table(
        "evaluation_runs",
        sa.Column("run_id", sa.String(length=100), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("target_config_json", sa.Text(), nullable=False),
        sa.Column("evaluator_configs_json", sa.Text(), nullable=False),
        sa.Column("dataset_version_hash", sa.String(length=64), nullable=True),
        sa.Column("total_cases", sa.Integer(), server_default="0"),
        sa.Column("completed_cases", sa.Integer(), server_default="0"),
        sa.Column("failed_cases", sa.Integer(), server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aggregate_metrics_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("idx_runs_status", "evaluation_runs", ["status"])
    op.create_index("idx_runs_started_at", "evaluation_runs", ["started_at"])

    # 4. case_results
    op.create_table(
        "case_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.String(length=100), nullable=False),
        sa.Column("run_id", sa.String(length=100), sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("actual_output_json", sa.Text(), nullable=True),
        sa.Column("expected_output_json", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("token_usage_json", sa.Text(), nullable=True),
        sa.Column("error_category", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("trace_json", sa.Text(), nullable=True),
    )
    op.create_index("idx_case_results_run_id", "case_results", ["run_id"])
    op.create_index("idx_case_results_case_id", "case_results", ["case_id"])

    # 5. metric_results
    op.create_table(
        "metric_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_result_id", sa.Integer(), sa.ForeignKey("case_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("metric_id", sa.String(length=100), nullable=False),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), server_default="{}"),
        sa.Column("is_model_based", sa.Boolean(), server_default=sa.text("0")),
    )
    op.create_index("idx_metric_results_case_id", "metric_results", ["case_result_id"])
    op.create_index("idx_metric_results_run_id", "metric_results", ["run_id"])
    op.create_index("idx_metric_results_metric_id", "metric_results", ["metric_id"])

    # 6. run_comparisons
    op.create_table(
        "run_comparisons",
        sa.Column("comparison_id", sa.String(length=100), primary_key=True),
        sa.Column("baseline_run_id", sa.String(length=100), nullable=False),
        sa.Column("candidate_run_id", sa.String(length=100), nullable=False),
        sa.Column("delta_metrics_json", sa.Text(), nullable=False),
        sa.Column("regressions_json", sa.Text(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("run_comparisons")
    op.drop_table("metric_results")
    op.drop_table("case_results")
    op.drop_table("evaluation_runs")
    op.drop_table("dataset_versions")
    op.drop_table("datasets")
