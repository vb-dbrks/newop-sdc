"""Authentication: parse Databricks Apps proxy headers → User.

Three deps available:
  - `current_user`        — lightweight CurrentUser dataclass (no DB lookup).
                            Use only when you don't need the User row.
  - `current_user_row`    — DB-backed User ORM object. Bootstraps a row on
                            first SSO login. Cached briefly per-subject.
  - `get_obo_ws` (in auth/obo.py) — `WorkspaceClient` acting as the user.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.cache import app_cache
from backend.db.repositories import users as users_repo
from backend.db.session import get_session
from backend.domain.models import User
from backend.settings import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurrentUser:
    sso_subject: str
    email: str
    display_name: str


_EMAIL_LOCAL_SEP = re.compile(r"[._\-+]")


def friendly_name_from_email(email: str) -> str:
    """Derive a human-readable display name from an email address.

    `alice.smith@customer.com` → `Alice Smith`.
    `j.doe-2@x.co`             → `J Doe 2`.

    Used when the SSO proxy doesn't carry a preferred-username header,
    so we never fall back to showing the raw email in the UI header.
    """
    local = email.split("@", 1)[0]
    parts = [p for p in _EMAIL_LOCAL_SEP.split(local) if p]
    if not parts:
        return email
    return " ".join(p.capitalize() for p in parts)


def _identity_from_headers(request: Request) -> CurrentUser | None:
    email = request.headers.get("X-Forwarded-Email")
    raw_name = (
        request.headers.get("X-Forwarded-Preferred-Username")
        or request.headers.get("X-Forwarded-User")
    )
    if not email:
        return None
    # Some proxies / IdPs send the email as the "preferred username" too.
    # In that case fall through to email-derived naming so the dashboard
    # doesn't say "Welcome, alice@customer.com".
    if raw_name and "@" not in raw_name:
        display = raw_name
    else:
        display = friendly_name_from_email(email)
    return CurrentUser(sso_subject=email, email=email, display_name=display)


def current_user(request: Request) -> CurrentUser:
    """Resolve identity from Databricks Apps SSO headers (no DB lookup).

    Local dev: falls back to `DEV_FAKE_USER_*` env vars when set.
    """
    identity = _identity_from_headers(request)
    if identity:
        # Note OBO header presence at debug, never the value.
        if request.headers.get("X-Forwarded-Access-Token"):
            logger.debug("OBO token header present for %s", identity.email)
        return identity

    if settings.dev_fake_user_email and settings.dev_fake_user_name:
        return CurrentUser(
            sso_subject=settings.dev_fake_user_email,
            email=settings.dev_fake_user_email,
            display_name=settings.dev_fake_user_name,
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@app_cache.cached("auth:user_row:{sso_subject}", ttl=30)
async def _bootstrap_user(
    sso_subject: str, email: str, name: str, db: AsyncSession
) -> User:
    return await users_repo.get_or_create_by_sso_subject(
        db, sso_subject=sso_subject, email=email, name=name
    )


async def current_user_row(
    user: Annotated[CurrentUser, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Return the DB-backed User row, bootstrapping on first SSO login.

    Cached for 30 sec per-subject to avoid hitting the DB on every request.
    """
    return await _bootstrap_user(user.sso_subject, user.email, user.display_name, db)


CurrentUserDep = Annotated[CurrentUser, Depends(current_user)]
CurrentUserRowDep = Annotated[User, Depends(current_user_row)]
