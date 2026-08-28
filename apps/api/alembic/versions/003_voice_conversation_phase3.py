"""voice_conversation_phase3

Revision ID: 003_voice_conversation_phase3
Revises: 002_ai_system_phase2
Create Date: 2026-08-24 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_voice_conversation_phase3'
down_revision: Union[str, None] = '002_ai_system_phase2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update conversation_sessions table columns
    op.add_column('conversation_sessions', sa.Column('mode', sa.String(length=20), nullable=False, server_default='conversation'))
    op.add_column('conversation_sessions', sa.Column('provider_preference', sa.String(length=50), nullable=True))
    op.add_column('conversation_sessions', sa.Column('model_preference', sa.String(length=100), nullable=True))
    op.add_column('conversation_sessions', sa.Column('stt_provider_preference', sa.String(length=50), nullable=True))
    op.add_column('conversation_sessions', sa.Column('stt_model_preference', sa.String(length=100), nullable=True))
    op.add_column('conversation_sessions', sa.Column('tts_provider_preference', sa.String(length=50), nullable=True))
    op.add_column('conversation_sessions', sa.Column('tts_voice_preference', sa.String(length=100), nullable=True))
    op.add_column('conversation_sessions', sa.Column('duration_seconds', sa.Integer(), nullable=True))

    # 2. Create conversation_turns table
    op.create_table(
        'conversation_turns',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('speaker', sa.String(length=20), nullable=False),
        sa.Column('transcript', sa.Text(), nullable=False),
        sa.Column('client_turn_id', sa.String(length=100), nullable=True),
        sa.Column('stt_provider', sa.String(length=50), nullable=True),
        sa.Column('stt_model', sa.String(length=100), nullable=True),
        sa.Column('ai_provider', sa.String(length=50), nullable=True),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('tts_provider', sa.String(length=50), nullable=True),
        sa.Column('tts_voice', sa.String(length=100), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('feedback_hint', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('idx_conversation_turns_session_id', 'conversation_turns', ['session_id'])
    op.create_index('idx_conversation_turns_client_turn_id', 'conversation_turns', ['client_turn_id'])
    op.create_index('idx_conversation_turns_sequence', 'conversation_turns', ['session_id', 'sequence'])


def downgrade() -> None:
    op.drop_index('idx_conversation_turns_sequence', table_name='conversation_turns')
    op.drop_index('idx_conversation_turns_client_turn_id', table_name='conversation_turns')
    op.drop_index('idx_conversation_turns_session_id', table_name='conversation_turns')
    op.drop_table('conversation_turns')

    op.drop_column('conversation_sessions', 'duration_seconds')
    op.drop_column('conversation_sessions', 'tts_voice_preference')
    op.drop_column('conversation_sessions', 'tts_provider_preference')
    op.drop_column('conversation_sessions', 'stt_model_preference')
    op.drop_column('conversation_sessions', 'stt_provider_preference')
    op.drop_column('conversation_sessions', 'model_preference')
    op.drop_column('conversation_sessions', 'provider_preference')
    op.drop_column('conversation_sessions', 'mode')
