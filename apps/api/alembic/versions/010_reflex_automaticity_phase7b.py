"""Phase 7b Reflex Automaticity — add automaticity_mastery to learning_items

Revision ID: 010_reflex_automaticity_phase7b
Revises: 009_audio_platform_phase9
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "010_reflex_automaticity_phase7b"
down_revision: Union[str, None] = "009_audio_platform_phase9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("learning_items") as batch_op:
        batch_op.add_column(sa.Column("automaticity_mastery", sa.Float(), nullable=False, server_default="0.0"))
        batch_op.create_index("ix_learning_items_automaticity", ["automaticity_mastery"])

    # Reflex exercises reuse learning tables; no new tables required.
    # Extra indices for reflex query patterns (exercise_type + timer metadata)
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.create_index("ix_exercises_type_user", ["exercise_type", "user_id"])

    with op.batch_alter_table("exercise_attempts") as batch_op:
        batch_op.create_index("ix_attempts_exercise_created", ["exercise_id", "created_at"])


def downgrade() -> None:
    with op.batch_alter_table("exercise_attempts") as batch_op:
        try:
            batch_op.drop_index("ix_attempts_exercise_created")
        except Exception:
            pass
    with op.batch_alter_table("exercises") as batch_op:
        try:
            batch_op.drop_index("ix_exercises_type_user")
        except Exception:
            pass
    with op.batch_alter_table("learning_items") as batch_op:
        try:
            batch_op.drop_index("ix_learning_items_automaticity")
        except Exception:
            pass
        batch_op.drop_column("automaticity_mastery")
