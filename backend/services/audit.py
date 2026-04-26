"""Append-only audit log helper.

See ADR 0005. Always called inside the same transaction as the action it records,
so that audit and the action commit (or roll back) together.
"""

from uuid import UUID


async def record(
    *,
    actor_user_id: UUID | None,
    entity_type: str,
    entity_id: UUID,
    action: str,
    before: dict | None = None,
    after: dict | None = None,
    context: dict | None = None,
) -> None:
    raise NotImplementedError("TODO: INSERT INTO audit_log")
