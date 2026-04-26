import pytest

from backend.settings import settings


@pytest.fixture
async def fake_user(monkeypatch):
    monkeypatch.setattr(settings, "dev_fake_user_email", "tester@example.az")
    monkeypatch.setattr(settings, "dev_fake_user_name", "Test User")


async def test_me_with_dev_fake_user(client, fake_user):
    r = await client.get("/api/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "tester@example.az"
    assert body["display_name"] == "Test User"


async def test_me_without_auth_returns_401(client, monkeypatch):
    monkeypatch.setattr(settings, "dev_fake_user_email", None)
    monkeypatch.setattr(settings, "dev_fake_user_name", None)
    r = await client.get("/api/me")
    assert r.status_code == 401
