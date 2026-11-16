"""FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --port 8000

In production the built frontend (``frontend/dist``) is served by this same
process, so a single port is enough.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import db
from .config import get_settings
from .routers import auth, literature, meta, papers
from .security import hash_password
from .services.pipeline import job_manager, log_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
log = logging.getLogger("apa")

settings = get_settings()


def _bootstrap_admin() -> None:
    existing = db.fetch_one("SELECT id FROM users LIMIT 1")
    if existing:
        return
    if not settings.ADMIN_PASSWORD:
        log.warning(
            "No users exist yet and ADMIN_PASSWORD is not set - open /register to create the first account."
        )
        return
    import uuid

    db.execute(
        "INSERT INTO users (id, email, name, password_hash, role, created_at) VALUES (?,?,?,?,?,?)",
        (
            uuid.uuid4().hex,
            settings.ADMIN_EMAIL.lower(),
            settings.ADMIN_NAME,
            hash_password(settings.ADMIN_PASSWORD),
            "admin",
            db.utcnow(),
        ),
    )
    log.info("Bootstrapped administrator account %s", settings.ADMIN_EMAIL)


def _recover_interrupted_jobs() -> None:
    rows = db.fetch_all("SELECT id FROM papers WHERE status IN ('queued','running')")
    for row in rows:
        db.execute(
            "UPDATE papers SET status='failed', stage='failed', error=?, updated_at=? WHERE id=?",
            ("Generation was interrupted by a server restart. Click retry to run it again.", db.utcnow(), row["id"]),
        )
        log_event(row["id"], "failed", "Interrupted by server restart", level="error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    _bootstrap_admin()
    _recover_interrupted_jobs()
    log.info("Academic Paper Assistant %s started (env=%s)", settings.APP_VERSION, settings.ENV)
    yield
    await job_manager.shutdown()


app = FastAPI(
    title="Academic Paper Assistant API",
    version=settings.APP_VERSION,
    description="AI-assisted academic paper generation with real literature retrieval.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(papers.router)
app.include_router(literature.router)
app.include_router(meta.router)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):  # pragma: no cover
    log.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ---------------------------------------------------------------------------
# Static frontend (single-port deployment)
# ---------------------------------------------------------------------------

DIST = settings.FRONTEND_DIST
ASSETS = DIST / "assets"


@app.get("/assets/{path:path}", include_in_schema=False)
def static_assets(path: str):
    candidate = (ASSETS / path).resolve()
    if not str(candidate).startswith(str(ASSETS.resolve())) or not candidate.is_file():
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return FileResponse(candidate)


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    index = DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Frontend is not built. Run `cd frontend && npm install && npm run build`, "
            "or start the Vite dev server with `npm run dev`."
        },
    )
