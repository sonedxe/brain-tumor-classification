"""Dependencias de la API."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.services.inference import InferenceService

bearer_scheme = HTTPBearer(auto_error=True)
optional_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_inference_service() -> InferenceService:
    settings = get_settings()
    return InferenceService(
        model_path=settings.model_path,
        model_version=settings.model_version,
        enable_gradcam=settings.enable_gradcam,
    )


def get_app_settings() -> Settings:
    return get_settings()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Valida el JWT del encabezado Authorization y devuelve el usuario."""
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Como `get_current_user`, pero devuelve None si no hay token valido.

    Se usa en rutas publicas que se enriquecen si el usuario esta autenticado
    (por ejemplo, registrar quien revisa una prediccion sin exigir cuenta).
    """
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        return None

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        return None
    return user
