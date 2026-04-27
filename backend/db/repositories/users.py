"""User repository — first-time SSO bootstrap + lookup."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.models import User


async def get_by_sso_subject(db: AsyncSession, sso_subject: str) -> User | None:
    return (
        await db.execute(select(User).where(User.sso_subject == sso_subject))
    ).scalar_one_or_none()


async def get_or_create_by_sso_subject(
    db: AsyncSession, *, sso_subject: str, email: str, name: str
) -> User:
    existing = await get_by_sso_subject(db, sso_subject)
    if existing is not None:
        # Self-heal: if the row was created by an older bootstrap that
        # stored the email as the display name, upgrade it to whatever
        # the current login resolved (typically the friendly-name-from-
        # email derivation in auth.sso). Never overwrites a non-email
        # name, so seeded display names ("Alice Author") are safe.
        if "@" in (existing.name or "") and "@" not in name:
            existing.name = name
            await db.commit()
            await db.refresh(existing)
        return existing
    user = User(sso_subject=sso_subject, email=email, name=name)
    db.add(user)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        # Concurrent creation — pick up the row inserted by the other request.
        existing = await get_by_sso_subject(db, sso_subject)
        if existing is not None:
            return existing
        raise
    await db.refresh(user)
    return user
