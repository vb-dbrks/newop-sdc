"""Async DB engine, session factory, and startup `init_db()`.

Per ADR 0021, schema is auto-created on app startup via SQLAlchemy
`Base.metadata.create_all`. Migrations are deferred until production
GxP / zero-downtime requirements appear.

Lakebase auth
-------------
When the app is deployed on Databricks Apps with a Lakebase resource bound,
the runtime injects PGHOST / PGPORT / PGUSER / PGDATABASE but NOT a static
password — Postgres connections authenticate with a short-lived OAuth token
minted from the app's service principal. We:

  1. Build the async engine from `settings.database_url` minus credentials.
  2. Pass a `password` *callable* into asyncpg via `connect_args` so each
     new physical connection mints a fresh token through the Databricks SDK.
  3. Cap pool recycle at < the token TTL so we never try to reuse a stale
     authenticated connection past its token's life.

Locally (sqlite+aiosqlite or a plain Postgres URL with creds) none of the
Lakebase plumbing kicks in — we just hand SQLAlchemy the URL as-is.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from urllib.parse import urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.domain.models import Base
from backend.settings import settings

logger = logging.getLogger(__name__)


_LAKEBASE_TOKEN_RECYCLE_SECONDS = 30 * 60  # tokens are ~1h; recycle pool well before


def _is_lakebase_url(url: str) -> bool:
    """Lakebase URL: asyncpg dialect, host ending in .azuredatabricks.net, no inline creds."""
    if not url.startswith("postgresql+asyncpg://"):
        return False
    parsed = urlparse(url)
    if parsed.password:
        # If a password is already baked into the URL, defer to it.
        return False
    host = parsed.hostname or ""
    return host.endswith(".azuredatabricks.net") or bool(os.environ.get("PGHOST"))


def _build_engine_kwargs(url: str) -> tuple[str, dict[str, object]]:
    """Return (sanitized_url, kwargs_for_create_async_engine)."""
    if not _is_lakebase_url(url):
        return url, {"echo": False, "future": True}

    # Lakebase: strip user/pass from the URL (asyncpg will get them via connect_args).
    parsed = urlparse(url)
    pg_user = parsed.username or os.environ.get("PGUSER")
    pg_host = parsed.hostname or os.environ.get("PGHOST")
    pg_port = parsed.port or int(os.environ.get("PGPORT", "5432"))
    pg_db = (parsed.path or "/").lstrip("/") or os.environ.get("PGDATABASE")
    netloc = f"{pg_host}:{pg_port}"
    sanitized = urlunparse(parsed._replace(netloc=netloc))

    if not pg_user:
        raise RuntimeError(
            "Lakebase mode but PGUSER is not set. The Databricks Apps runtime "
            "should inject this when the database resource is bound."
        )

    # The Postgres host has the form <prefix>.database.<region>.azuredatabricks.net.
    # Lakebase tokens are scoped per-instance, identified by name. We can either
    # accept the instance name from env (set by us in app.yaml in the future) or
    # cheaply call list_database_instances() once and pick the one matching
    # PGHOST. Simpler: rely on PGAPPNAME — Databricks Apps inject the instance
    # name there. Falls back to the env override DATABRICKS_DATABASE_INSTANCE_NAME.
    instance_name = (
        os.environ.get("DATABRICKS_DATABASE_INSTANCE_NAME")
        or os.environ.get("PGAPPNAME")
        or ""
    )

    def _mint_token() -> str:
        # Imported lazily so local-dev paths that never touch Lakebase don't
        # require databricks-sdk at import time.
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()
        # Lakebase requires an instance-scoped credential, NOT a workspace token.
        # https://docs.databricks.com/api/workspace/database/generatedatabasecredential
        names = [instance_name] if instance_name else []
        if not names:
            # Last resort: discover from the host. Lakebase hostnames don't
            # encode the instance name, so we list and match by host.
            for inst in w.database.list_database_instances():
                if (inst.read_write_dns or "").lower() == (pg_host or "").lower():
                    names = [inst.name]
                    break
        if not names:
            raise RuntimeError(
                "Could not determine Lakebase instance name. Set "
                "DATABRICKS_DATABASE_INSTANCE_NAME in app.yaml."
            )
        cred = w.database.generate_database_credential(instance_names=names)
        token = getattr(cred, "token", None)
        if not token:
            raise RuntimeError("generate_database_credential returned no token")
        return token

    server_settings: dict[str, str] = {"application_name": "velocia-newop-sdc"}
    if settings.db_schema:
        # Defense-in-depth: even raw `text(...)` queries that don't qualify a
        # schema land in `velocia` instead of `public`.
        server_settings["search_path"] = settings.db_schema

    connect_args: dict[str, object] = {
        "user": pg_user,
        "password": _mint_token,  # asyncpg accepts a callable; invoked per connect
        "ssl": "require",
        "server_settings": server_settings,
    }
    if pg_db:
        connect_args["database"] = pg_db

    logger.info(
        "Lakebase engine configured: host=%s db=%s user=%s (token minted per-connect)",
        pg_host,
        pg_db,
        pg_user,
    )

    return sanitized, {
        "echo": False,
        "future": True,
        "connect_args": connect_args,
        "pool_pre_ping": True,
        "pool_recycle": _LAKEBASE_TOKEN_RECYCLE_SECONDS,
    }


_url, _engine_kwargs = _build_engine_kwargs(settings.database_url)
engine = create_async_engine(_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create the app's schema (if any) and all tables. Idempotent.

    Called once at app startup from `backend.main.lifespan`. Safe to invoke
    repeatedly — `CREATE SCHEMA IF NOT EXISTS` and `create_all` are both
    no-ops when the objects already exist.

    On Lakebase: `CREATE SCHEMA IF NOT EXISTS <schema> AUTHORIZATION
    CURRENT_USER` makes the app's service principal the schema owner, so
    every subsequent `CREATE TABLE` succeeds without any external GRANT
    against `public`. The bundle's `CAN_CONNECT_AND_CREATE` resource
    permission gives the SP database-level CREATE, which is enough.
    """
    async with engine.begin() as conn:
        if settings.db_schema and engine.dialect.name == "postgresql":
            schema = settings.db_schema.replace('"', '""')
            await conn.execute(
                text(f'CREATE SCHEMA IF NOT EXISTS "{schema}" AUTHORIZATION CURRENT_USER')
            )
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
