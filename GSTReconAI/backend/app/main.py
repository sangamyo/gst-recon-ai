"""FastAPI entry-point for GSTRecon AI."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routes import clients, reconciliation, uploads, users
from app.utils.logger import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    logger.info(
        "Starting {} (env={}, task_mode={})",
        settings.project_name,
        settings.env,
        "celery" if settings.use_celery else "in-process",
    )
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    # Auth uses a Bearer token header (not cookies), so credentials are not needed.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(clients.router, prefix=settings.api_v1_prefix)
app.include_router(uploads.router, prefix=settings.api_v1_prefix)
app.include_router(reconciliation.router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["system"])
def root():
    return {"name": settings.project_name, "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["system"])
def healthcheck():
    return {"status": "ok", "task_mode": "celery" if settings.use_celery else "in-process"}


if __name__ == "__main__":  # pragma: no cover - convenience for `python -m app.main`
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
