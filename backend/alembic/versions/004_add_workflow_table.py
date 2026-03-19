"""add workflow table

Revision ID: 004
Revises: 003
Create Date: 2026-03-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | Sequence[str] | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workflow",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(2000), nullable=False, server_default=""),
        sa.Column("nodes", sa.JSON(), nullable=True),
        sa.Column("edges", sa.JSON(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "created_by", sa.String(100), nullable=False, server_default="user"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index("idx_workflow_name", "workflow", ["name"])
    op.create_index("idx_workflow_is_active", "workflow", ["is_active"])
    op.create_index("idx_workflow_created_by", "workflow", ["created_by"])


def downgrade() -> None:
    op.drop_index("idx_workflow_created_by", table_name="workflow")
    op.drop_index("idx_workflow_is_active", table_name="workflow")
    op.drop_index("idx_workflow_name", table_name="workflow")
    op.drop_table("workflow")
