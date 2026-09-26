"""Constantes compartidas con el modulo de machine learning."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LABELS_PATH = REPO_ROOT / "ml" / "configs" / "labels.json"

TUMOR_CLASSES = ("glioma", "meningioma", "pituitario")
NO_TUMOR_CLASS = "no_tumor"


@lru_cache
def load_classes() -> tuple[str, ...]:
    """Lee ml/configs/labels.json, fuente unica de verdad.

    El modulo de entrenamiento y el backend leen el mismo archivo, de modo que
    las etiquetas no pueden desincronizarse entre el modelo y la API.
    """
    with LABELS_PATH.open(encoding="utf-8") as handle:
        return tuple(json.load(handle)["classes"])


CLASSES: tuple[str, ...] = load_classes()
NUM_CLASSES: int = len(CLASSES)
