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
from backend.db.session import init_db
from backend.middleware.idempotency import IdempotencyMiddleware
from backend.middleware.security_headers import SecurityHeadersMiddleware

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_filter.install()
    await init_db()
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
