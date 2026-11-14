"""Esquemas de entrada y salida (contrato publico de la API)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.config import get_settings
from app.schemas.catalog import ImageRead, LesionClassRead, MLModelRead
from app.schemas.feedback import FeedbackRead
from app.services.clinical_safety import ClinicalAssessment, assess


class PredictionResponse(BaseModel):
    """Contrato de `POST /predict` (sin cambios para el cliente Flutter)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "meningioma",
                "confidence": 0.97,
                "probabilities": {
                    "glioma": 0.01,
                    "meningioma": 0.97,
                    "pituitario": 0.01,
                    "no_tumor": 0.01,
                },
                "gradcam_path": "/static/gradcam/9f2a.png",
                "model_version": "mobilenetv3-v1",
                "inference_ms": 82.4,
                "is_conclusive": True,
                "triage_level": "alto",
                "recommendation": (
                    "Hallazgo tumoral con alta confianza. Deriva a un "
                    "especialista en radiologia o neurocirugia para "
                    "confirmacion diagnostica."
                ),
                "confidence_threshold": 0.70,
                "top_two_margin": 0.96,
            }
        }
    )

    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[str, float]
    gradcam_path: str | None = None
    model_version: str
    inference_ms: float = Field(ge=0.0)

    # Capa de seguridad clinica. Los valores por defecto mantienen la
    # compatibilidad con clientes antiguos que solo leen el contrato basico.
    is_conclusive: bool = True
    triage_level: str = "bajo"
    recommendation: str = ""
    confidence_threshold: float = 0.70
    top_two_margin: float = 0.0


class PredictionRead(BaseModel):
    """Elemento del historial. Conserva los nombres planos que ya consumia el
    frontend (`image_hash`, `label`, `model_version`) aunque internamente ahora
    provengan de relaciones."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    image_hash: str
    label: str
    confidence: float
    model_version: str
    inference_ms: float
    created_at: datetime
    gradcam_path: str | None = None
    source: str = "api"


class ScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    probability: float
    lesion_class: LesionClassRead


class PredictionDetailRead(BaseModel):
    """Detalle de una prediccion: imagen, modelo, clase y distribucion completa."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    image: ImageRead
    model: MLModelRead
    predicted_class: LesionClassRead
    confidence: float
    inference_ms: float
    gradcam_path: str | None = None
    source: str
    created_at: datetime
    scores: list[ScoreRead] = Field(default_factory=list)
    feedback: list[FeedbackRead] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def probabilities(self) -> dict[str, float]:
        return {score.lesion_class.code: score.probability for score in self.scores}

    def _clinical_assessment(self) -> ClinicalAssessment:
        """Recalcula la capa de seguridad al vuelo (no se persiste).

        Usa los mismos umbrales configurados que `POST /predict` para que el
        detalle y el resultado original nunca se contradigan.
        """
        settings = get_settings()
        return assess(
            self.predicted_class.code,
            self.confidence,
            self.probabilities,
            confidence_threshold=settings.clinical_confidence_threshold,
            margin_threshold=settings.clinical_margin_threshold,
            high_confidence_threshold=settings.clinical_high_confidence_threshold,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_conclusive(self) -> bool:
        return self._clinical_assessment().is_conclusive

    @computed_field  # type: ignore[prop-decorator]
    @property
    def triage_level(self) -> str:
        return self._clinical_assessment().triage_level

    @computed_field  # type: ignore[prop-decorator]
    @property
    def recommendation(self) -> str:
        return self._clinical_assessment().recommendation

    @computed_field  # type: ignore[prop-decorator]
    @property
    def top_two_margin(self) -> float:
        return self._clinical_assessment().top_two_margin


class ClassStat(BaseModel):
    code: str
    display_name: str
    count: int
    avg_confidence: float | None = None


class StatsSummary(BaseModel):
    total_predictions: int
    unique_images: int
    models_registered: int
    total_feedback: int
    avg_confidence: float | None = None
    avg_inference_ms: float | None = None
    by_class: list[ClassStat] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    model_ready: bool
    model_version: str
    classes: list[str]
