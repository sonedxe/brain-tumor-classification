"""Data augmentation con torchvision.

Sustituye al ImageDataGenerator descrito en el manuscripto. La lista de
transformaciones se mantiene: rotation, zoom, horizontal flip y jitter de
brillo. La razon del cambio esta en docs/notas-correccion-paper.md.
"""

from __future__ import annotations

import torch
from timm.data import create_transform, resolve_data_config
from torchvision import transforms

from dataset.preprocessing import load_config


def build_train_transform(model_name: str) -> transforms.Compose:
    """Transformaciones de entrenamiento leyendo la config y la pretrained_cfg.

    Se delega en `create_transform` para que la normalizacion salga de la
    arquitectura real del modelo y no de un valor escrito a mano. Asi es
    imposible que los cinco modelos acaben con la misma normalizacion por error.
    """
    config = load_config(model_name)
    aug = config["augmentation"]

    return create_transform(
        input_size=config["input"]["size"],
        is_training=True,
        color_jitter=0.2 if aug.get("brightness_range") else None,
        auto_augment=None,
        interpolation="bilinear",
        re_prob=0.0,
        re_mode="pixel",
        re_count=1,
        mean=config["normalization"]["mean"],
        std=config["normalization"]["std"],
    )


def build_val_transform(model_name: str) -> transforms.Compose:
    config = load_config(model_name)
    norm = config["normalization"]
    size = config["input"]["size"]

    return transforms.Compose(
        [
            transforms.Resize((size, size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=norm["mean"], std=norm["std"]),
        ]
    )


def build_from_pretrained_cfg(model) -> tuple[transforms.Compose, transforms.Compose]:
    """Variante que toma medias y desviaciones de la propia pretrained_cfg."""
    config = resolve_data_config(model.pretrained_cfg, model=model)
    train_tf = create_transform(**config, is_training=True)
    val_tf = create_transform(**config, is_training=False)
    return train_tf, val_tf


def denormalize(tensor: torch.Tensor, mean: list[float], std: list[float]) -> torch.Tensor:
    """Devuelve un tensor NCHW en rango 0-255, para superponer el mapa Grad-CAM."""
    mean_t = torch.tensor(mean, dtype=tensor.dtype, device=tensor.device).view(1, 3, 1, 1)
    std_t = torch.tensor(std, dtype=tensor.dtype, device=tensor.device).view(1, 3, 1, 1)
    out = tensor * std_t + mean_t
    return (out.clamp(0, 1) * 255).to(torch.uint8)
