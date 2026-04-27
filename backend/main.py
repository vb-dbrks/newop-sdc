import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import log_filter
from backend.api import (
    agent_runs,
    documents,
    exports,
    fields,
    generate,
    notifications,
    reviews,
    studies,
    threads,
    uploads,
)
from backend.api.me import router as me_router
from backend.db.seed import seed_default
from backend.db.session import SessionLocal, init_db
from backend.middleware.idempotency import IdempotencyMiddleware
from backend.middleware.security_headers import SecurityHeadersMiddleware
from backend.settings import settings

logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_filter.install()
    await init_db()
    if settings.seed_on_startup and settings.seed_user_email:
        try:
            async with SessionLocal() as session:
                await seed_default(
                    session,
                    user_email=settings.seed_user_email,
                    user_name=settings.seed_user_name or settings.seed_user_email,
                )
        except Exception:  # seed must never block app startup
            logger.exception(
                "Seed-on-startup failed; app will start anyway. "
                "Inspect logs and re-run scripts/seed_dev.py if needed."
            )
    yield


app = FastAPI(title="Velocia App", version="0.1.0", lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(IdempotencyMiddleware)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


api_routers = [
    me_router,
    studies.router,
    documents.router,
    fields.router,
    threads.router,
    reviews.router,
    generate.router,
    agent_runs.router,
    uploads.router,
    notifications.router,
    exports.router,
]
for r in api_routers:
    app.include_router(r, prefix="/api")


if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        index = FRONTEND_DIST / "index.html"
        if index.is_file():
            return FileResponse(index)
        return JSONResponse({"detail": "frontend not built; run `make build`"}, status_code=503)
