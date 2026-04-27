"""Tests for backend.db.seed — single- and multi-user paths, idempotency."""

from __future__ import annotations

from sqlalchemy import select

from backend.db.seed import seed_default, seed_users
from backend.db.session import SessionLocal
from backend.domain.enums import StudyAccessRole
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


async def test_seed_users_multi_user_with_roles():
    """Two users sharing all 5 studies, each with a different role."""
    async with SessionLocal() as session:
        counts = await seed_users(
            session,
            users=[
                {"email": "alice@x.com", "name": "Alice", "role": "author"},
                {"email": "bob@x.com", "name": "Bob", "role": "reviewer"},
            ],
        )
    assert counts == {"users": 2, "study_documents": 5, "study_access_list": 10}

    async with SessionLocal() as session:
        grants = (await session.execute(select(StudyAccessList))).scalars().all()
        users = {u.email: u for u in (await session.execute(select(User))).scalars()}

    alice_grants = [g for g in grants if g.user_id == users["alice@x.com"].user_id]
    bob_grants = [g for g in grants if g.user_id == users["bob@x.com"].user_id]
    assert {g.role for g in alice_grants} == {StudyAccessRole.AUTHOR}
    assert {g.role for g in bob_grants} == {StudyAccessRole.REVIEWER}
    assert len(alice_grants) == 5
    assert len(bob_grants) == 5


async def test_seed_users_scoped_studies():
    """Carol gets access to only 2 of the 5 studies."""
    async with SessionLocal() as session:
        counts = await seed_users(
            session,
            users=[
                {"email": "alice@x.com", "name": "Alice", "role": "author"},
                {
                    "email": "carol@x.com",
                    "name": "Carol",
                    "role": "author",
                    "studies": ["D9999C00001", "D9999C00002"],
                },
            ],
        )
    # 2 users + 5 studies + (5 alice + 2 carol) grants = 7
    assert counts == {"users": 2, "study_documents": 5, "study_access_list": 7}

    async with SessionLocal() as session:
        carol = (
            await session.execute(select(User).where(User.email == "carol@x.com"))
        ).scalar_one()
        carol_grants = (
            await session.execute(
                select(StudyAccessList).where(StudyAccessList.user_id == carol.user_id)
            )
        ).scalars().all()
        carol_studies = {
            (
                await session.execute(
                    select(StudyDocument).where(
                        StudyDocument.study_document_id == g.study_document_id
                    )
                )
            ).scalar_one().study_id
            for g in carol_grants
        }
    assert carol_studies == {"D9999C00001", "D9999C00002"}


async def test_seed_users_idempotent():
    spec = [
        {"email": "alice@x.com", "name": "Alice", "role": "author"},
        {"email": "bob@x.com", "name": "Bob", "role": "reviewer"},
    ]
    async with SessionLocal() as session:
        await seed_users(session, users=spec)
    async with SessionLocal() as session:
        counts = await seed_users(session, users=spec)
    assert counts == {"users": 0, "study_documents": 0, "study_access_list": 0}
