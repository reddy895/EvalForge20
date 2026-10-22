"""Create providers and registered_models tables for persistent catalog

Revision ID: 002_providers_and_models
Revises: 001_initial_schema
Create Date: 2026-10-22 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_providers_and_models"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "providers",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("provider_type", sa.String(length=32), nullable=False, server_default="cloud"),
        sa.Column("implementation_status", sa.String(length=64), nullable=False, server_default="configurable_cloud"),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("is_configured", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_healthy", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("setup_instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_providers_name", "providers", ["name"], unique=True)

    op.create_table(
        "registered_models",
        sa.Column("id", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider_id", sa.String(length=64), nullable=False),
        sa.Column("model_identifier", sa.String(length=255), nullable=False),
        sa.Column("family", sa.String(length=64), nullable=True),
        sa.Column("parameter_count", sa.String(length=32), nullable=True),
        sa.Column("context_window", sa.Integer(), nullable=False, server_default="4096"),
        sa.Column("is_local", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_installed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("supports_tools", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("supports_structured_output", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("license", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_registered_models_name", "registered_models", ["name"])
    op.create_index("ix_registered_models_provider_id", "registered_models", ["provider_id"])


def downgrade() -> None:
    op.drop_table("registered_models")
    op.drop_table("providers")
