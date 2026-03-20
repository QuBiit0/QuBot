"""Add pgvector extension and embedding columns to memory tables

Revision ID: 005
Revises: 004
Create Date: 2026-03-20 00:00:00.000000

Changes:
- Installs pgvector PostgreSQL extension (CREATE EXTENSION IF NOT EXISTS vector)
- Adds `embedding_vector` column (vector(1536)) to agent_memory
- Adds `embedding_vector` column (vector(1536)) to global_memory
- Creates IVFFlat approximate nearest-neighbor indexes
- Adds `content_hash` column to agent_memory for deduplication (Phase 5)

Fallback: If pgvector extension is unavailable the migration skips the
vector-typed columns and indexes gracefully — the application falls back to
the existing JSONB embedding path.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "005"
down_revision: str | Sequence[str] | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Dimensions for text-embedding-3-small
EMBEDDING_DIM = 1536


def _pgvector_available(conn) -> bool:
    """Check whether the pgvector extension can be created."""
    try:
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        return True
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()
    has_vector = _pgvector_available(conn)

    # ── agent_memory ─────────────────────────────────────────────────────────

    # embedding column (JSONB) — keeps backward compat with memory_tool.py
    # Only add if it doesn't already exist
    existing = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='agent_memory' AND column_name='embedding'"
        )
    ).fetchone()
    if not existing:
        op.add_column(
            "agent_memory",
            sa.Column("embedding", sa.JSON(), nullable=True),
        )

    # content_hash for deduplication (Phase 5)
    existing_hash = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='agent_memory' AND column_name='content_hash'"
        )
    ).fetchone()
    if not existing_hash:
        op.add_column(
            "agent_memory",
            sa.Column("content_hash", sa.String(64), nullable=True),
        )
        op.create_index(
            "idx_agent_memory_content_hash",
            "agent_memory",
            ["content_hash"],
        )

    # pgvector column + index
    if has_vector:
        existing_vec = conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='agent_memory' AND column_name='embedding_vector'"
            )
        ).fetchone()
        if not existing_vec:
            conn.execute(
                sa.text(
                    f"ALTER TABLE agent_memory "
                    f"ADD COLUMN embedding_vector vector({EMBEDDING_DIM})"
                )
            )
            # IVFFlat index (cosine distance)
            conn.execute(
                sa.text(
                    "CREATE INDEX IF NOT EXISTS idx_agent_memory_embedding_vector "
                    "ON agent_memory USING ivfflat (embedding_vector vector_cosine_ops) "
                    "WITH (lists = 100)"
                )
            )

    # ── global_memory ─────────────────────────────────────────────────────────

    existing_gemb = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='global_memory' AND column_name='embedding'"
        )
    ).fetchone()
    if not existing_gemb:
        op.add_column(
            "global_memory",
            sa.Column("embedding", sa.JSON(), nullable=True),
        )

    if has_vector:
        existing_gvec = conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='global_memory' AND column_name='embedding_vector'"
            )
        ).fetchone()
        if not existing_gvec:
            conn.execute(
                sa.text(
                    f"ALTER TABLE global_memory "
                    f"ADD COLUMN embedding_vector vector({EMBEDDING_DIM})"
                )
            )
            conn.execute(
                sa.text(
                    "CREATE INDEX IF NOT EXISTS idx_global_memory_embedding_vector "
                    "ON global_memory USING ivfflat (embedding_vector vector_cosine_ops) "
                    "WITH (lists = 50)"
                )
            )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop pgvector columns if they exist
    for table in ("agent_memory", "global_memory"):
        try:
            conn.execute(
                sa.text(
                    f"ALTER TABLE {table} DROP COLUMN IF EXISTS embedding_vector"
                )
            )
        except Exception:
            pass

    # Drop content_hash
    try:
        op.drop_index("idx_agent_memory_content_hash", table_name="agent_memory")
        op.drop_column("agent_memory", "content_hash")
    except Exception:
        pass

    # Drop embedding JSON columns
    for table in ("agent_memory", "global_memory"):
        try:
            op.drop_column(table, "embedding")
        except Exception:
            pass
