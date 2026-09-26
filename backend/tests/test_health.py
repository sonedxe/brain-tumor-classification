"""Pruebas del endpoint de salud."""

from __future__ import annotations


def test_root_exposes_service_metadata(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["docs"] == "/docs"
    assert body["health"] == "/api/v1/health"


def test_health_returns_the_four_classes(client):
    response = client.get("/api/v1/health")

    assert response.status_code in (200, 503)
    body = response.json()
    assert body["classes"] == ["glioma", "meningioma", "pituitario", "no_tumor"]
    assert isinstance(body["model_ready"], bool)


def test_health_reports_mock_mode_before_weights_exist(client):
    response = client.get("/api/v1/health")

    body = response.json()
    if not body["model_ready"]:
        assert body["status"] == "ok_mock"
    else:
        assert body["status"] == "ok"


def test_openapi_documents_the_predict_contract(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/predict" in response.json()["paths"]
