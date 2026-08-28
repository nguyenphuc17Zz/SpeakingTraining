"""learner_memory_phase5

Revision ID: 005_learner_memory_phase5
Revises: 004_conversation_intelligence_phase4
Create Date: 2026-08-24 19:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_learner_memory_phase5'
down_revision: Union[str, None] = '004_conversation_intelligence_phase4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create learner_memories table
    op.create_table(
        'learner_memories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('memory_type', sa.String(length=50), nullable=False),
        sa.Column('key', sa.String(length=120), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('evidence_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('severity', sa.String(length=30), nullable=False, server_default='SHOULD_FIX'),
        sa.Column('severity_score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('priority_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('mastery', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('correct_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trend', sa.String(length=30), nullable=False, server_default='new'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='new'),
        sa.Column('is_regression', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('contexts_used', sa.JSON(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'key', name='uq_learner_memory_user_key'),
    )
    op.create_index('idx_learner_memories_user_id', 'learner_memories', ['user_id'])
    op.create_index('idx_learner_memories_key', 'learner_memories', ['key'])
    op.create_index('idx_learner_memories_memory_type', 'learner_memories', ['memory_type'])
    op.create_index('idx_learner_memories_priority_score', 'learner_memories', ['priority_score'])
    op.create_index('idx_learner_memories_last_seen', 'learner_memories', ['last_seen'])
    op.create_index('idx_learner_memories_trend', 'learner_memories', ['trend'])
    op.create_index('idx_learner_memories_status', 'learner_memories', ['status'])

    # 2. Create memory_evidences table
    op.create_table(
        'memory_evidences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('memory_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('turn_id', sa.String(length=36), nullable=True),
        sa.Column('turn_analysis_id', sa.String(length=36), nullable=True),
        sa.Column('correction_id', sa.String(length=36), nullable=True),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('original_snippet', sa.Text(), nullable=True),
        sa.Column('corrected_snippet', sa.Text(), nullable=True),
        sa.Column('context_tag', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['correction_id'], ['analysis_corrections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['memory_id'], ['learner_memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['turn_analysis_id'], ['turn_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['turn_id'], ['conversation_turns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('memory_id', 'session_id', 'turn_id', 'correction_id', 'evidence_type', name='uq_memory_evidence_source'),
    )
    op.create_index('idx_memory_evidences_memory_id', 'memory_evidences', ['memory_id'])
    op.create_index('idx_memory_evidences_user_id', 'memory_evidences', ['user_id'])
    op.create_index('idx_memory_evidences_session_id', 'memory_evidences', ['session_id'])
    op.create_index('idx_memory_evidences_turn_id', 'memory_evidences', ['turn_id'])
    op.create_index('idx_memory_evidences_created_at', 'memory_evidences', ['created_at'])

    # 3. Create learner_profiles table
    op.create_table(
        'learner_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('overall_level', sa.String(length=30), nullable=False, server_default='intermediate'),
        sa.Column('speaking_level', sa.String(length=30), nullable=False, server_default='intermediate'),
        sa.Column('fluency_level', sa.String(length=30), nullable=False, server_default='intermediate'),
        sa.Column('grammar_level', sa.String(length=30), nullable=False, server_default='intermediate'),
        sa.Column('vocabulary_level', sa.String(length=30), nullable=False, server_default='intermediate'),
        sa.Column('naturalness_level', sa.String(length=30), nullable=False, server_default='intermediate'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('level_confidence', sa.String(length=30), nullable=False, server_default='insufficient_evidence'),
        sa.Column('total_sessions_analyzed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_turns_analyzed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_response_speed_ms', sa.Float(), nullable=True),
        sa.Column('current_focus', sa.String(length=150), nullable=True),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('weaknesses', sa.JSON(), nullable=True),
        sa.Column('learning_goals', sa.JSON(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('summary_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('summary_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_recalculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('idx_learner_profiles_user_id', 'learner_profiles', ['user_id'])

    # 4. Create memory_feedback table
    op.create_table(
        'memory_feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('memory_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=30), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['memory_id'], ['learner_memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_memory_feedback_memory_id', 'memory_feedback', ['memory_id'])
    op.create_index('idx_memory_feedback_user_id', 'memory_feedback', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_memory_feedback_user_id', table_name='memory_feedback')
    op.drop_index('idx_memory_feedback_memory_id', table_name='memory_feedback')
    op.drop_table('memory_feedback')

    op.drop_index('idx_learner_profiles_user_id', table_name='learner_profiles')
    op.drop_table('learner_profiles')

    op.drop_index('idx_memory_evidences_created_at', table_name='memory_evidences')
    op.drop_index('idx_memory_evidences_turn_id', table_name='memory_evidences')
    op.drop_index('idx_memory_evidences_session_id', table_name='memory_evidences')
    op.drop_index('idx_memory_evidences_user_id', table_name='memory_evidences')
    op.drop_index('idx_memory_evidences_memory_id', table_name='memory_evidences')
    op.drop_table('memory_evidences')

    op.drop_index('idx_learner_memories_status', table_name='learner_memories')
    op.drop_index('idx_learner_memories_trend', table_name='learner_memories')
    op.drop_index('idx_learner_memories_last_seen', table_name='learner_memories')
    op.drop_index('idx_learner_memories_priority_score', table_name='learner_memories')
    op.drop_index('idx_learner_memories_memory_type', table_name='learner_memories')
    op.drop_index('idx_learner_memories_key', table_name='learner_memories')
    op.drop_index('idx_learner_memories_user_id', table_name='learner_memories')
    op.drop_table('learner_memories')
