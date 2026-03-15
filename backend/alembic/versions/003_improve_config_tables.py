"""improve config tables

Revision ID: 003
Revises: 002
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, Sequence[str], None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to system_config if they don't exist
    try:
        op.add_column('system_config', sa.Column('validation_rules', sa.JSON(), nullable=True))
    except:
        pass
    
    # Create indexes for better performance
    try:
        op.create_index('idx_system_config_updated', 'system_config', ['updated_at'], unique=False)
    except:
        pass
    
    try:
        op.create_index('idx_config_history_changed', 'config_history', ['changed_at'], unique=False)
    except:
        pass


def downgrade() -> None:
    try:
        op.drop_index('idx_system_config_updated', table_name='system_config')
    except:
        pass
    
    try:
        op.drop_index('idx_config_history_changed', table_name='config_history')
    except:
        pass
    
    try:
        op.drop_column('system_config', 'validation_rules')
    except:
        pass
