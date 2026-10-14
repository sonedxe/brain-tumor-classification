"""Utilidades de imagen para el endpoint de prediccion.

La normalizacion ya no se decide aqui: el `InferenceService` la toma del propio
checkpoint (`normalization`), que registra la que se uso al entrenar. Todos los
modelos de este proyecto usan la normalizacion de ImageNet, pero la fuente de
verdad es el checkpoint, no una constante en el backend.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image


def load_rgb_image(raw: bytes, size: int) -> np.ndarray:
    """Abre la imagen, fuerza RGB y redimensiona. Devuelve HWC float32 0-255."""
    with Image.open(io.BytesIO(raw)) as image:
        rgb = image.convert("RGB")
        resized = rgb.resize((size, size), Image.BILINEAR)
        return np.asarray(resized, dtype=np.float32)
