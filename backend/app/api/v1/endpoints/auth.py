"""Autenticacion en modo mock (camino opcional).

La clasificacion **no** requiere cuenta. Estas rutas existen para que la
pantalla "Cuenta" del frontend consuma endpoints reales de punta a punta
mientras no haya un servicio de identidad definitivo.

Reglas del mock:

- Los usuarios viven en memoria (se pierden al reiniciar el proceso) y las
  contrasenas se guardan como hash SHA-256, nunca en claro.
- El token es determinista a partir del correo, de modo que las pruebas no son
  intermitentes.
- No emite JWT ni valida firma: es un marcador de posicion sustituible por la
  implementacion real sin cambiar el contrato HTTP.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])

# email -> (nombre, hash de la contrasena)
_USERS: dict[str, tuple[str, str]] = {}


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _token_for(email: str) -> str:
    return "mock-" + hashlib.sha256(email.encode("utf-8")).hexdigest()[:24]


def _error(status_code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crea una cuenta (mock)",
)
def register(payload: RegisterRequest) -> AuthResponse:
    email = payload.email.strip().lower()
    if email in _USERS:
        raise _error(status.HTTP_409_CONFLICT, "El correo ya esta registrado")
    _USERS[email] = (payload.name.strip(), _hash(payload.password))
    return AuthResponse(
        access_token=_token_for(email),
        name=payload.name.strip(),
        email=email,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Inicia sesion (mock)",
)
def login(payload: LoginRequest) -> AuthResponse:
    email = payload.email.strip().lower()
    record = _USERS.get(email)
    if record is None or record[1] != _hash(payload.password):
        raise _error(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
    return AuthResponse(
        access_token=_token_for(email),
        name=record[0],
        email=email,
    )
