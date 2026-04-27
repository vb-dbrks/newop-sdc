"""OBO (On-Behalf-Of) WorkspaceClient and SP WorkspaceClient dependencies.

Pattern from the DQX app: the Databricks Apps proxy injects the user's
access token in `X-Forwarded-Access-Token` on every request. We mint a
short-lived `WorkspaceClient` from that token so any Databricks API calls
the app makes on the user's behalf (Volume reads/writes, UC catalog
queries, etc.) inherit Unity Catalog's authorization automatically — see
ADR 0019 (three-layer auth model) and ADR 0020 (OBO token pattern).

For app-internal operations (Lakebase, agent endpoint), use `get_sp_ws()`
which returns a `WorkspaceClient` configured from the app's service
principal credentials (default Databricks SDK auth chain).
"""

from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import Header, HTTPException, status

from backend.cache import app_cache
from backend.settings import settings

try:
    from databricks.sdk import WorkspaceClient
except ImportError:  # databricks-sdk should be installed; this is a safety net
    WorkspaceClient = None  # type: ignore[assignment, misc]


_OBO_TTL = settings.obo_cache_ttl_seconds
_SP_TTL = settings.obo_cache_ttl_seconds


@app_cache.cached("auth:obo:{token_hash}", ttl=_OBO_TTL)
async def _create_obo_ws(token_hash: str, token: str):
    if WorkspaceClient is None:
        raise RuntimeError("databricks-sdk is not installed")
    return WorkspaceClient(token=token, auth_type="pat")


async def get_obo_ws(
    token: Annotated[str | None, Header(alias="X-Forwarded-Access-Token")] = None,
):
    """Return a `WorkspaceClient` acting as the calling user.

    Falls back to a 401 if no header is present (i.e., the request didn't
    come through the Databricks Apps proxy and no dev override was set).
    """
    if not token:
        # Local-dev override: if no proxy is in front of us and dev-fake user
        # is enabled, fall back to the SP client so the dev environment can
        # exercise upload paths without real OBO tokens.
        if settings.dev_fake_user_email:
            return await get_sp_ws()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Forwarded-Access-Token. The app must be reached via the Databricks Apps proxy.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return await _create_obo_ws(token_hash, token)


@app_cache.cached("auth:sp", ttl=_SP_TTL)
async def get_sp_ws():
    """Return a `WorkspaceClient` configured from the app's service principal.

    Uses the Databricks SDK default auth chain (env vars, ~/.databrickscfg,
    or the workspace runtime when deployed). Cached because each construction
    runs an SDK auth probe.
    """
    if WorkspaceClient is None:
        raise RuntimeError("databricks-sdk is not installed")
    return WorkspaceClient()
