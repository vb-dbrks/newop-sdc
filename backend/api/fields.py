"""Field PATCH + history + enhance endpoints.

Field paths are dot-notated to match audit_log.field_name conventions
(e.g. `new_opportunity.primary_objective`, `sdc_milestone[milestone_id=...].target_date`).
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/study-documents", tags=["fields"])


@router.patch("/{study_document_id}/fields/{field_path:path}")
async def patch_field(study_document_id: str, field_path: str, payload: dict):
    """Update a body-table column (Author only). Inserts an audit_log row inside the same tx."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{study_document_id}/fields/{field_path:path}/history")
async def field_history(study_document_id: str, field_path: str):
    """Read audit_log filtered by (study_document_id, field_name)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{study_document_id}/fields/{field_path:path}:enhance")
async def enhance_field(study_document_id: str, field_path: str):
    """Trigger an enhance_field agent run for this field. Returns { agent_run_id }."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
