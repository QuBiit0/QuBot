"""add config tables

Revision ID: 002
Revises: 001
Create Date: 2026-03-14 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # system_config table
    op.create_table('system_config',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('key', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('category', sa.Enum('GENERAL', 'SECURITY', 'LLM', 'MESSAGING', 'INTEGRATIONS', 'FEATURES', 'UI', 'ADVANCED', name='configcategory'), nullable=False),
    sa.Column('value_type', sa.Enum('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'JSON', 'SECRET', name='configvaluetype'), nullable=False),
    sa.Column('value_string', sa.Text(), nullable=True),
    sa.Column('value_integer', sa.Integer(), nullable=True),
    sa.Column('value_float', sa.Float(), nullable=True),
    sa.Column('value_boolean', sa.Boolean(), nullable=True),
    sa.Column('value_json', sa.JSON(), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
    sa.Column('is_editable', sa.Boolean(), nullable=False),
    sa.Column('is_secret', sa.Boolean(), nullable=False),
    sa.Column('requires_restart', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('updated_by', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('key')
    )
    op.create_index('idx_config_category_key', 'system_config', ['category', 'key'], unique=False)
    op.create_index(op.f('ix_system_config_category'), 'system_config', ['category'], unique=False)
    op.create_index(op.f('ix_system_config_key'), 'system_config', ['key'], unique=False)
    
    # config_preset table
    op.create_table('config_preset',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
    sa.Column('values', sa.JSON(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('category', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_config_preset_is_active'), 'config_preset', ['is_active'], unique=False)
    
    # config_history table
    op.create_table('config_history',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('config_key', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('category', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('old_value', sa.Text(), nullable=True),
    sa.Column('new_value', sa.Text(), nullable=True),
    sa.Column('changed_by', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('changed_at', sa.DateTime(), nullable=False),
    sa.Column('change_reason', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_config_history_key_time', 'config_history', ['config_key', 'changed_at'], unique=False)
    op.create_index(op.f('ix_config_history_config_key'), 'config_history', ['config_key'], unique=False)
    
    # environment_config table
    op.create_table('environment_config',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('environment', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('key', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('value', sa.JSON(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('environment', 'key', name='idx_env_config_env_key')
    )
    op.create_index(op.f('ix_environment_config_environment'), 'environment_config', ['environment'], unique=False)


def downgrade() -> None:
    op.drop_table('environment_config')
    op.drop_table('config_history')
    op.drop_table('config_preset')
    op.drop_table('system_config')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS configcategory')
    op.execute('DROP TYPE IF EXISTS configvaluetype')
