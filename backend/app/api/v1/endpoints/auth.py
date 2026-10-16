"""Autenticacion real (camino opcional).

La clasificacion **no** requiere cuenta. Estas rutas existen para que la
pantalla "Cuenta" del frontend consuma endpoints reales de punta a punta.

- Los usuarios se persisten en SQLite (`users`) y la contrasena se guarda como
  hash PBKDF2-HMAC-SHA256 con sal (`app.core.security`), nunca en claro.
- El acceso emite un **JWT** corto (HS256) y, ademas, una **sesion** con
  refresh token opaco que se guarda hasheado en `auth_sessions`. Asi se puede
  rotar y revocar de verdad (`/auth/refresh`, `/auth/logout`).
- `GET /auth/me` valida el token y devuelve el usuario autenticado.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models.auth_session import AuthSession
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _utcnow() -> datetime:
    """UTC sin zona: SQLite devuelve datetimes naive y hay que comparar igual."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _issue_session(db: Session, user: User) -> AuthResponse:
    """Emite un JWT de acceso y registra una sesion con refresh token."""
    settings = get_settings()
    token, expires_at = create_access_token(
        user.id, {"email": user.email, "name": user.name, "role": user.role}
    )
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

    refresh_token = new_refresh_token()
    db.add(
        AuthSession(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=_utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
    )
    db.commit()

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        name=user.name,
        email=user.email,
        expires_in=expires_in,
        refresh_token=refresh_token,
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crea una cuenta",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = _normalize_email(payload.email)
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El correo ya esta registrado"
        )

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_session(db, user)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Inicia sesion",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = _normalize_email(payload.email)
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="La cuenta esta desactivada"
        )
    return _issue_session(db, user)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Rota el refresh token y emite un nuevo JWT",
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AuthResponse:
    hashed = hash_refresh_token(payload.refresh_token)
    session = db.execute(
        select(AuthSession).where(AuthSession.refresh_token_hash == hashed)
    ).scalar_one_or_none()

    if session is None or session.revoked_at is not None or session.expires_at < _utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o expirado",
        )

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no disponible"
        )

    session.revoked_at = _utcnow()  # rotacion: el token anterior deja de servir
    db.commit()
    return _issue_session(db, user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoca la sesion (refresh token)",
)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> Response:
    hashed = hash_refresh_token(payload.refresh_token)
    session = db.execute(
        select(AuthSession).where(AuthSession.refresh_token_hash == hashed)
    ).scalar_one_or_none()
    if session is not None and session.revoked_at is None:
        session.revoked_at = _utcnow()
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead, summary="Usuario autenticado")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
