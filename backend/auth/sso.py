from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from backend.settings import settings


@dataclass(frozen=True)
class CurrentUser:
    sso_subject: str
    email: str
    display_name: str


def current_user(request: Request) -> CurrentUser:
    """Resolve the caller's identity from Databricks Apps SSO headers.

    In production, Databricks Apps injects signed identity headers on every request.
    For local dev, fall back to DEV_FAKE_USER_* env vars when explicitly set.
    """
    email = request.headers.get("X-Forwarded-Email")
    name = request.headers.get("X-Forwarded-Preferred-Username") or request.headers.get(
        "X-Forwarded-User"
    )

    if email and name:
        return CurrentUser(sso_subject=email, email=email, display_name=name)

    if settings.dev_fake_user_email and settings.dev_fake_user_name:
        return CurrentUser(
            sso_subject=settings.dev_fake_user_email,
            email=settings.dev_fake_user_email,
            display_name=settings.dev_fake_user_name,
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
