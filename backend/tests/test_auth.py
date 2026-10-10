"""Pruebas del modulo de autenticacion mock."""

from __future__ import annotations

import pytest

from app.api.v1.endpoints import auth as auth_module


@pytest.fixture(autouse=True)
def clean_users():
    auth_module._USERS.clear()
    yield
    auth_module._USERS.clear()


def _register(client, email="equipo@unmsm.edu.pe", password="secreto123"):
    return client.post(
        "/api/v1/auth/register",
        json={"name": "Equipo UNMSM", "email": email, "password": password},
    )


def test_register_returns_the_token_contract(client):
    response = _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"].startswith("mock-")
    assert body["token_type"] == "bearer"
    assert body["name"] == "Equipo UNMSM"
    assert body["email"] == "equipo@unmsm.edu.pe"
    assert body["mock"] is True


def test_register_then_login_succeeds(client):
    _register(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "equipo@unmsm.edu.pe", "password": "secreto123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"].startswith("mock-")


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


def test_openapi_documents_the_auth_contract(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
