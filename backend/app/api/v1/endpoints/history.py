"""Historial de predicciones, sin datos identificables del paciente.

El contrato de salida conserva los nombres planos de siempre (`image_hash`,
`label`, `model_version`), pero ahora se resuelven por relaciones hacia
`images`, `lesion_classes` y `ml_models`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import predictions as predictions_repo
from app.schemas.prediction import PredictionRead

router = APIRouter(tags=["history"])


@router.get("/history", response_model=list[PredictionRead], summary="Ultimas predicciones")
def history(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list:
    return predictions_repo.list_predictions(db, limit=limit, offset=offset)
