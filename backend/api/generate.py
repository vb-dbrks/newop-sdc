from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["generate"])


@router.post("/generate")
async def start_generate(payload: dict):
    """Start a generation run. Returns { study_id, document_id, agent_run_id }."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
