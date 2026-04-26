from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/agent-runs", tags=["agent_runs"])


@router.get("/{agent_run_id}")
async def get_agent_run(agent_run_id: str):
    """Poll an agent run. Returns { status, step_history, error_message?, document_id? }."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
