"""Pruebas del informe clinico en PDF."""

from __future__ import annotations

from app.db.session import SessionLocal
from app.models.prediction import Prediction


def _token(client, email):
    r = client.post(
        "/api/v1/auth/register",
        json={"name": "Dr. Prueba", "email": email, "password": "secreto123"},
    )
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _predict(client, token, image_bytes):
    client.post(
        "/api/v1/predict",
        files={"file": ("mri.png", image_bytes, "image/png")},
        headers=_auth(token),
    )
    return client.get("/api/v1/history").json()[0]["id"]


def test_owner_downloads_a_valid_pdf(client, sample_image_bytes):
    token = _token(client, "a@unmsm.edu.pe")
    pid = _predict(client, token, sample_image_bytes)

    r = client.get(f"/api/v1/predictions/{pid}/report.pdf", headers=_auth(token))

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert f"informe-{pid}.pdf" in r.headers["content-disposition"]
    assert r.content.startswith(b"%PDF")


def test_pdf_survives_missing_gradcam_file(client, sample_image_bytes):
    token = _token(client, "a@unmsm.edu.pe")
    pid = _predict(client, token, sample_image_bytes)
    with SessionLocal() as db:
        db.get(Prediction, pid).gradcam_path = "/static/gradcam/no-existe.png"
        db.commit()

    r = client.get(f"/api/v1/predictions/{pid}/report.pdf", headers=_auth(token))

    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")


def test_other_user_gets_403(client, sample_image_bytes):
    owner = _token(client, "a@unmsm.edu.pe")
    other = _token(client, "b@unmsm.edu.pe")
    pid = _predict(client, owner, sample_image_bytes)

    r = client.get(f"/api/v1/predictions/{pid}/report.pdf", headers=_auth(other))

    assert r.status_code == 403


def test_unknown_prediction_is_404(client):
    token = _token(client, "a@unmsm.edu.pe")

    r = client.get("/api/v1/predictions/9999/report.pdf", headers=_auth(token))

    assert r.status_code == 404


def test_requires_authentication(client):
    assert client.get("/api/v1/predictions/1/report.pdf").status_code in (401, 403)
