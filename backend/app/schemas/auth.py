"""Esquemas de autenticacion (camino opcional, modo mock).

Contrato que consume `frontend/lib/data/services/auth_service.dart`. La
respuesta incluye siempre `access_token` y `name`, que son los dos campos que
lee el `AuthViewModel`.
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
    mock: bool = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "mock-1f2a3b4c5d6e7f8091a2b3c4",
                "token_type": "bearer",
                "name": "Equipo UNMSM",
                "email": "equipo@unmsm.edu.pe",
                "mock": True,
            }
        }
    }
