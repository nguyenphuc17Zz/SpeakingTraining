"""Mode 6 Speaking Ramp — add ramp_sessions table

Revision ID: 011_speaking_ramp_mode6
Revises: 010_reflex_automaticity_phase7b
Create Date: 2026-09-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "011_speaking_ramp_mode6"
down_revision: Union[str, None] = "010_reflex_automaticity_phase7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ramp_sessions",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("state", sa.String(30), default="idle", nullable=False, index=True),
        sa.Column("stage", sa.Integer(), default=0, nullable=False),
        sa.Column("support_level", sa.Integer(), default=3, nullable=False),
        sa.Column("stage_start", sa.Integer(), default=0, nullable=False),
        sa.Column("support_level_start", sa.Integer(), default=3, nullable=False),
        sa.Column("desired_minutes", sa.Integer(), default=15, nullable=False),
        sa.Column("session_goal", sa.String(200), nullable=True),
        sa.Column("topic_context", sa.Text(), nullable=True),
        sa.Column("exercises_completed", sa.Integer(), default=0, nullable=False),
        sa.Column("exercises_total", sa.Integer(), default=0, nullable=False),
        sa.Column("independent_success_count", sa.Integer(), default=0, nullable=False),
        sa.Column("full_sentence_count", sa.Integer(), default=0, nullable=False),
        sa.Column("elaboration_success_count", sa.Integer(), default=0, nullable=False),
        sa.Column("reason_success_count", sa.Integer(), default=0, nullable=False),
        sa.Column("example_success_count", sa.Integer(), default=0, nullable=False),
        sa.Column("followup_success_count", sa.Integer(), default=0, nullable=False),
        sa.Column("max_speech_duration_ms", sa.Integer(), default=0, nullable=False),
        sa.Column("total_speech_duration_ms", sa.Integer(), default=0, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_results", sa.JSON(), nullable=True),
        sa.Column("stage_attempt_buffer", sa.JSON(), nullable=True),
        sa.Column("milestones_achieved", sa.JSON(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ramp_sessions_user_state", "ramp_sessions", ["user_id", "state"])


def downgrade() -> None:
    op.drop_index("ix_ramp_sessions_user_state", "ramp_sessions")
    op.drop_table("ramp_sessions")
