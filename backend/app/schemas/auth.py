"""Esquemas de autenticacion (camino opcional).

Contrato que consume `frontend/lib/data/services/auth_service.dart`. La
respuesta incluye siempre `access_token` y `name`, que son los dos campos que
lee el `AuthViewModel`. `access_token` ahora es un JWT real firmado (HS256).
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


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str
    email: str
    expires_in: int
    mock: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.abc123",
                "token_type": "bearer",
                "name": "Equipo UNMSM",
                "email": "equipo@unmsm.edu.pe",
                "expires_in": 604800,
                "mock": False,
            }
        }
    }


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    email: str
