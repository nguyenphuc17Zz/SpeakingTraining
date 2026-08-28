"""ai_system_phase2

Revision ID: 002_ai_system_phase2
Revises: 001_initial_schema
Create Date: 2026-08-24 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_ai_system_phase2'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ai_usage_records table
    op.create_table(
        'ai_usage_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('task', sa.String(length=50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('fallback_occurred', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('attempts_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('idx_ai_usage_user_id', 'ai_usage_records', ['user_id'])
    op.create_index('idx_ai_usage_provider', 'ai_usage_records', ['provider'])
    op.create_index('idx_ai_usage_task', 'ai_usage_records', ['task'])
    op.create_index('idx_ai_usage_created_at', 'ai_usage_records', ['created_at'])

    # 2. Add routing configuration columns to user_settings
    op.add_column(
        'user_settings',
        sa.Column('routing_mode', sa.String(length=20), nullable=False, server_default='auto'),
    )
    op.add_column(
        'user_settings',
        sa.Column('fallback_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )
    op.add_column(
        'user_settings',
        sa.Column('fallback_priority', sa.String(length=255), nullable=False, server_default='gemini,groq,openrouter'),
    )


def downgrade() -> None:
    op.drop_column('user_settings', 'fallback_priority')
    op.drop_column('user_settings', 'fallback_enabled')
    op.drop_column('user_settings', 'routing_mode')

    op.drop_index('idx_ai_usage_created_at', table_name='ai_usage_records')
    op.drop_index('idx_ai_usage_task', table_name='ai_usage_records')
    op.drop_index('idx_ai_usage_provider', table_name='ai_usage_records')
    op.drop_index('idx_ai_usage_user_id', table_name='ai_usage_records')
    op.drop_table('ai_usage_records')
