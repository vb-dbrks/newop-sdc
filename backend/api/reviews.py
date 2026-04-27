"""Reviewer decisions on study_document_version."""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/study-documents", tags=["reviews"])


@router.post("/{study_document_id}:approve")
async def approve(study_document_id: str):
    """Insert review_approval; if all reviewers in pool approved → flip study_status='approved'."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{study_document_id}:request-changes")
async def request_changes(study_document_id: str, payload: dict):
    """Insert review_approval (changes_requested) + comment; flip study_status='draft'."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
