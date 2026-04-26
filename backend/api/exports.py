from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/documents", tags=["exports"])


@router.get("/{document_id}/export.docx")
async def export_docx(document_id: str):
    """Render the document snapshot to a .docx via python-docx."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
