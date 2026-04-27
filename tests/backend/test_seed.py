"""Tests for backend.db.seed.seed_default — idempotency and counts."""

from __future__ import annotations

from sqlalchemy import select

from backend.db.seed import seed_default
from backend.db.session import SessionLocal
from backend.domain.models import StudyAccessList, StudyDocument, User


async def test_seed_default_inserts_expected_rows():
    async with SessionLocal() as session:
        counts = await seed_default(
            session, user_email="alice@example.com", user_name="Alice Test"
        )
    assert counts == {"users": 1, "study_documents": 5, "study_access_list": 5}

    async with SessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()
        docs = (await session.execute(select(StudyDocument))).scalars().all()
        grants = (await session.execute(select(StudyAccessList))).scalars().all()
    assert len(users) == 1
    assert users[0].email == "alice@example.com"
    assert users[0].name == "Alice Test"
    assert len(docs) == 5
    assert len(grants) == 5
    assert all(g.user_id == users[0].user_id for g in grants)


async def test_seed_default_is_idempotent():
    async with SessionLocal() as session:
        await seed_default(
            session, user_email="alice@example.com", user_name="Alice Test"
        )
    async with SessionLocal() as session:
        counts = await seed_default(
            session, user_email="alice@example.com", user_name="Alice Test"
        )
    # Second run inserts nothing.
    assert counts == {"users": 0, "study_documents": 0, "study_access_list": 0}

    async with SessionLocal() as session:
        docs = (await session.execute(select(StudyDocument))).scalars().all()
    assert len(docs) == 5


async def test_seed_default_refreshes_user_name():
    async with SessionLocal() as session:
        await seed_default(
            session, user_email="alice@example.com", user_name="Alice Test"
        )
    async with SessionLocal() as session:
        await seed_default(
            session, user_email="alice@example.com", user_name="Alice Renamed"
        )
    async with SessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.email == "alice@example.com"))
        ).scalar_one()
    assert user.name == "Alice Renamed"
