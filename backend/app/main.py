"""Punto de entrada de la API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.deps import get_inference_service
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import init_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    service = get_inference_service()
    if service.is_ready:
        logger.info("Modelo %s listo", settings.model_version)
    else:
        try:
            service.load()
            logger.info("Modelo %s cargado", settings.model_version)
        except NotImplementedError:
            state = "mock" if settings.mock_inference else "no disponible"
            logger.warning("Pesos no cargados, inferencia en modo %s", state)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    summary="Clasificacion multiclase de tumores cerebrales en imagenes de MRI",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

settings.media_root.mkdir(parents=True, exist_ok=True)
app.mount(settings.static_url, StaticFiles(directory=settings.media_root), name="static")

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }
