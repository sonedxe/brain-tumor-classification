"""Catalogo de clases (las cuatro etiquetas del modelo).

Antes la etiqueta se guardaba como texto suelto en cada prediccion; ahora vive
en una tabla propia y las predicciones la referencian por FK. Esto evita que un
typo ("meningiomaa") rompa las estadisticas y permite colgar metadatos de cada
clase (nombre visible, si es tumor y su descripcion).

Las cuatro filas se siembran desde `ml/configs/labels.json`, que sigue siendo la
fuente unica de verdad compartida con el entrenamiento.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LesionClass(Base):
    __tablename__ = "lesion_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(64))
    index: Mapped[int] = mapped_column(Integer)  # posicion en la salida del modelo
    is_tumor: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuracion
        return f"LesionClass(code={self.code!r}, index={self.index})"
