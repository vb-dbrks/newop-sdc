from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/studies", tags=["studies"])


@router.get("")
async def list_studies(type: str | None = None, status_: str | None = None, q: str | None = None):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("")
async def create_study(payload: dict):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{study_id}")
async def get_study(study_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{study_id}/documents")
async def list_documents(study_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
