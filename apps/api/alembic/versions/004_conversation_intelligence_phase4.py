"""conversation_intelligence_phase4

Revision ID: 004_conversation_intelligence_phase4
Revises: 003_voice_conversation_phase3
Create Date: 2026-08-24 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_conversation_intelligence_phase4'
down_revision: Union[str, None] = '003_voice_conversation_phase3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create turn_analyses table
    op.create_table(
        'turn_analyses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('turn_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('overall_quality_score', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('communicative_success', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_suspicious_transcript', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('context_notes', sa.JSON(), nullable=True),
        sa.Column('input_hash', sa.String(length=64), nullable=True),
        sa.Column('analyzer_version', sa.String(length=30), nullable=False, server_default='1.0.0'),
        sa.Column('prompt_version', sa.String(length=50), nullable=False, server_default='conversation.analysis.v1'),
        sa.Column('ai_provider', sa.String(length=50), nullable=True),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['turn_id'], ['conversation_turns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_turn_analyses_turn_id', 'turn_analyses', ['turn_id'])
    op.create_index('idx_turn_analyses_session_id', 'turn_analyses', ['session_id'])
    op.create_index('idx_turn_analyses_input_hash', 'turn_analyses', ['input_hash'])

    # 2. Create analysis_corrections table
    op.create_table(
        'analysis_corrections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('turn_analysis_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=30), nullable=False),
        sa.Column('severity_score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('original', sa.Text(), nullable=False),
        sa.Column('corrected', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('native_alternative', sa.Text(), nullable=True),
        sa.Column('acceptable_alternatives', sa.JSON(), nullable=True),
        sa.Column('context_note', sa.Text(), nullable=True),
        sa.Column('confidence', sa.String(length=20), nullable=False, server_default='high'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['turn_analysis_id'], ['turn_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_analysis_corrections_turn_analysis_id', 'analysis_corrections', ['turn_analysis_id'])

    # 3. Create grammar_notes table
    op.create_table(
        'grammar_notes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('turn_analysis_id', sa.String(length=36), nullable=False),
        sa.Column('grammar_pattern', sa.String(length=100), nullable=False),
        sa.Column('user_usage', sa.Text(), nullable=False),
        sa.Column('correct_usage', sa.Text(), nullable=False),
        sa.Column('short_explanation', sa.Text(), nullable=False),
        sa.Column('example_sentence', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['turn_analysis_id'], ['turn_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_grammar_notes_turn_analysis_id', 'grammar_notes', ['turn_analysis_id'])

    # 4. Create vocabulary_notes table
    op.create_table(
        'vocabulary_notes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('turn_analysis_id', sa.String(length=36), nullable=False),
        sa.Column('original_word', sa.String(length=100), nullable=False),
        sa.Column('suggested_alternatives', sa.JSON(), nullable=True),
        sa.Column('nuance_explanation', sa.Text(), nullable=False),
        sa.Column('jlpt_level', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['turn_analysis_id'], ['turn_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_vocabulary_notes_turn_analysis_id', 'vocabulary_notes', ['turn_analysis_id'])

    # 5. Create session_analyses table
    op.create_table(
        'session_analyses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=False, server_default='75'),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('weaknesses', sa.JSON(), nullable=True),
        sa.Column('repeated_issues', sa.JSON(), nullable=True),
        sa.Column('top_recommendations', sa.JSON(), nullable=True),
        sa.Column('total_user_turns_analyzed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_corrections_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('must_fix_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('should_fix_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('native_alt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('grammar_summary', sa.JSON(), nullable=True),
        sa.Column('vocabulary_summary', sa.JSON(), nullable=True),
        sa.Column('analyzer_version', sa.String(length=30), nullable=False, server_default='1.0.0'),
        sa.Column('prompt_version', sa.String(length=50), nullable=False, server_default='session.analysis.v1'),
        sa.Column('ai_provider', sa.String(length=50), nullable=True),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index('idx_session_analyses_session_id', 'session_analyses', ['session_id'])

    # 6. Create analysis_jobs table
    op.create_table(
        'analysis_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='queued'),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('turn_id', sa.String(length=36), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['turn_id'], ['conversation_turns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_analysis_jobs_session_id', 'analysis_jobs', ['session_id'])
    op.create_index('idx_analysis_jobs_turn_id', 'analysis_jobs', ['turn_id'])
    op.create_index('idx_analysis_jobs_status', 'analysis_jobs', ['status'])

    # 7. Create analysis_user_feedback table
    op.create_table(
        'analysis_user_feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('turn_analysis_id', sa.String(length=36), nullable=True),
        sa.Column('correction_id', sa.String(length=36), nullable=True),
        sa.Column('rating', sa.String(length=30), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['correction_id'], ['analysis_corrections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['turn_analysis_id'], ['turn_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_analysis_user_feedback_user_id', 'analysis_user_feedback', ['user_id'])
    op.create_index('idx_analysis_user_feedback_correction_id', 'analysis_user_feedback', ['correction_id'])


def downgrade() -> None:
    op.drop_index('idx_analysis_user_feedback_correction_id', table_name='analysis_user_feedback')
    op.drop_index('idx_analysis_user_feedback_user_id', table_name='analysis_user_feedback')
    op.drop_table('analysis_user_feedback')

    op.drop_index('idx_analysis_jobs_status', table_name='analysis_jobs')
    op.drop_index('idx_analysis_jobs_turn_id', table_name='analysis_jobs')
    op.drop_index('idx_analysis_jobs_session_id', table_name='analysis_jobs')
    op.drop_table('analysis_jobs')

    op.drop_index('idx_session_analyses_session_id', table_name='session_analyses')
    op.drop_table('session_analyses')

    op.drop_index('idx_vocabulary_notes_turn_analysis_id', table_name='vocabulary_notes')
    op.drop_table('vocabulary_notes')

    op.drop_index('idx_grammar_notes_turn_analysis_id', table_name='grammar_notes')
    op.drop_table('grammar_notes')

    op.drop_index('idx_analysis_corrections_turn_analysis_id', table_name='analysis_corrections')
    op.drop_table('analysis_corrections')

    op.drop_index('idx_turn_analyses_input_hash', table_name='turn_analyses')
    op.drop_index('idx_turn_analyses_session_id', table_name='turn_analyses')
    op.drop_index('idx_turn_analyses_turn_id', table_name='turn_analyses')
    op.drop_table('turn_analyses')
