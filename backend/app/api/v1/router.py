"""Router de la version 1 de la API."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    catalog,
    health,
    history,
    predict,
    predictions,
    stats,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(predict.router)
api_router.include_router(predictions.router)
api_router.include_router(history.router)
api_router.include_router(catalog.router)
api_router.include_router(stats.router)
api_router.include_router(auth.router)
