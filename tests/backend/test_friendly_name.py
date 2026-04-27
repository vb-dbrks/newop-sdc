"""Tests for friendly_name_from_email + the self-heal in get_or_create."""

from __future__ import annotations

import pytest

from backend.auth.sso import friendly_name_from_email
from backend.db.repositories import users as users_repo
from backend.db.session import SessionLocal


@pytest.mark.parametrize(
    "email,expected",
    [
        ("alice@customer.com", "Alice"),
        ("alice.smith@customer.com", "Alice Smith"),
        ("j.doe-2@x.co", "J Doe 2"),
        ("first_last@example.org", "First Last"),
        ("name+tag@example.org", "Name Tag"),
        ("UPPER.case@x.com", "Upper Case"),
    ],
)
def test_friendly_name_from_email(email: str, expected: str):
    assert friendly_name_from_email(email) == expected


async def test_get_or_create_self_heals_email_shaped_name():
    """A row originally bootstrapped with name=email gets upgraded
    on the next login when a non-email name is supplied."""
    async with SessionLocal() as session:
        # Simulate the old buggy bootstrap: name == email
        old = await users_repo.get_or_create_by_sso_subject(
            session,
            sso_subject="alice@customer.com",
            email="alice@customer.com",
            name="alice@customer.com",
        )
        assert old.name == "alice@customer.com"

    async with SessionLocal() as session:
        # Next login resolves a friendly name and the repo upgrades the row.
        refreshed = await users_repo.get_or_create_by_sso_subject(
            session,
            sso_subject="alice@customer.com",
            email="alice@customer.com",
            name="Alice Customer",
        )
        assert refreshed.name == "Alice Customer"


async def test_get_or_create_does_not_overwrite_friendly_name():
    """A seeded name (non-email) must not be clobbered if a later
    bootstrap somehow hands an email-shaped name."""
    async with SessionLocal() as session:
        await users_repo.get_or_create_by_sso_subject(
            session,
            sso_subject="alice@customer.com",
            email="alice@customer.com",
            name="Alice Author",
        )

    async with SessionLocal() as session:
        same = await users_repo.get_or_create_by_sso_subject(
            session,
            sso_subject="alice@customer.com",
            email="alice@customer.com",
            name="alice@customer.com",
        )
        assert same.name == "Alice Author"
