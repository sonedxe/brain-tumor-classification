"""Augmentacion torchvision: flip horizontal aleatorio y rotacion de hasta 10 grados."""

from __future__ import annotations

from torchvision import transforms

from dataset.preprocessing import load_config


def build_train_transform(model_name: str) -> transforms.Compose:
    """Transformaciones acordadas en los notebooks, con normalizacion ImageNet."""
    config = load_config(model_name)
    norm = config["normalization"]
    aug = config["augmentation"]
    size = config["input"]["size"]
    return transforms.Compose(
        [
            transforms.Resize((size, size)),
            transforms.RandomHorizontalFlip(p=aug["horizontal_flip"]),
            transforms.RandomRotation(aug["rotation_degrees"]),
            transforms.ToTensor(),
            transforms.Normalize(mean=norm["mean"], std=norm["std"]),
        ]
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


def denormalize(tensor, mean: list[float], std: list[float]):
    """Devuelve un tensor NCHW en rango 0-255, para superponer el mapa Grad-CAM."""
    mean_t = torch.tensor(mean, dtype=tensor.dtype, device=tensor.device).view(1, 3, 1, 1)
    std_t = torch.tensor(std, dtype=tensor.dtype, device=tensor.device).view(1, 3, 1, 1)
    out = tensor * std_t + mean_t
    return (out.clamp(0, 1) * 255).to(torch.uint8)
