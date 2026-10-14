"""Autenticacion real (camino opcional).

La clasificacion **no** requiere cuenta. Estas rutas existen para que la
pantalla "Cuenta" del frontend consuma endpoints reales de punta a punta.

- Los usuarios se persisten en SQLite (`users`) y la contrasena se guarda como
  hash PBKDF2-HMAC-SHA256 con sal (`app.core.security`), nunca en claro.
- El acceso emite un **JWT** firmado (HS256) con expiracion configurable.
- `GET /auth/me` valida el token y devuelve el usuario autenticado.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _auth_response(user: User) -> AuthResponse:
    token, expires_at = create_access_token(
        user.id, {"email": user.email, "name": user.name}
    )
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        name=user.name,
        email=user.email,
        expires_in=expires_in,
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
    return _auth_response(user)


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
    return _auth_response(user)


@router.get("/me", response_model=UserRead, summary="Usuario autenticado")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
