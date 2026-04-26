"""In-app notifier. Writes a row to `notifications` per recipient per event.

See ADR 0016. Email / Slack fan-out can be added later without changing the API.
"""

from uuid import UUID

from backend.domain.enums import NotificationKind


async def notify(
    *,
    recipient_user_id: UUID,
    kind: NotificationKind,
    title: str,
    body: str | None,
    deep_link: str,
    payload: dict | None = None,
) -> None:
    raise NotImplementedError("TODO: INSERT INTO notifications")
