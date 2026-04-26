from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/documents", tags=["reviews"])


@router.post("/{document_id}:approve")
async def approve(document_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{document_id}:request-changes")
async def request_changes(document_id: str, payload: dict):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
