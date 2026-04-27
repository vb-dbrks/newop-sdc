from fastapi import APIRouter

from backend.auth.sso import CurrentUserRowDep
from backend.domain.schemas import MeResponse

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUserRowDep) -> MeResponse:
    return MeResponse.model_validate(user)
