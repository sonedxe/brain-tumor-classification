"""Esquemas de autenticacion (camino opcional).

Contrato que consume `frontend/lib/data/services/auth_service.dart`. La
respuesta incluye siempre `access_token` y `name`, que son los dos campos que
lee el `AuthViewModel`. `access_token` es un JWT real firmado (HS256) y
`refresh_token` un token opaco que se guarda hasheado en `auth_sessions`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=8)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=8)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str
    email: str
    expires_in: int
    refresh_token: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.abc123",
                "token_type": "bearer",
                "name": "Equipo UNMSM",
                "email": "equipo@unmsm.edu.pe",
                "expires_in": 604800,
                "refresh_token": "2mR8...opaco...",
            }
        }
    }


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    email: str
    role: str = "user"
    is_active: bool = True
