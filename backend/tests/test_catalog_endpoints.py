"""Pruebas de los endpoints nuevos: catalogos, detalle, feedback y estadisticas."""

from __future__ import annotations

import io

from PIL import Image


def _png(color=(90, 140, 200), size: int = 256) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (size, size), color=color).save(buffer, format="PNG")
    return buffer.getvalue()


def _predict(client, color=(90, 140, 200)) -> dict:
    response = client.post(
        "/api/v1/predict",
        files={"file": ("mri.png", _png(color), "image/png")},
        data={"client": "pytest"},
    )
    assert response.status_code == 201
    return response.json()


def test_models_catalog_registers_the_five_architectures(client):
    response = client.get("/api/v1/models")

    assert response.status_code == 200
    models = response.json()
    assert len(models) == 5
    names = {model["name"] for model in models}
    assert names == {
        "mobilenetv3",
        "efficientnetb0",
        "shufflenetv2",
        "densenet121",
        "resnet18",
    }
    assert all(model["accuracy"] is not None for model in models)
    assert any(model["is_active"] for model in models)


def test_classes_catalog_has_the_four_labels(client):
    response = client.get("/api/v1/classes")

    assert response.status_code == 200
    classes = response.json()
    assert [row["code"] for row in classes] == [
        "glioma",
        "meningioma",
        "pituitario",
        "no_tumor",
    ]
    assert classes[-1]["is_tumor"] is False


def test_prediction_detail_exposes_the_full_distribution(client):
    body = _predict(client)
    prediction_id = client.get("/api/v1/history").json()[0]["id"]

    response = client.get(f"/api/v1/predictions/{prediction_id}")

    assert response.status_code == 200
    detail = response.json()
    assert detail["predicted_class"]["code"] == body["label"]
    assert len(detail["scores"]) == 4
    assert set(detail["probabilities"]) == {
        "glioma",
        "meningioma",
        "pituitario",
        "no_tumor",
    }
    # La suma de las probabilidades persistidas debe dar 1.
    assert abs(sum(detail["probabilities"].values()) - 1.0) < 1e-6
    assert detail["image"]["width"] == 256
    assert detail["image"]["format"] == "PNG"


def test_prediction_detail_is_404_when_missing(client):
    assert client.get("/api/v1/predictions/9999").status_code == 404


def test_image_is_deduplicated_by_hash(client):
    _predict(client, color=(10, 20, 30))
    _predict(client, color=(10, 20, 30))  # misma imagen -> mismo hash

    summary = client.get("/api/v1/stats/summary").json()
    assert summary["total_predictions"] == 2
    assert summary["unique_images"] == 1


def test_feedback_is_recorded_and_can_correct_the_label(client):
    _predict(client)
    prediction_id = client.get("/api/v1/history").json()[0]["id"]

    response = client.post(
        f"/api/v1/predictions/{prediction_id}/feedback",
        json={"is_correct": False, "corrected_label": "glioma", "comment": "Revisado"},
    )

    assert response.status_code == 201
    feedback = response.json()
    assert feedback["is_correct"] is False
    assert feedback["corrected_class"]["code"] == "glioma"

    detail = client.get(f"/api/v1/predictions/{prediction_id}").json()
    assert len(detail["feedback"]) == 1


def test_feedback_rejects_an_unknown_label(client):
    _predict(client)
    prediction_id = client.get("/api/v1/history").json()[0]["id"]

    response = client.post(
        f"/api/v1/predictions/{prediction_id}/feedback",
        json={"is_correct": False, "corrected_label": "inventado"},
    )

    assert response.status_code == 422


def test_stats_summary_aggregates_by_class(client):
    _predict(client)

    summary = client.get("/api/v1/stats/summary").json()

    assert summary["total_predictions"] == 1
    assert summary["models_registered"] == 5
    assert summary["avg_confidence"] is not None
    assert sum(row["count"] for row in summary["by_class"]) == 1


def test_history_keeps_the_flat_contract(client):
    body = _predict(client)

    record = client.get("/api/v1/history").json()[0]

    assert record["label"] == body["label"]
    assert record["model_version"] == body["model_version"]
    assert len(record["image_hash"]) == 64
    assert record["source"] == "pytest"


def test_openapi_documents_the_new_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/models" in paths
    assert "/api/v1/classes" in paths
    assert "/api/v1/predictions/{prediction_id}" in paths
    assert "/api/v1/predictions/{prediction_id}/feedback" in paths
    assert "/api/v1/stats/summary" in paths
