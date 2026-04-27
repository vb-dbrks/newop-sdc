"""Portfolio + study_document read endpoints.

Schema: study_document is the umbrella; new_opportunity / study_design_concept /
study_protocol are body tables. See ADR 0018 and 02-data-model.md.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/study-documents", tags=["study-documents"])


@router.get("")
async def list_study_documents(
    document_type: str | None = None,
    study_status: str | None = None,
    q: str | None = None,
):
    """Portfolio table — rows from study_document with caller-visible filters."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{study_document_id}")
async def get_study_document(study_document_id: str):
    """Full document: umbrella + body row + sub-entities + open comment counts."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{study_document_id}/versions")
async def list_versions(study_document_id: str):
    """List study_document_version snapshots."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
