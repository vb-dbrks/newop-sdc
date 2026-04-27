from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.db.session import engine, init_db
from backend.domain.models import Base
from backend.main import app


@pytest.fixture(autouse=True)
async def _fresh_schema():
    """Drop & recreate the schema before each test so they're isolated.

    We use SQLite in-memory by default (set via DATABASE_URL=sqlite+aiosqlite:///:memory:
    in pytest invocation) but file-based SQLite also works — we just nuke tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await init_db()
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
