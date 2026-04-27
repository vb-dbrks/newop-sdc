"""Per-study role guards.

`require_role_on(*allowed)` returns a FastAPI dependency that:
  1. Resolves the current user (DB-backed via `current_user_row`).
  2. Looks up `study_access_list` for `(study_document_id, user_id)`.
  3. Rejects with 404 (not 403 — we don't leak doc existence) if the user
     has no active row, or has a role not in `allowed`.

See ADR 0019 (three-layer auth) and ADR 0008 (per-study role assignment).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.sso import current_user_row
from backend.db.repositories import access_list as access_list_repo
from backend.db.session import get_session
from backend.domain.enums import StudyAccessRole
from backend.domain.models import User


def require_role_on(*allowed: StudyAccessRole):
    """FastAPI dependency factory: caller must have one of `allowed` roles."""

    async def _check(
        study_document_id: str,
        user: Annotated[User, Depends(current_user_row)],
        db: Annotated[AsyncSession, Depends(get_session)],
    ) -> StudyAccessRole:
        role = await access_list_repo.get_active_role(
            db, study_document_id=study_document_id, user_id=user.user_id
        )
        if role is None or role not in allowed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return role

    return Depends(_check)


# Convenience wrappers for the common cases.
require_author = require_role_on(StudyAccessRole.AUTHOR)
require_member = require_role_on(StudyAccessRole.AUTHOR, StudyAccessRole.REVIEWER)
require_reviewer = require_role_on(StudyAccessRole.REVIEWER)
