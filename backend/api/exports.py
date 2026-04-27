from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/study-documents", tags=["exports"])


@router.get("/{study_document_id}/export.docx")
async def export_docx(study_document_id: str):
    """Render the latest study_document_version snapshot to .docx via python-docx."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
