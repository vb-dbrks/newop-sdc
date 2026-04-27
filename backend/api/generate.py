from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["generate"])


@router.post("/generate")
async def start_generate(payload: dict):
    """Start a generation run.

    Body: { document_type, prompt, parent_opportunity_id?, attached_source_document_ids? }
    Returns: { study_document_id, agent_run_id }.
    SDC requires `parent_opportunity_id`.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
