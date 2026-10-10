"""Construccion de los dataloaders sobre la particion compartida.

Los cinco modelos usan exactamente los mismos splits fisicos, generados una
sola vez con `ml/dataset/prepare.py`:

    ml/data/processed/{train,val,test}/<clase>/*

No se duplica el dataset por modelo: el nombre del modelo solo selecciona los
transforms (normalizacion especifica) de su YAML.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ML_DIR = Path(__file__).resolve().parents[1]
for _candidate in (_ML_DIR, _ML_DIR / "training", _ML_DIR / "dataset", _ML_DIR / "evaluation"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

import torch
from torch.utils.data import DataLoader, Dataset
from torchvision.datasets import ImageFolder

from augmentation import build_train_transform, build_val_transform
from dataset.preprocessing import load_classes, load_config

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
SPLITS = ("train", "val", "test")


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
    """Tres splits COMPARTIDOS por los cinco modelos.

    `root` es ml/data/processed (o un directorio temporal en pruebas).
    `model_name` solo elige los transforms de ml/configs/<modelo>.yaml.
    """
    config = load_config(model_name)
    base = root or PROCESSED_DIR
    train_root = base / "train"
    val_root = base / "val"
    test_root = base / "test"

    for split_root in (train_root, val_root, test_root):
        assert_classes_match(split_root)

    train_ds = CanonicalLabels(ImageFolder(train_root, transform=build_train_transform(model_name)))
    val_ds = CanonicalLabels(ImageFolder(val_root, transform=build_val_transform(model_name)))
    test_ds = CanonicalLabels(ImageFolder(test_root, transform=build_val_transform(model_name)))

    assert config["input"]["channels"] == 3
    return train_ds, val_ds, test_ds


class CanonicalLabels(Dataset):
    """Remapea los indices de ImageFolder al orden de labels.json.

    ImageFolder ordena alfabeticamente (glioma, meningioma, no_tumor,
    pituitario), pero labels.json —contrato compartido con backend y
    frontend— define (glioma, meningioma, pituitario, no_tumor). Sin este
    remapeo, entrenar con las etiquetas permutadas en silencio.
    """

    def __init__(self, base: ImageFolder) -> None:
        self.base = base
        canonical = load_classes()
        self.classes: list[str] = list(canonical)
        self.target_mapping: list[int] = [canonical.index(c) for c in base.classes]
        self.targets: list[int] = [self.target_mapping[t] for t in base.targets]

    def __len__(self) -> int:
        return len(self.base)

    def __getitem__(self, index: int):
        image, target = self.base[index]
        return image, self.target_mapping[target]


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

    common = dict(num_workers=num_workers, pin_memory=torch.cuda.is_available())
    train_loader = DataLoader(
        train_ds, batch_size=bs, shuffle=True, drop_last=False, **common
    )
    val_loader = DataLoader(val_ds, batch_size=bs, shuffle=False, **common)
    test_loader = DataLoader(test_ds, batch_size=bs, shuffle=False, **common)

    assert train_params["mode"] in {"tanh", "imagenet"}
    return train_loader, val_loader, test_loader


def class_distribution(dataset: Dataset) -> dict[str, int]:
    targets = getattr(dataset, "targets", [])
    names = dataset.classes
    return {names[i]: targets.count(i) for i in range(len(names))}
