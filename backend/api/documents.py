from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}")
async def get_document(document_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{document_id}/history")
async def document_history(document_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{document_id}:submit")
async def submit_document(document_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{document_id}/reviewers")
async def assign_reviewer(document_id: str, payload: dict):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.delete("/{document_id}/reviewers/{user_id}")
async def remove_reviewer(document_id: str, user_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
