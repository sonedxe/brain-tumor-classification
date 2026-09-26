"""Utilidades de imagen: carga, resize y normalizacion por modelo."""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

NORMALIZATION_MODES: dict[str, dict[str, list[float]]] = {
    "tanh": {"mean": [0.5, 0.5, 0.5], "std": [0.5, 0.5, 0.5]},
    "imagenet": {
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
    },
}


def load_rgb_image(raw: bytes, size: int) -> np.ndarray:
    """Abre la imagen, fuerza RGB y redimensiona. Devuelve HWC float32 0-255."""
    with Image.open(io.BytesIO(raw)) as image:
        rgb = image.convert("RGB")
        resized = rgb.resize((size, size), Image.BILINEAR)
        return np.asarray(resized, dtype=np.float32)


def normalize(array: np.ndarray, mode: str) -> np.ndarray:
    """Normaliza a NCHW float32 segun el modo del modelo.

    La normalizacion no es identica para los cinco modelos: MobileNetV3,
    EfficientNetB0, ShuffleNetV2 y DenseNet121 usan mean=std=0.5, que es el
    rango -1 a 1 del manuscripto; ResNet18 usa medias y desviaciones de
    ImageNet. Aplicar una sola a todos hace que ResNet18 falle en silencio.
    """
    if mode not in NORMALIZATION_MODES:
        raise ValueError(f"Modo de normalizacion desconocido: {mode}")

    norm = NORMALIZATION_MODES[mode]
    mean = np.asarray(norm["mean"], dtype=np.float32).reshape(1, 3, 1, 1)
    std = np.asarray(norm["std"], dtype=np.float32).reshape(1, 3, 1, 1)
    chw = np.transpose(array, (2, 0, 1))[np.newaxis, ...]
    return ((chw / 255.0) - mean) / std


def to_displayable(array: np.ndarray, mode: str) -> np.ndarray:
    """Deshace la normalizacion y devuelve HWC uint8, para superponer el mapa."""
    if mode not in NORMALIZATION_MODES:
        raise ValueError(f"Modo de normalizacion desconocido: {mode}")

    norm = NORMALIZATION_MODES[mode]
    mean = np.asarray(norm["mean"], dtype=np.float32).reshape(3, 1, 1)
    std = np.asarray(norm["std"], dtype=np.float32).reshape(3, 1, 1)

    chw = array[0] if array.ndim == 4 else array
    hwc = np.transpose(chw * std + mean, (1, 2, 0))
    return np.uint8(np.clip(hwc * 255.0, 0, 255))
