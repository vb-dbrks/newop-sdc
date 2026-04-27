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
