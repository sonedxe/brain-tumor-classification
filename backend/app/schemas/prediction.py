"""Esquemas de entrada y salida (contrato publico de la API)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "meningioma",
                "confidence": 0.97,
                "probabilities": {
                    "glioma": 0.01,
                    "meningioma": 0.97,
                    "pituitario": 0.01,
                    "no_tumor": 0.01,
                },
                "gradcam_path": "/static/gradcam/9f2a.png",
                "model_version": "mobilenetv3-v1",
                "inference_ms": 82.4,
            }
        }
    )

    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[str, float]
    gradcam_path: str | None = None
    model_version: str
    inference_ms: float = Field(ge=0.0)


class PredictionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_hash: str
    label: str
    confidence: float
    model_version: str
    inference_ms: float
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    model_ready: bool
    model_version: str
    classes: list[str]
