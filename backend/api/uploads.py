"""File uploads → source_document.

See ADR 0010 and 07-sequence-file-upload.md. Stream multipart body through
files.upload() into the Volume; verify via files.get_metadata(); persist a
source_document row.
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("")
async def upload(
    file: Annotated[UploadFile, File(...)],
    study_document_id: Annotated[str, Form(...)],
):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{document_id}")
async def get_upload(document_id: str):
    """Returns source_document row including ingestion_status."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
