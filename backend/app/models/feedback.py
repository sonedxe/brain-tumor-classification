"""Validacion humana de una prediccion (patron *human-in-the-loop*).

Como la herramienta es de apoyo y no un dispositivo medico, registrar la
revision de un especialista permite medir la utilidad real del modelo y, en el
futuro, alimentar un ciclo de reentrenamiento con los casos dudosos.

No guarda datos del paciente: solo el veredicto sobre la prediccion (correcta o
no), la clase corregida si aplica y un comentario libre.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PredictionFeedback(Base):
    __tablename__ = "prediction_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("predictions.id"), index=True
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    is_correct: Mapped[bool] = mapped_column(Boolean)
    corrected_class_id: Mapped[int | None] = mapped_column(
        ForeignKey("lesion_classes.id"), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prediction: Mapped["Prediction"] = relationship(back_populates="feedback")  # noqa: F821
    corrected_class: Mapped["LesionClass | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuracion
        return f"PredictionFeedback(prediction_id={self.prediction_id}, ok={self.is_correct})"
