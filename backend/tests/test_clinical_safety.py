"""Pruebas de la capa de seguridad clinica (triaje por confianza y margen)."""

from __future__ import annotations

import pytest

from app.services.clinical_safety import (
    TRIAGE_HIGH,
    TRIAGE_INCONCLUSIVE,
    TRIAGE_LOW,
    TRIAGE_MEDIUM,
    assess,
)

FOUR_CLASSES = ("glioma", "meningioma", "pituitario", "no_tumor")


def _distribution(top_label: str, top: float) -> dict[str, float]:
    """Reparte el resto de probabilidad entre las otras tres clases."""
    rest = (1.0 - top) / (len(FOUR_CLASSES) - 1)
    return {name: (top if name == top_label else rest) for name in FOUR_CLASSES}


def test_no_tumor_concluyente_es_riesgo_bajo():
    result = assess("no_tumor", 0.95, _distribution("no_tumor", 0.95))

    assert result.is_conclusive is True
    assert result.triage_level == TRIAGE_LOW
    assert "radiologia" in result.recommendation


def test_tumor_con_alta_confianza_es_riesgo_alto():
    result = assess("glioma", 0.96, _distribution("glioma", 0.96))

    assert result.is_conclusive is True
    assert result.triage_level == TRIAGE_HIGH
    assert "Deriva" in result.recommendation


def test_tumor_con_confianza_moderada_es_riesgo_medio():
    result = assess("meningioma", 0.75, _distribution("meningioma", 0.75))

    assert result.is_conclusive is True
    assert result.triage_level == TRIAGE_MEDIUM
    assert "revision" in result.recommendation.lower()


def test_confianza_baja_es_no_concluyente():
    result = assess("pituitario", 0.45, _distribution("pituitario", 0.45))

    assert result.is_conclusive is False
    assert result.triage_level == TRIAGE_INCONCLUSIVE
    assert "no concluyente" in result.recommendation.lower()


def test_confianza_alta_pero_margen_insuficiente_es_no_concluyente():
    # 0.40 vs 0.38: la confianza absoluta no llega al umbral en este caso,
    # pero el margen es la senal que se quiere probar.
    probabilities = {"glioma": 0.40, "meningioma": 0.38, "pituitario": 0.12, "no_tumor": 0.10}
    result = assess(
        "glioma",
        0.40,
        probabilities,
        confidence_threshold=0.30,
        margin_threshold=0.10,
    )

    assert result.is_conclusive is False
    assert result.triage_level == TRIAGE_INCONCLUSIVE


def test_margen_se_expone_para_auditoria():
    probabilities = {"glioma": 0.90, "meningioma": 0.05, "pituitario": 0.03, "no_tumor": 0.02}
    result = assess("glioma", 0.90, probabilities)

    assert result.top_two_margin == pytest.approx(0.85)
    assert result.confidence_threshold == 0.70


def test_sin_distribucion_usa_la_confianza_como_margen():
    result = assess("glioma", 0.95)

    assert result.is_conclusive is True
    assert result.triage_level == TRIAGE_HIGH
    assert result.top_two_margin == pytest.approx(0.95)
