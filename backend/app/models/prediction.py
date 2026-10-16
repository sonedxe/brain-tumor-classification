"""Prediccion (hecho principal) y sus puntajes por clase.

Es el nucleo del modelo de datos: relaciona una `image` con el `ml_model` que la
clasifico y con la `lesion_class` predicha. Antes de este cambio, la etiqueta y
la version del modelo eran texto suelto y el resto de la informacion (las cuatro
probabilidades) se calculaba y se descartaba.

`PredictionScore` guarda la distribucion completa de probabilidades (una fila por
clase), que es lo que permite auditar por que el modelo eligio una etiqueta.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"), index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id"), index=True)
    predicted_class_id: Mapped[int] = mapped_column(
        ForeignKey("lesion_classes.id"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    confidence: Mapped[float] = mapped_column(Float)
    inference_ms: Mapped[float] = mapped_column(Float)
    gradcam_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(16), default="api")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    image: Mapped["Image"] = relationship()  # noqa: F821
    model: Mapped["MLModel"] = relationship()  # noqa: F821
    predicted_class: Mapped["LesionClass"] = relationship()  # noqa: F821
    scores: Mapped[list["PredictionScore"]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["PredictionFeedback"]] = relationship(  # noqa: F821
        back_populates="prediction", cascade="all, delete-orphan"
    )

    # Propiedades de conveniencia: exponen los datos que el contrato HTTP
    # historico usaba con nombres planos (image_hash/label/model_version) sin
    # duplicar columnas en la tabla.
    @property
    def image_hash(self) -> str:
        return self.image.sha256

    @property
    def label(self) -> str:
        return self.predicted_class.code

    @property
    def model_version(self) -> str:
        return self.model.version

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuracion
        return f"Prediction(id={self.id}, confidence={self.confidence:.3f})"


class PredictionScore(Base):
    __tablename__ = "prediction_scores"
    __table_args__ = (
        UniqueConstraint("prediction_id", "class_id", name="uq_score_prediction_class"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("predictions.id"), index=True
    )
    class_id: Mapped[int] = mapped_column(ForeignKey("lesion_classes.id"), index=True)
    probability: Mapped[float] = mapped_column(Float)

    prediction: Mapped["Prediction"] = relationship(back_populates="scores")
    lesion_class: Mapped["LesionClass"] = relationship()  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuracion
        return f"PredictionScore(class_id={self.class_id}, p={self.probability:.3f})"
