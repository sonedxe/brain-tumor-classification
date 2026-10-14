"""Pruebas del modulo de autenticacion (JWT real + usuarios en SQLite)."""

from __future__ import annotations

from sqlalchemy import select

from app.core.security import decode_token, verify_password
from app.db.session import SessionLocal
from app.models.user import User


def _register(client, email="equipo@unmsm.edu.pe", password="secreto123"):
    return client.post(
        "/api/v1/auth/register",
        json={"name": "Equipo UNMSM", "email": email, "password": password},
    )


def test_register_returns_the_token_contract(client):
    response = _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["name"] == "Equipo UNMSM"
    assert body["email"] == "equipo@unmsm.edu.pe"
    assert body["expires_in"] > 0
    # Un JWT tiene tres segmentos separados por punto.
    assert len(body["access_token"].split(".")) == 3


def test_registered_token_is_a_valid_jwt(client):
    token = _register(client).json()["access_token"]

    payload = decode_token(token)
    assert payload["email"] == "equipo@unmsm.edu.pe"
    assert int(payload["sub"]) > 0


def test_password_is_not_stored_in_clear(client):
    _register(client, password="secreto123")

    with SessionLocal() as db:
        user = db.execute(select(User)).scalar_one()
    assert user.password_hash != "secreto123"
    assert verify_password("secreto123", user.password_hash)
    assert not verify_password("otra-clave", user.password_hash)


def test_register_then_login_succeeds(client):
    _register(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "equipo@unmsm.edu.pe", "password": "secreto123"},
    )

    assert response.status_code == 200
    assert len(response.json()["access_token"].split(".")) == 3


def test_login_is_case_insensitive_on_email(client):
    _register(client, email="Equipo@UNMSM.edu.pe")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "equipo@unmsm.edu.pe", "password": "secreto123"},
    )

    assert response.status_code == 200


def test_login_with_wrong_password_fails(client):
    _register(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "equipo@unmsm.edu.pe", "password": "otra-clave"},
    )

    assert response.status_code == 401


def test_duplicate_email_is_rejected(client):
    _register(client)

    response = _register(client)

    assert response.status_code == 409


def test_short_password_is_rejected_by_schema(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "X", "email": "a@b.com", "password": "123"},
    )

    assert response.status_code == 422


def test_me_returns_the_authenticated_user(client):
    token = _register(client).json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "equipo@unmsm.edu.pe"
    assert body["name"] == "Equipo UNMSM"


def test_me_without_token_is_rejected(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code in (401, 403)


def test_me_with_invalid_token_is_rejected(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer no-es-un-token"}
    )

    assert response.status_code == 401


def test_openapi_documents_the_auth_contract(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
