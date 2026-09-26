"""Preprocesamiento de imagenes: resize, RGB y normalizacion por modelo."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml
from PIL import Image

CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"


def load_config(model: str) -> dict:
    with (CONFIGS_DIR / f"{model}.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_classes() -> list[str]:
    import json

    with (CONFIGS_DIR / "labels.json").open(encoding="utf-8") as fh:
        return json.load(fh)["classes"]


def to_rgb(image: Image.Image) -> Image.Image:
    """Convierte a RGB, porque el dataset mezcla PNG, JPG y mapas de gris."""
    return image if image.mode == "RGB" else image.convert("RGB")


def resize(image: Image.Image, size: int) -> Image.Image:
    return image.resize((size, size), Image.BILINEAR)


def normalize(array: np.ndarray, mean: list[float], std: list[float]) -> np.ndarray:
    """Normaliza a NCHW float32.

    La normalizacion NO es la misma para los cinco modelos. MobileNetV3,
    EfficientNetB0, ShuffleNetV2 y DenseNet121 usan mean=std=0.5, que equivale
    al rango -1 a 1 del manuscripto. ResNet18 usa medias y desviaciones de
    ImageNet. Aplicar una sola normalizacion a todos hace que ResNet18 entrene
    sin converger, sin emitir error.
    """
    mean_arr = np.asarray(mean, dtype=np.float32).reshape(1, 3, 1, 1)
    std_arr = np.asarray(std, dtype=np.float32).reshape(1, 3, 1, 1)
    chw = np.transpose(array, (2, 0, 1))[np.newaxis, ...]
    return ((chw / 255.0) - mean_arr) / std_arr


def preprocess_image(image: Image.Image, config: dict) -> np.ndarray:
    size = config["input"]["size"]
    arr = np.asarray(resize(to_rgb(image), size), dtype=np.float32)
    norm = config["normalization"]
    return normalize(arr, norm["mean"], norm["std"])


def preprocess_path(path: Path, config: dict) -> np.ndarray:
    with Image.open(path) as image:
        return preprocess_image(image, config)
