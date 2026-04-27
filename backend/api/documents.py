"""Workflow + access endpoints on study_document."""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/study-documents", tags=["workflow"])


@router.post("/{study_document_id}:submit")
async def submit_document(study_document_id: str):
    """Author submits Draft → In Review. Snapshots reviewer pool into study_document_version."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{study_document_id}/access")
async def grant_access(study_document_id: str, payload: dict):
    """Author grants access. Body { user_id, role, expire_at? }."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.delete("/{study_document_id}/access/{user_id}/{role}")
async def revoke_access(study_document_id: str, user_id: str, role: str):
    """Soft-revoke (is_active=false). Applies to next submission, not current."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
