"""Capa de seguridad clinica (triaje por confianza y margen).

Convierte la salida probabilistica del modelo en una recomendacion de uso
clinico. **No es un diagnostico**: es una salvaguarda que obliga a derivar a
un especialista cuando el modelo no es concluyente, y que distingue el riesgo
de un hallazgo tumoral confirmado del de un estudio sin hallazgos.

Decisiones de diseno (justificadas para la sustentacion):

1. **Umbral de confianza** (`confidence_threshold`, por defecto 0.70): por
   debajo, el resultado se marca como *no concluyente* en lugar de forzar una
   clase. Evita que el usuario interprete una probabilidad marginal como un
   diagnostico.
2. **Margen top-1 / top-2** (`margin_threshold`, por defecto 0.10): si las dos
   clases mas probables estan casi empatadas, el modelo no discrimina bien
   aunque la confianza absoluta sea alta. Es una segunda senal de seguridad.
3. **Riesgo por clase**: un hallazgo tumoral concluyente es de riesgo alto si
   la confianza es muy alta (>= 0.90) y medio si es moderada; un estudio sin
   tumor es de riesgo bajo. En todos los casos la recomendacion remite a un
   especialista, porque la app es una herramienta de apoyo.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

NO_TUMOR_CLASS = "no_tumor"

DEFAULT_CONFIDENCE_THRESHOLD = 0.70
DEFAULT_MARGIN_THRESHOLD = 0.10
DEFAULT_HIGH_CONFIDENCE_THRESHOLD = 0.90

TRIAGE_LOW = "bajo"
TRIAGE_MEDIUM = "medio"
TRIAGE_HIGH = "alto"
TRIAGE_INCONCLUSIVE = "no_concluyente"

RECOMMENDATION_INCONCLUSIVE = (
    "Resultado no concluyente: la confianza o el margen entre clases es "
    "insuficiente. No uses este resultado para decidir; repite el estudio o "
    "consulta a un especialista en radiologia."
)

RECOMMENDATION_NO_TUMOR = (
    "No se detecto un hallazgo tumoral con confianza suficiente. Aun asi, la "
    "lectura de un especialista en radiologia sigue siendo la referencia."
)

RECOMMENDATION_MEDIUM = (
    "Posible hallazgo tumoral. Se recomienda revision por un especialista en "
    "radiologia o neurocirugia antes de cualquier decision clinica."
)

RECOMMENDATION_HIGH = (
    "Hallazgo tumoral con alta confianza. Deriva a un especialista en "
    "radiologia o neurocirugia para confirmacion diagnostica."
)


@dataclass(frozen=True)
class ClinicalAssessment:
    """Resultado de la capa de seguridad para una prediccion."""

    is_conclusive: bool
    triage_level: str
    recommendation: str
    confidence_threshold: float
    top_two_margin: float


def _top_two_margin(
    confidence: float, probabilities: Mapping[str, float] | None
) -> float:
    values = sorted((probabilities or {}).values(), reverse=True)
    top1 = values[0] if values else confidence
    top2 = values[1] if len(values) > 1 else 0.0
    return max(0.0, float(top1) - float(top2))


def assess(
    label: str,
    confidence: float,
    probabilities: Mapping[str, float] | None = None,
    *,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
    high_confidence_threshold: float = DEFAULT_HIGH_CONFIDENCE_THRESHOLD,
) -> ClinicalAssessment:
    """Evalua una prediccion y devuelve el nivel de triaje recomendado.

    Args:
        label: clase predicha (`glioma`, `meningioma`, `pituitario`, `no_tumor`).
        confidence: probabilidad de la clase predicha (0-1).
        probabilities: distribucion completa (opcional; si falta se usa
            `confidence` como top-1).
        confidence_threshold: confianza minima para considerar el resultado
            concluyente.
        margin_threshold: separacion minima entre la clase top-1 y la top-2.
        high_confidence_threshold: confianza a partir de la cual un hallazgo
            tumoral se clasifica como riesgo alto.
    """

    margin = _top_two_margin(confidence, probabilities)
    conclusive = (
        confidence >= confidence_threshold and margin >= margin_threshold
    )

    if not conclusive:
        return ClinicalAssessment(
            is_conclusive=False,
            triage_level=TRIAGE_INCONCLUSIVE,
            recommendation=RECOMMENDATION_INCONCLUSIVE,
            confidence_threshold=confidence_threshold,
            top_two_margin=margin,
        )

    if label == NO_TUMOR_CLASS:
        return ClinicalAssessment(
            is_conclusive=True,
            triage_level=TRIAGE_LOW,
            recommendation=RECOMMENDATION_NO_TUMOR,
            confidence_threshold=confidence_threshold,
            top_two_margin=margin,
        )

    if confidence >= high_confidence_threshold:
        return ClinicalAssessment(
            is_conclusive=True,
            triage_level=TRIAGE_HIGH,
            recommendation=RECOMMENDATION_HIGH,
            confidence_threshold=confidence_threshold,
            top_two_margin=margin,
        )

    return ClinicalAssessment(
        is_conclusive=True,
        triage_level=TRIAGE_MEDIUM,
        recommendation=RECOMMENDATION_MEDIUM,
        confidence_threshold=confidence_threshold,
        top_two_margin=margin,
    )
