"""pronunciation_engine_phase6

Revision ID: 006_pronunciation_engine_phase6
Revises: 005_learner_memory_phase5
Create Date: 2026-08-24 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '006_pronunciation_engine_phase6'
down_revision: Union[str, None] = '005_learner_memory_phase5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create pronunciation_attempts table
    op.create_table(
        'pronunciation_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('turn_id', sa.String(length=36), nullable=True),
        sa.Column('reference_text', sa.Text(), nullable=False),
        sa.Column('expected_reading', sa.Text(), nullable=True),
        sa.Column('user_text', sa.Text(), nullable=True),
        sa.Column('target_type', sa.String(length=30), nullable=False, server_default='sentence'),
        sa.Column('reference_type', sa.String(length=30), nullable=False, server_default='synthetic'),
        sa.Column('analysis_status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('overall_confidence', sa.String(length=30), nullable=True),
        sa.Column('score_interpretation', sa.String(length=30), nullable=True),
        sa.Column('engine_version', sa.String(length=30), nullable=False, server_default='1.0.0'),
        sa.Column('scores_json', sa.JSON(), nullable=True),
        sa.Column('feedback_json', sa.JSON(), nullable=True),
        sa.Column('acoustic_metadata_json', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['turn_id'], ['conversation_turns.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pronunciation_attempts_user_id'), 'pronunciation_attempts', ['user_id'], unique=False)
    op.create_index(op.f('ix_pronunciation_attempts_session_id'), 'pronunciation_attempts', ['session_id'], unique=False)
    op.create_index(op.f('ix_pronunciation_attempts_turn_id'), 'pronunciation_attempts', ['turn_id'], unique=False)
    op.create_index(op.f('ix_pronunciation_attempts_analysis_status'), 'pronunciation_attempts', ['analysis_status'], unique=False)

    # 2. Create pronunciation_practice_targets table
    op.create_table(
        'pronunciation_practice_targets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('target_text', sa.Text(), nullable=False),
        sa.Column('target_reading', sa.Text(), nullable=False),
        sa.Column('target_type', sa.String(length=30), nullable=False, server_default='word'),
        sa.Column('difficulty', sa.String(length=30), nullable=False, server_default='beginner'),
        sa.Column('weak_area_key', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='phoneme'),
        sa.Column('hint', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pronunciation_practice_targets_user_id'), 'pronunciation_practice_targets', ['user_id'], unique=False)
    op.create_index(op.f('ix_pronunciation_practice_targets_weak_area_key'), 'pronunciation_practice_targets', ['weak_area_key'], unique=False)


def downgrade() -> None:
    op.drop_table('pronunciation_practice_targets')
    op.drop_table('pronunciation_attempts')
