"""Idempotency-Key middleware.

Pattern documented in `architecture/03-api-contracts.md`. State-changing
endpoints (POST/PATCH/DELETE under /api) honour an `Idempotency-Key` header.
On a hit, the prior 2xx response is replayed verbatim. On a miss, the
request is processed and the result cached.

Backed by the `idempotency_keys` table — `(key, user_id)` PK, JSONB body,
24h TTL (configurable via settings.idempotency_ttl_hours).
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.db.session import SessionLocal
from backend.domain.models import IdempotencyKey
from backend.settings import settings

_MUTATING_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method not in _MUTATING_METHODS or not request.url.path.startswith("/api"):
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)

        # Identity is established in route deps; we approximate "user_id" via
        # the proxy header so we don't need a DB lookup just to gate idempotency.
        user_id = request.headers.get("X-Forwarded-Email") or settings.dev_fake_user_email or ""
        if not user_id:
            return await call_next(request)

        ttl = timedelta(hours=settings.idempotency_ttl_hours)
        cutoff = datetime.now(UTC) - ttl

        async with SessionLocal() as db:
            existing = (
                await db.execute(
                    select(IdempotencyKey).where(
                        IdempotencyKey.key == key,
                        IdempotencyKey.user_id == user_id,
                        IdempotencyKey.created_at >= cutoff,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                return JSONResponse(
                    content=existing.response_body,
                    status_code=existing.response_status,
                    headers={"Idempotency-Replayed": "true"},
                )

        response = await call_next(request)

        # Only cache successful JSON responses.
        if 200 <= response.status_code < 300 and "application/json" in response.headers.get(
            "content-type", ""
        ):
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            try:
                parsed = json.loads(body) if body else {}
            except json.JSONDecodeError:
                parsed = {"raw": body.decode("utf-8", errors="replace")}
            async with SessionLocal() as db:
                db.add(
                    IdempotencyKey(
                        key=key,
                        user_id=user_id,
                        response_body=parsed,
                        response_status=response.status_code,
                    )
                )
                try:
                    await db.commit()
                except Exception:
                    await db.rollback()
            # Re-emit the body since we consumed the iterator above.
            return JSONResponse(
                content=parsed,
                status_code=response.status_code,
                headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
            )

        return response
