"""Registro de modelos (patron *registry*).

El proyecto compara cinco arquitecturas CNN. En vez de guardar el nombre del
modelo como texto en cada prediccion, se registra una vez por version y las
predicciones lo referencian. Asi se puede saber con que modelo se clasifico cada
imagen, cual esta activo y comparar metricas sin tocar las filas historicas.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    architecture: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    dataset: Mapped[str] = mapped_column(String(64), default="brain-tumor-mri")
    num_parameters_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    macro_f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    roc_auc: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuracion
        return f"MLModel(name={self.name!r}, version={self.version!r})"
