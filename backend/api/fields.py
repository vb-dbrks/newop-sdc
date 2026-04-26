from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/documents", tags=["fields"])


@router.patch("/{document_id}/fields/{field_key}")
async def patch_field(document_id: str, field_key: str, payload: dict):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{document_id}/fields/{field_key}/history")
async def field_history(document_id: str, field_key: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{document_id}/fields/{field_key}:enhance")
async def enhance_field(document_id: str, field_key: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
