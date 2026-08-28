"""Phase 9 Audio Platform and Voice Experience Migration

Revision ID: 009_audio_platform_phase9
Revises: 008_shadowing_engine_phase8
Create Date: 2026-08-24 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "009_audio_platform_phase9"
down_revision: Union[str, None] = "008_shadowing_engine_phase8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create voice_profiles table
    op.create_table(
        "voice_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="voicevox"),
        sa.Column("voice_id", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Create audio_presets table
    op.create_table(
        "audio_presets",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("volume", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("loop_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("pause_after_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("auto_play", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("record_after", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Add columns to user_settings table
    with op.batch_alter_table("user_settings") as batch_op:
        batch_op.add_column(sa.Column("default_voice_profile_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("default_tts_speed", sa.Float(), nullable=False, server_default="1.0"))
        batch_op.add_column(sa.Column("default_tts_pitch", sa.Float(), nullable=False, server_default="0.0"))
        batch_op.add_column(sa.Column("tts_fallback_enabled", sa.Boolean(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("tts_fallback_provider", sa.String(length=50), nullable=False, server_default="voicevox"))
        batch_op.add_column(sa.Column("tts_fallback_voice_id", sa.String(length=50), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("auto_play_ai_response", sa.Boolean(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("auto_play_references", sa.Boolean(), nullable=False, server_default="1"))


def downgrade() -> None:
    with op.batch_alter_table("user_settings") as batch_op:
        batch_op.drop_column("auto_play_references")
        batch_op.drop_column("auto_play_ai_response")
        batch_op.drop_column("tts_fallback_voice_id")
        batch_op.drop_column("tts_fallback_provider")
        batch_op.drop_column("tts_fallback_enabled")
        batch_op.drop_column("default_tts_pitch")
        batch_op.drop_column("default_tts_speed")
        batch_op.drop_column("default_voice_profile_id")

    op.drop_table("audio_presets")
    op.drop_table("voice_profiles")
