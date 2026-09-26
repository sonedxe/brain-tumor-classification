"""Endpoint de clasificacion multiclase (OE3)."""

from __future__ import annotations

import hashlib
import logging
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_inference_service
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.prediction_log import PredictionLog
from app.schemas.prediction import PredictionResponse
from app.services.inference import InferenceService
from app.utils.image import load_rgb_image
from app.utils.validation import InvalidImageError, ensure_valid_image

logger = logging.getLogger(__name__)

router = APIRouter(tags=["predictions"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clasifica una imagen de resonancia magnetica",
)
async def predict(
    file: UploadFile = File(..., description="Imagen de MRI en JPEG, PNG, BMP, WEBP o TIFF"),
    db: Session = Depends(get_db),
    service: InferenceService = Depends(get_inference_service),
    settings: Settings = Depends(get_settings),
) -> PredictionResponse:
    raw = await file.read()

    try:
        ensure_valid_image(raw, settings.max_upload_bytes)
    except InvalidImageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    try:
        image = load_rgb_image(raw, settings.image_size)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="No se pudo procesar la imagen") from exc

    started = time.perf_counter()
    result = service.predict(image)
    inference_ms = (time.perf_counter() - started) * 1000.0

    image_hash = hashlib.sha256(raw).hexdigest()
    db.add(
        PredictionLog(
            image_hash=image_hash,
            label=result["label"],
            confidence=result["confidence"],
            model_version=settings.model_version,
            inference_ms=inference_ms,
        )
    )
    db.commit()

    return PredictionResponse(
        label=result["label"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        gradcam_path=result.get("gradcam_path"),
        model_version=settings.model_version,
        inference_ms=inference_ms,
    )
