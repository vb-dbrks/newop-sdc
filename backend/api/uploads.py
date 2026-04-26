from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("")
async def upload(
    file: UploadFile = File(...),
    study_id: str = Form(...),
    document_id: str | None = Form(None),
):
    """Stream the multipart body through files.upload() to a Volume path.

    Computes sha256 in flight, verifies via files.get_metadata(), persists file_uploads.
    See ADR 0010 and design-specs/architecture/07-sequence-file-upload.md.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{upload_id}")
async def get_upload(upload_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
