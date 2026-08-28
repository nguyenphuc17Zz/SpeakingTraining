"""learning_engine_phase7

Revision ID: 007_learning_engine_phase7
Revises: 006_pronunciation_engine_phase6
Create Date: 2026-08-24 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '007_learning_engine_phase7'
down_revision: Union[str, None] = '006_pronunciation_engine_phase6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. learning_goals
    op.create_table(
        'learning_goals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal_type', sa.String(length=50), nullable=False, server_default='speaking'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_learning_goals_user_id'), 'learning_goals', ['user_id'], unique=False)
    op.create_index(op.f('ix_learning_goals_goal_type'), 'learning_goals', ['goal_type'], unique=False)
    op.create_index(op.f('ix_learning_goals_status'), 'learning_goals', ['status'], unique=False)

    # 2. learning_items
    op.create_table(
        'learning_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('memory_key', sa.String(length=120), nullable=True),
        sa.Column('key', sa.String(length=120), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.String(length=30), nullable=False, server_default='normal'),
        sa.Column('lifecycle', sa.String(length=30), nullable=False, server_default='discovered'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('overall_mastery', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('recognition_mastery', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('production_mastery', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('spontaneous_mastery', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('context_variety_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('priority_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('independent_success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assisted_success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('review_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('review_interval_days', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_practiced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_review_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contexts_used', sa.JSON(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'key', name='uq_learning_item_user_key'),
    )
    op.create_index(op.f('ix_learning_items_user_id'), 'learning_items', ['user_id'], unique=False)
    op.create_index(op.f('ix_learning_items_key'), 'learning_items', ['key'], unique=False)
    op.create_index(op.f('ix_learning_items_memory_key'), 'learning_items', ['memory_key'], unique=False)
    op.create_index(op.f('ix_learning_items_item_type'), 'learning_items', ['item_type'], unique=False)
    op.create_index(op.f('ix_learning_items_lifecycle'), 'learning_items', ['lifecycle'], unique=False)
    op.create_index(op.f('ix_learning_items_status'), 'learning_items', ['status'], unique=False)
    op.create_index(op.f('ix_learning_items_priority_score'), 'learning_items', ['priority_score'], unique=False)
    op.create_index(op.f('ix_learning_items_next_review_at'), 'learning_items', ['next_review_at'], unique=False)

    # 3. exercise_templates
    op.create_table(
        'exercise_templates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('template_key', sa.String(length=100), nullable=False),
        sa.Column('exercise_type', sa.String(length=50), nullable=False),
        sa.Column('item_type_affinity', sa.String(length=50), nullable=True),
        sa.Column('template_version', sa.String(length=20), nullable=False, server_default='v1'),
        sa.Column('title_template', sa.String(length=255), nullable=False),
        sa.Column('objective_template', sa.Text(), nullable=False),
        sa.Column('scenario_template', sa.Text(), nullable=True),
        sa.Column('instruction_template', sa.Text(), nullable=False),
        sa.Column('prompt_frame', sa.Text(), nullable=True),
        sa.Column('expected_pattern_rules', sa.JSON(), nullable=True),
        sa.Column('default_estimated_minutes', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_exercise_templates_template_key'), 'exercise_templates', ['template_key'], unique=True)
    op.create_index(op.f('ix_exercise_templates_exercise_type'), 'exercise_templates', ['exercise_type'], unique=False)

    # 4. exercises
    op.create_table(
        'exercises',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('exercise_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='not_started'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('scenario', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('constraints', sa.JSON(), nullable=True),
        sa.Column('target_patterns', sa.JSON(), nullable=True),
        sa.Column('learning_item_keys', sa.JSON(), nullable=True),
        sa.Column('success_criteria', sa.JSON(), nullable=True),
        sa.Column('acceptable_variants', sa.JSON(), nullable=True),
        sa.Column('difficulty', sa.String(length=30), nullable=False, server_default='normal'),
        sa.Column('scaffold_level', sa.String(length=30), nullable=False, server_default='none'),
        sa.Column('scaffold_hint', sa.Text(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('template_version', sa.String(length=30), nullable=False, server_default='v1'),
        sa.Column('generator_version', sa.String(length=30), nullable=False, server_default='1.0.0'),
        sa.Column('prompt_version', sa.String(length=30), nullable=False, server_default='exercise.gen.v1'),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('exercise_signature', sa.String(length=64), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_exercises_user_id'), 'exercises', ['user_id'], unique=False)
    op.create_index(op.f('ix_exercises_exercise_type'), 'exercises', ['exercise_type'], unique=False)
    op.create_index(op.f('ix_exercises_status'), 'exercises', ['status'], unique=False)
    op.create_index(op.f('ix_exercises_exercise_signature'), 'exercises', ['exercise_signature'], unique=False)

    # 5. exercise_attempts
    op.create_table(
        'exercise_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('exercise_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('pronunciation_attempt_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='in_progress'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('independence_level', sa.String(length=30), nullable=False, server_default='independent'),
        sa.Column('response_speed_ms', sa.Float(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('assessment_confidence', sa.Float(), nullable=True),
        sa.Column('target_usage', sa.String(length=30), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('metrics_json', sa.JSON(), nullable=True),
        sa.Column('mastery_deltas_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['conversation_sessions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pronunciation_attempt_id'], ['pronunciation_attempts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_exercise_attempts_exercise_id'), 'exercise_attempts', ['exercise_id'], unique=False)
    op.create_index(op.f('ix_exercise_attempts_user_id'), 'exercise_attempts', ['user_id'], unique=False)
    op.create_index(op.f('ix_exercise_attempts_session_id'), 'exercise_attempts', ['session_id'], unique=False)
    op.create_index(op.f('ix_exercise_attempts_pronunciation_attempt_id'), 'exercise_attempts', ['pronunciation_attempt_id'], unique=False)
    op.create_index(op.f('ix_exercise_attempts_status'), 'exercise_attempts', ['status'], unique=False)

    # 6. learning_plans
    op.create_table(
        'learning_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('plan_date', sa.String(length=10), nullable=False),
        sa.Column('time_budget_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='active'),
        sa.Column('focus_title', sa.String(length=255), nullable=False),
        sa.Column('focus_reason', sa.Text(), nullable=True),
        sa.Column('generator_version', sa.String(length=30), nullable=False, server_default='1.0.0'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'plan_date', name='uq_user_daily_plan_date'),
    )
    op.create_index(op.f('ix_learning_plans_user_id'), 'learning_plans', ['user_id'], unique=False)
    op.create_index(op.f('ix_learning_plans_plan_date'), 'learning_plans', ['plan_date'], unique=False)
    op.create_index(op.f('ix_learning_plans_status'), 'learning_plans', ['status'], unique=False)

    # 7. learning_plan_items
    op.create_table(
        'learning_plan_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('plan_id', sa.String(length=36), nullable=False),
        sa.Column('exercise_id', sa.String(length=36), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('target_type', sa.String(length=50), nullable=False, server_default='targeted_drill'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['learning_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_learning_plan_items_plan_id'), 'learning_plan_items', ['plan_id'], unique=False)
    op.create_index(op.f('ix_learning_plan_items_exercise_id'), 'learning_plan_items', ['exercise_id'], unique=False)
    op.create_index(op.f('ix_learning_plan_items_status'), 'learning_plan_items', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('learning_plan_items')
    op.drop_table('learning_plans')
    op.drop_table('exercise_attempts')
    op.drop_table('exercises')
    op.drop_table('exercise_templates')
    op.drop_table('learning_items')
    op.drop_table('learning_goals')
