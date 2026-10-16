"""Endpoint de clasificacion multiclase (OE3).

El contrato HTTP no cambio, pero ahora cada prediccion se persiste completa:
la imagen (deduplicada por hash), el modelo usado, la clase predicha y las
cuatro probabilidades (`prediction_scores`). El acceso a datos se delega en
`app.repositories`.
"""

from __future__ import annotations

import hashlib
import logging
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_inference_service
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories import catalog as catalog_repo
from app.repositories import predictions as predictions_repo
from app.schemas.prediction import PredictionResponse
from app.services.inference import InferenceService
from app.utils.image import load_rgb_image, read_image_meta
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
    client: str | None = Form(default=None, description="Origen de la peticion (flutter, web)"),
    db: Session = Depends(get_db),
    service: InferenceService = Depends(get_inference_service),
    settings: Settings = Depends(get_settings),
    current_user: User | None = Depends(get_current_user_optional),
) -> PredictionResponse:
    raw = await file.read()

    try:
        ensure_valid_image(raw, settings.max_upload_bytes)
    except InvalidImageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    try:
        image = load_rgb_image(raw, settings.image_size)
        width, height, image_format = read_image_meta(raw)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="No se pudo procesar la imagen") from exc

    started = time.perf_counter()
    result = service.predict(image)
    inference_ms = (time.perf_counter() - started) * 1000.0

    # Persistencia enriquecida: imagen (dedup) + modelo + clase + probabilidades.
    db_image = catalog_repo.get_or_create_image(
        db,
        sha256=hashlib.sha256(raw).hexdigest(),
        width=width,
        height=height,
        image_format=image_format,
        size_bytes=len(raw),
    )

    model = catalog_repo.get_model_by_version(db, settings.model_version)
    if model is None:
        model = catalog_repo.ensure_model(
            db,
            name=settings.model_version.rsplit("-v", 1)[0],
            version=settings.model_version,
            architecture=service.architecture,
        )

    classes_by_code = catalog_repo.map_classes_by_code(db)
    predicted_class = classes_by_code.get(result["label"])
    if predicted_class is None:
        raise HTTPException(
            status_code=500, detail=f"Clase desconocida en el catalogo: {result['label']}"
        )

    scores = [
        (classes_by_code[code], probability)
        for code, probability in result["probabilities"].items()
        if code in classes_by_code
    ]

    predictions_repo.create_prediction(
        db,
        image=db_image,
        model=model,
        predicted_class=predicted_class,
        confidence=result["confidence"],
        inference_ms=inference_ms,
        gradcam_path=result.get("gradcam_path"),
        scores=scores,
        user_id=current_user.id if current_user else None,
        source=(client or "api")[:16],
    )

    return PredictionResponse(
        label=result["label"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        gradcam_path=result.get("gradcam_path"),
        model_version=model.version,
        inference_ms=inference_ms,
    )
