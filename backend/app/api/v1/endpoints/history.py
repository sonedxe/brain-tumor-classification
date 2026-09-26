"""Historial de predicciones, sin datos identificables del paciente."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.prediction_log import PredictionLog
from app.schemas.prediction import PredictionLogRead

router = APIRouter(tags=["history"])


@router.get("/history", response_model=list[PredictionLogRead], summary="Ultimas predicciones")
def history(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[PredictionLog]:
    stmt = (
        select(PredictionLog)
        .order_by(PredictionLog.created_at.desc(), PredictionLog.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())
