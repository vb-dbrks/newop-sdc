from uuid import UUID

from fastapi import Depends, HTTPException, status

from backend.auth.sso import CurrentUser, current_user


def require_member(study_id: UUID, user: CurrentUser = Depends(current_user)) -> CurrentUser:
    """Caller must hold any role on this study; else 404 (don't leak existence)."""
    # TODO: check study_role_assignments
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def require_author(study_id: UUID, user: CurrentUser = Depends(current_user)) -> CurrentUser:
    """Caller must be Author on this study."""
    # TODO: check study_role_assignments role='author'
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def require_reviewer(study_id: UUID, user: CurrentUser = Depends(current_user)) -> CurrentUser:
    """Caller must be Reviewer on this study."""
    # TODO: check study_role_assignments role='reviewer'
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
