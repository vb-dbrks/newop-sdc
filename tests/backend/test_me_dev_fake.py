import pytest

from backend.cache import app_cache
from backend.settings import settings


@pytest.fixture
async def fake_user(monkeypatch):
    monkeypatch.setattr(settings, "dev_fake_user_email", "tester@example.az")
    monkeypatch.setattr(settings, "dev_fake_user_name", "Test User")
    # Cached user-row lookups would persist across tests otherwise.
    await app_cache.invalidate("auth:user_row:tester@example.az")
    yield


async def test_me_with_dev_fake_user(client, fake_user):
    r = await client.get("/api/me")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "tester@example.az"
    assert body["name"] == "Test User"
    assert "user_id" in body
    assert "onboarded_at" in body


async def test_me_repeat_returns_same_user_id(client, fake_user):
    first = (await client.get("/api/me")).json()
    # Bust the 30s cache so we hit the DB again.
    await app_cache.invalidate("auth:user_row:tester@example.az")
    second = (await client.get("/api/me")).json()
    assert first["user_id"] == second["user_id"]


async def test_me_without_auth_returns_401(client, monkeypatch):
    monkeypatch.setattr(settings, "dev_fake_user_email", None)
    monkeypatch.setattr(settings, "dev_fake_user_name", None)
    r = await client.get("/api/me")
    assert r.status_code == 401
