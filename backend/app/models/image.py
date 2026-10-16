"""Imagen subida, identificada por su hash SHA-256.

Normaliza el `image_hash` que antes se repetia en cada fila de prediccion: dos
predicciones de la misma imagen (por ejemplo con modelos distintos) comparten
una sola fila en `images`.

Solo se guardan metadatos tecnicos (ancho, alto, formato, bytes). No se guarda
el nombre del archivo, ni la fecha de nacimiento, ni los tags DICOM ni ningun
dato que permita reidentificar al paciente.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    format: Mapped[str] = mapped_column(String(16))
    size_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuracion
        return f"Image(sha256={self.sha256[:12]}..., {self.width}x{self.height})"
