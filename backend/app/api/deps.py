"""Dependencias de la API."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.inference import InferenceService


@lru_cache
def get_inference_service() -> InferenceService:
    settings = get_settings()
    return InferenceService(
        model_path=settings.model_path,
        model_version=settings.model_version,
        enable_gradcam=settings.enable_gradcam,
        mock=settings.mock_inference,
    )


def get_app_settings() -> Settings:
    return get_settings()
