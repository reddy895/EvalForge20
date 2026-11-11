"""Add composite indexes for evaluation history queries

Revision ID: 003_query_indexes
Revises: 002_providers_and_models
Create Date: 2026-11-11 15:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "003_query_indexes"
down_revision: str | None = "002_providers_and_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_evaluation_runs_status_created_at",
        "evaluation_runs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_evaluation_runs_dataset_created_at",
        "evaluation_runs",
        ["dataset_id", "created_at"],
    )
    op.create_index(
        "ix_evaluation_runs_model_created_at",
        "evaluation_runs",
        ["model_id", "created_at"],
    )
    op.create_index(
        "ix_case_results_evaluation_passed",
        "case_results",
        ["evaluation_id", "passed"],
    )


def downgrade() -> None:
    op.drop_index("ix_case_results_evaluation_passed", table_name="case_results")
    op.drop_index("ix_evaluation_runs_model_created_at", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_dataset_created_at", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_status_created_at", table_name="evaluation_runs")
