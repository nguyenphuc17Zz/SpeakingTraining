"""
Database Schema Synchronizer & SQLite Migration Guard.
Ensures that all columns defined in SQLAlchemy models exist in the active database.
Particularly essential for SQLite local development where create_all does not add new columns to existing tables.
"""

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.logging import logger
from app.infrastructure.database.base import Base

# Import all domain models to ensure Base.metadata and ORM registries are fully populated
import app.domains.ai.models  # noqa
import app.domains.analytics.models  # noqa
import app.domains.conversation.models  # noqa
import app.domains.conversation_intelligence.models  # noqa
import app.domains.gamification.models  # noqa
import app.domains.learner_memory.models  # noqa
import app.domains.learning.models  # noqa
import app.domains.personas.models  # noqa
import app.domains.providers.models  # noqa
import app.domains.settings.models  # noqa
import app.domains.shadowing.models  # noqa
import app.domains.users.models  # noqa


async def sync_database_schema(engine: AsyncEngine) -> None:
    """Inspects tables and automatically adds any missing columns."""
    async with engine.begin() as conn:
        # Create any completely new tables first
        await conn.run_sync(Base.metadata.create_all)

        # Inspect table columns for SQLite / Postgres
        def check_columns(sync_conn):
            inspector = inspect(sync_conn)
            for table_name, table in Base.metadata.tables.items():
                if not inspector.has_table(table_name):
                    continue

                existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                for col in table.columns:
                    if col.name not in existing_cols:
                        col_type = col.type.compile(sync_conn.dialect)
                        nullable = "NULL" if col.nullable else "NOT NULL DEFAULT ''"
                        if col.default is not None and hasattr(col.default, "arg"):
                            default_val = col.default.arg
                            if isinstance(default_val, (int, float)):
                                nullable = f"DEFAULT {default_val}"
                            elif isinstance(default_val, bool):
                                nullable = f"DEFAULT {1 if default_val else 0}"
                            elif isinstance(default_val, str):
                                nullable = f"DEFAULT '{default_val}'"

                        alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type} {nullable}"
                        logger.info(f"[DB Schema Sync] Adding missing column: {table_name}.{col.name} ({col_type})")
                        try:
                            sync_conn.execute(text(alter_stmt))
                        except Exception as err:
                            logger.warning(f"[DB Schema Sync] Could not alter {table_name}.{col.name}: {err}")

        await conn.run_sync(check_columns)
