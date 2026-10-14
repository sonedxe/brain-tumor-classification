"""Endpoint de salud, usado tambien como readiness check del modelo."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_inference_service
from app.core.constants import CLASSES
from app.core.config import get_settings
from app.schemas.prediction import HealthResponse
from app.services.inference import InferenceService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    response: Response,
    service: InferenceService = Depends(get_inference_service),
) -> HealthResponse:
    settings = get_settings()
    ready = service.is_ready

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        state = "model_not_loaded"
    else:
        state = "ok"

    return HealthResponse(
        status=state,
        model_ready=ready,
        model_version=settings.model_version,
        classes=list(CLASSES),
    )
