from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["threads"])


@router.get("/documents/{document_id}/threads")
async def list_threads(document_id: str, status_: str | None = None):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/documents/{document_id}/threads")
async def open_thread(document_id: str, payload: dict):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/threads/{thread_id}/comments")
async def add_comment(thread_id: str, payload: dict):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/threads/{thread_id}:resolve")
async def resolve_thread(thread_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
