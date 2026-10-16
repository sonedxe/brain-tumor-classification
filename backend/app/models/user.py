"""Cuenta de usuario (autenticacion real, camino opcional).

La clasificacion no requiere cuenta. Se persiste lo minimo para autenticar:
correo, nombre, el hash de la contrasena (nunca en claro) y el rol. No se
guardan datos personales adicionales.

`is_active` implementa borrado logico: dar de baja una cuenta no borra sus
predicciones historicas, solo impide iniciar sesion.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuracion
        return f"User(id={self.id}, email={self.email!r}, role={self.role!r})"
