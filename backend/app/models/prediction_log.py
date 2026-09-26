"""Registro de predicciones.

Por tratarse de datos medicos, no se persiste nada que permita identificar a
un paciente: ni nombre, ni fecha de nacimiento, ni los tags DICOM de la
imagen, ni el nombre original del archivo. Solo el hash SHA-256, que permite
detectar imagenes repetidas sin revelar contenido clinico.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_hash: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(64), index=True)
    inference_ms: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
