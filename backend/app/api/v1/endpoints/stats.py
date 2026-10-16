"""Estadisticas agregadas del uso (apoyo a la evaluacion del OE3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import predictions as predictions_repo
from app.schemas.prediction import StatsSummary

router = APIRouter(prefix="/stats", tags=["analytics"])


@router.get("/summary", response_model=StatsSummary, summary="Resumen agregado")
def summary(db: Session = Depends(get_db)) -> dict:
    """Conteo por clase, confianza media y latencia media de inferencia."""
    return predictions_repo.stats_summary(db)
