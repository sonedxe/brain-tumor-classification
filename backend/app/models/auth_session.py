"""Sesion autenticada con *refresh token* (patron de sesiones).

El acceso sigue siendo un JWT de vida corta; la sesion guarda el *hash* del
refresh token (nunca el token en claro), su expiracion y el momento en que se
revoca. Asi se puede cerrar sesion de verdad y rotar el token sin invalidar el
resto de sesiones del usuario.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(128), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuracion
        return f"AuthSession(user_id={self.user_id}, revoked={self.revoked_at is not None})"
