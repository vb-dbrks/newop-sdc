from fastapi import APIRouter, Depends

from backend.auth.sso import CurrentUser, current_user

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(user: CurrentUser = Depends(current_user)) -> dict[str, str]:
    return {
        "sso_subject": user.sso_subject,
        "email": user.email,
        "display_name": user.display_name,
    }
