"""Datos de referencia (catalogos) que debe tener la base al arrancar.

Siembra las cuatro `lesion_classes` (desde `ml/configs/labels.json`, la fuente
unica de verdad) y registra las cinco arquitecturas CNN comparadas en `ml_models`
con sus metricas reales de `ml/evaluation/reports/comparison.json`.

Es idempotente: se puede llamar en cada arranque sin duplicar filas.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import CLASSES
from app.db.base import Base
from app.models.lesion_class import LesionClass
from app.models.ml_model import MLModel

logger = logging.getLogger(__name__)

CLASS_CATALOG: dict[str, dict[str, object]] = {
    "glioma": {
        "display_name": "Glioma",
        "is_tumor": True,
        "description": "Tumor primario de las celulas gliales",
    },
    "meningioma": {
        "display_name": "Meningioma",
        "is_tumor": True,
        "description": "Tumor de las meninges",
    },
    "pituitario": {
        "display_name": "Pituitario",
        "is_tumor": True,
        "description": "Tumor de la glandula pituitaria",
    },
    "no_tumor": {
        "display_name": "Sin tumor",
        "is_tumor": False,
        "description": "Sin hallazgos tumorales",
    },
}

# Metricas de test tomadas de ml/evaluation/reports/comparison.json.
MODEL_REGISTRY: dict[str, dict[str, object]] = {
    "mobilenetv3": {
        "architecture": "mobilenet_v3_large",
        "num_parameters_m": 5.483,
        "accuracy": 0.8719,
        "macro_f1": 0.869725,
        "roc_auc": 0.971,
    },
    "efficientnetb0": {
        "architecture": "efficientnet_b0",
        "num_parameters_m": 5.289,
        "accuracy": 0.8706,
        "macro_f1": 0.867325,
        "roc_auc": 0.9711,
    },
    "shufflenetv2": {
        "architecture": "shufflenet_v2_x1_0",
        "num_parameters_m": 2.279,
        "accuracy": 0.8256,
        "macro_f1": 0.8215,
        "roc_auc": 0.9539,
    },
    "densenet121": {
        "architecture": "densenet121",
        "num_parameters_m": 7.979,
        "accuracy": 0.8756,
        "macro_f1": 0.87415,
        "roc_auc": 0.9677,
    },
    "resnet18": {
        "architecture": "resnet18",
        "num_parameters_m": 11.69,
        "accuracy": 0.8569,
        "macro_f1": 0.853675,
        "roc_auc": 0.9644,
    },
}

DATASET_NAME = "brain-tumor-mri"


def seed_reference_data(db: Session, active_version: str | None = None) -> None:
    active_version = active_version or get_settings().model_version
    _seed_classes(db)
    _seed_models(db, active_version)
    db.commit()


def _seed_classes(db: Session) -> None:
    existing = {row.code for row in db.scalars(select(LesionClass)).all()}
    for index, code in enumerate(CLASSES):
        if code in existing:
            continue
        meta = CLASS_CATALOG.get(code, {})
        db.add(
            LesionClass(
                code=code,
                display_name=str(meta.get("display_name", code.title())),
                index=index,
                is_tumor=bool(meta.get("is_tumor", code != "no_tumor")),
                description=str(meta.get("description") or "") or None,
            )
        )


def _seed_models(db: Session, active_version: str) -> None:
    existing = {row.name for row in db.scalars(select(MLModel)).all()}
    for name, meta in MODEL_REGISTRY.items():
        version = f"{name}-v1"
        if name in existing:
            # Mantiene el modelo activo alineado con la configuracion actual.
            model = db.scalar(select(MLModel).where(MLModel.name == name))
            if model is not None:
                model.is_active = version == active_version
            continue
        db.add(
            MLModel(
                name=name,
                architecture=str(meta["architecture"]),
                version=version,
                dataset=DATASET_NAME,
                num_parameters_m=float(meta["num_parameters_m"]),
                accuracy=float(meta["accuracy"]),
                macro_f1=float(meta["macro_f1"]),
                roc_auc=float(meta["roc_auc"]),
                is_active=version == active_version,
            )
        )


def create_all_and_seed(db: Session) -> None:
    """Crea las tablas (si faltan) y siembra los catalogos."""
    import app.models  # noqa: F401  (registra todas las tablas en Base.metadata)

    Base.metadata.create_all(bind=db.get_bind())
    seed_reference_data(db)
    logger.info("Catalogo sembrado: %d clases, %d modelos", len(CLASSES), len(MODEL_REGISTRY))
