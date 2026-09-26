"""Construccion de los dataloaders."""

from __future__ import annotations

from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from torchvision.datasets import ImageFolder

from augmentation import build_train_transform, build_val_transform
from dataset.preprocessing import load_classes, load_config

RAW_DIR = Path(__file__).resolve().parents[1] / "dataset" / "raw"


def resolve_split_dir(model_name: str, split: str) -> Path:
    return RAW_DIR / model_name / "processed" / split


def assert_classes_match(dataset_root: Path) -> None:
    """El orden de las carpetas del dataset debe coincidir con labels.json.

    ImageFolder ordena por nombre, asi que un orden distinto en el disco
    reordena las etiquetas en silencio y el modelo entrena con las clases
    permutadas sin ningún aviso.
    """
    expected = load_classes()
    found = sorted(p.name for p in dataset_root.iterdir() if p.is_dir())
    if found != sorted(expected):
        raise ValueError(
            f"Clases del dataset {found} no coinciden con labels.json {sorted(expected)}"
        )


def build_datasets(model_name: str, root: Path | None = None) -> tuple[Dataset, Dataset, Dataset]:
    config = load_config(model_name)
    base = root or resolve_split_dir(model_name, "")
    train_root = base / "train"
    val_root = base / "val"
    test_root = base / "test"

    for split_root in (train_root, val_root, test_root):
        assert_classes_match(split_root)

    train_ds = ImageFolder(train_root, transform=build_train_transform(model_name))
    val_ds = ImageFolder(val_root, transform=build_val_transform(model_name))
    test_ds = ImageFolder(test_root, transform=build_val_transform(model_name))

    assert train_ds.classes == load_classes(), (
        f"Orden de clases del dataset {train_ds.classes} "
        f"difiere de labels.json {load_classes()}"
    )
    assert config["input"]["channels"] == 3
    return train_ds, val_ds, test_ds


def build_dataloaders(
    model_name: str,
    root: Path | None = None,
    batch_size: int | None = None,
    num_workers: int = 4,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    config = load_config(model_name)
    train_ds, val_ds, test_ds = build_datasets(model_name, root)
    bs = batch_size or config["training"]["batch_size"]
    train_params = config["normalization"]

    common = dict(num_workers=num_workers, pin_memory=torch.backends.mps.is_available())
    train_loader = DataLoader(
        train_ds, batch_size=bs, shuffle=True, drop_last=True, **common
    )
    val_loader = DataLoader(val_ds, batch_size=bs, shuffle=False, **common)
    test_loader = DataLoader(test_ds, batch_size=bs, shuffle=False, **common)

    assert train_params["mode"] in {"tanh", "imagenet"}
    return train_loader, val_loader, test_loader


def class_distribution(dataset: Dataset) -> dict[str, int]:
    targets = getattr(dataset, "targets", [])
    names = dataset.classes
    return {names[i]: targets.count(i) for i in range(len(names))}
