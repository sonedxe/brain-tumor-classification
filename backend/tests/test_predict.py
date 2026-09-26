"""Pruebas del endpoint de prediccion y del historial."""

from __future__ import annotations

import io

import pytest
from PIL import Image

VALID_CLASSES = {"glioma", "meningioma", "pituitario", "no_tumor"}


def _png(size: int = 256) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (size, size), color=(200, 40, 60)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_predict_returns_the_documented_contract(client, sample_image_bytes):
    response = client.post(
        "/api/v1/predict", files={"file": ("mri.png", sample_image_bytes, "image/png")}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["label"] in VALID_CLASSES
    assert 0.0 <= body["confidence"] <= 1.0
    assert set(body["probabilities"]) == VALID_CLASSES
    assert abs(sum(body["probabilities"].values()) - 1.0) < 1e-6
    assert body["inference_ms"] >= 0.0
    assert "model_version" in body
    assert "gradcam_path" in body


def test_predict_is_deterministic_in_mock_mode(client, sample_image_bytes):
    first = client.post(
        "/api/v1/predict", files={"file": ("a.png", sample_image_bytes, "image/png")}
    ).json()
    second = client.post(
        "/api/v1/predict", files={"file": ("b.png", sample_image_bytes, "image/png")}
    ).json()

    assert first["label"] == second["label"]
    assert first["probabilities"] == second["probabilities"]


def test_predict_creates_a_history_record(client, sample_image_bytes):
    client.post("/api/v1/predict", files={"file": ("mri.png", sample_image_bytes, "image/png")})

    response = client.get("/api/v1/history")

    assert response.status_code == 200
    records = response.json()
    assert len(records) == 1
    assert records[0]["label"] in VALID_CLASSES
    assert len(records[0]["image_hash"]) == 64


def test_history_never_stores_identifiable_data(client, sample_image_bytes):
    client.post(
        "/api/v1/predict",
        files={"file": ("paciente_juan_perez.png", sample_image_bytes, "image/png")},
    )

    body = client.get("/api/v1/history").text
    assert "paciente" not in body.lower()
    assert "juan" not in body.lower()


def test_rejects_a_file_that_is_not_an_image(client):
    response = client.post(
        "/api/v1/predict", files={"file": ("nota.txt", b"esto no es una imagen", "text/plain")}
    )

    assert response.status_code == 400


def test_rejects_an_empty_file(client):
    response = client.post("/api/v1/predict", files={"file": ("vacio.png", b"", "image/png")})

    assert response.status_code == 400


def test_rejects_a_too_small_image(client):
    response = client.post("/api/v1/predict", files={"file": ("p.png", _png(8), "image/png")})

    assert response.status_code == 400


def test_rejects_a_oversized_upload(client, settings):
    oversized = _png(256)
    payload = oversized * ((settings.max_upload_bytes // len(oversized)) + 2)

    response = client.post(
        "/api/v1/predict", files={"file": ("grande.png", payload, "image/png")}
    )

    assert response.status_code == 413


def test_requires_the_file_field(client):
    response = client.post("/api/v1/predict", data={})

    assert response.status_code == 422


@pytest.mark.parametrize("limit", [0, 101])
def test_history_limit_is_bounded(client, limit):
    response = client.get(f"/api/v1/history?limit={limit}")

    assert response.status_code == 422
