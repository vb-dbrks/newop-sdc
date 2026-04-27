"""StudyAccessList repository — per-document Author/Reviewer lookups."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.enums import StudyAccessRole
from backend.domain.models import StudyAccessList


async def get_active_role(
    db: AsyncSession, *, study_document_id: str, user_id: str
) -> StudyAccessRole | None:
    """Return the highest active role this user holds on this document, or None.

    Author beats Reviewer when both are present.
    """
    rows = (
        await db.execute(
            select(StudyAccessList).where(
                StudyAccessList.study_document_id == study_document_id,
                StudyAccessList.user_id == user_id,
                StudyAccessList.is_active.is_(True),
            )
        )
    ).scalars().all()
    if not rows:
        return None
    roles = {row.role for row in rows}
    if StudyAccessRole.AUTHOR in roles:
        return StudyAccessRole.AUTHOR
    if StudyAccessRole.REVIEWER in roles:
        return StudyAccessRole.REVIEWER
    return None
