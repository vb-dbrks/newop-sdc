"""Comments — review_comment + comment_audit_bridge per IA v2 (no separate threads table)."""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["comments"])


@router.get("/study-documents/{study_document_id}/comments")
async def list_comments(study_document_id: str, status_: str | None = None):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/study-documents/{study_document_id}/comments")
async def add_comment(study_document_id: str, payload: dict):
    """Insert review_comment + audit_log + comment_audit_bridge in one tx."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/comments/{comment_id}:resolve")
async def resolve_comment(comment_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
