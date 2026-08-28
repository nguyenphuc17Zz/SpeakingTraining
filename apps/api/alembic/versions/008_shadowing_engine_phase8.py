"""shadowing_engine_phase8

Revision ID: 008_shadowing_engine_phase8
Revises: 007_learning_engine_phase7
Create Date: 2026-08-24 21:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '008_shadowing_engine_phase8'
down_revision: Union[str, None] = '007_learning_engine_phase7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. shadowing_videos
    op.create_table(
        'shadowing_videos',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=64), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('canonical_url', sa.String(length=500), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('channel_name', sa.String(length=255), nullable=False),
        sa.Column('channel_id', sa.String(length=100), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=1000), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=30), nullable=False, server_default='ja'),
        sa.Column('source_status', sa.String(length=50), nullable=False, server_default='available'),
        sa.Column('import_status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('metadata_fetched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('overall_difficulty', sa.String(length=30), nullable=False, server_default='normal'),
        sa.Column('summary_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shadowing_videos_video_id'), 'shadowing_videos', ['video_id'], unique=True)
    op.create_index(op.f('ix_shadowing_videos_import_status'), 'shadowing_videos', ['import_status'], unique=False)

    # 2. shadowing_transcripts
    op.create_table(
        'shadowing_transcripts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='youtube'),
        sa.Column('source_version', sa.String(length=50), nullable=False, server_default='v1'),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=30), nullable=False, server_default='ja'),
        sa.Column('quality', sa.String(length=30), nullable=False, server_default='high'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('transcript_hash', sa.String(length=64), nullable=True),
        sa.Column('raw_data_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['shadowing_videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shadowing_transcripts_video_id'), 'shadowing_transcripts', ['video_id'], unique=False)
    op.create_index(op.f('ix_shadowing_transcripts_is_active'), 'shadowing_transcripts', ['is_active'], unique=False)

    # 3. shadowing_segments
    op.create_table(
        'shadowing_segments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transcript_id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('start_time', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('end_time', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('normalized_text', sa.Text(), nullable=False),
        sa.Column('reading', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=30), nullable=False, server_default='ja'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('speaker_id', sa.String(length=50), nullable=False, server_default='Speaker A'),
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('difficulty_json', sa.JSON(), nullable=True),
        sa.Column('vocabulary_json', sa.JSON(), nullable=True),
        sa.Column('grammar_json', sa.JSON(), nullable=True),
        sa.Column('expressions_json', sa.JSON(), nullable=True),
        sa.Column('candidate_categories_json', sa.JSON(), nullable=True),
        sa.Column('recommendation_score', sa.Float(), nullable=True),
        sa.Column('recommendation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['transcript_id'], ['shadowing_transcripts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['shadowing_videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shadowing_segments_transcript_id'), 'shadowing_segments', ['transcript_id'], unique=False)
    op.create_index(op.f('ix_shadowing_segments_video_id'), 'shadowing_segments', ['video_id'], unique=False)
    op.create_index(op.f('ix_shadowing_segments_sequence'), 'shadowing_segments', ['sequence'], unique=False)
    op.create_index(op.f('ix_shadowing_segments_start_time'), 'shadowing_segments', ['start_time'], unique=False)

    # 4. shadowing_import_jobs
    op.create_table(
        'shadowing_import_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('stage_statuses_json', sa.JSON(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['shadowing_videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shadowing_import_jobs_video_id'), 'shadowing_import_jobs', ['video_id'], unique=False)
    op.create_index(op.f('ix_shadowing_import_jobs_user_id'), 'shadowing_import_jobs', ['user_id'], unique=False)
    op.create_index(op.f('ix_shadowing_import_jobs_status'), 'shadowing_import_jobs', ['status'], unique=False)

    # 5. shadowing_bookmarks
    op.create_table(
        'shadowing_bookmarks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('segment_id', sa.String(length=36), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['shadowing_videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], ['shadowing_segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'segment_id', name='uq_shadowing_bookmark_user_segment'),
    )
    op.create_index(op.f('ix_shadowing_bookmarks_user_id'), 'shadowing_bookmarks', ['user_id'], unique=False)
    op.create_index(op.f('ix_shadowing_bookmarks_video_id'), 'shadowing_bookmarks', ['video_id'], unique=False)
    op.create_index(op.f('ix_shadowing_bookmarks_segment_id'), 'shadowing_bookmarks', ['segment_id'], unique=False)

    # 6. shadowing_segment_progress
    op.create_table(
        'shadowing_segment_progress',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('segment_id', sa.String(length=36), nullable=False),
        sa.Column('exercise_id', sa.String(length=36), nullable=True),
        sa.Column('listen_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shadow_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('best_score', sa.Float(), nullable=True),
        sa.Column('mastery', sa.String(length=30), nullable=False, server_default='discovered'),
        sa.Column('last_practiced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_attempt_result_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['shadowing_videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], ['shadowing_segments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'segment_id', name='uq_shadowing_progress_user_segment'),
    )
    op.create_index(op.f('ix_shadowing_segment_progress_user_id'), 'shadowing_segment_progress', ['user_id'], unique=False)
    op.create_index(op.f('ix_shadowing_segment_progress_video_id'), 'shadowing_segment_progress', ['video_id'], unique=False)
    op.create_index(op.f('ix_shadowing_segment_progress_segment_id'), 'shadowing_segment_progress', ['segment_id'], unique=False)
    op.create_index(op.f('ix_shadowing_segment_progress_exercise_id'), 'shadowing_segment_progress', ['exercise_id'], unique=False)
    op.create_index(op.f('ix_shadowing_segment_progress_mastery'), 'shadowing_segment_progress', ['mastery'], unique=False)

    # 7. shadowing_video_progress
    op.create_table(
        'shadowing_video_progress',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('video_id', sa.String(length=36), nullable=False),
        sa.Column('watch_progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('shadow_progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mastery_progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('segments_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_practice_time_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('best_score', sa.Float(), nullable=True),
        sa.Column('last_position_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['shadowing_videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'video_id', name='uq_shadowing_video_progress_user_video'),
    )
    op.create_index(op.f('ix_shadowing_video_progress_user_id'), 'shadowing_video_progress', ['user_id'], unique=False)
    op.create_index(op.f('ix_shadowing_video_progress_video_id'), 'shadowing_video_progress', ['video_id'], unique=False)


def downgrade() -> None:
    op.drop_table('shadowing_video_progress')
    op.drop_table('shadowing_segment_progress')
    op.drop_table('shadowing_bookmarks')
    op.drop_table('shadowing_import_jobs')
    op.drop_table('shadowing_segments')
    op.drop_table('shadowing_transcripts')
    op.drop_table('shadowing_videos')
