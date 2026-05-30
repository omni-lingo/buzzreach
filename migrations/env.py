"""Alembic environment configuration for BuzzReach migrations.

Imports ``Base.metadata`` so autogenerate picks up all registered models.
Model modules must be imported before metadata is read — each atom adds
its own import line below the ``Base`` import.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.backend.db.base import Base
from src.backend.models.audit_log import AuditLog  # noqa: F401 — register model metadata
from src.backend.models.opportunity import Opportunity  # noqa: F401 — register model metadata
from src.backend.models.seen_url import SeenUrl  # noqa: F401 — register model metadata
from src.backend.models.user import User  # noqa: F401 — register model metadata
from src.backend.settings import Settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = Settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def _build_translate_map() -> dict[str, str | None] | None:
    """Return a schema_translate_map for SQLite, else None."""
    if settings.database_url.startswith("sqlite"):
        return {settings.db_schema: None}
    return None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    translate_map = _build_translate_map()
    with connectable.connect() as connection:
        ctx_kwargs: dict[str, object] = {
            "connection": connection,
            "target_metadata": target_metadata,
            "include_schemas": True,
            "render_as_batch": settings.database_url.startswith("sqlite"),
        }
        if translate_map:
            ctx_kwargs["execution_options"] = {
                "schema_translate_map": translate_map,
            }

        context.configure(**ctx_kwargs)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
