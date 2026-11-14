"""Flujo común de transfer learning para las cinco arquitecturas."""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import yaml
from torch.utils.data import DataLoader

_ML_DIR = Path(__file__).resolve().parents[1]
for _candidate in (_ML_DIR, _ML_DIR / "training", _ML_DIR / "dataset", _ML_DIR / "evaluation"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from dataloader import build_dataloaders, class_distribution
from dataset.preprocessing import load_classes, load_config
from model_factory import (
    MODEL_SPECS,
    build_model,
    freeze_backbone,
    set_frozen_batchnorm_eval,
    trainable_parameters,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "ml" / "models"
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=sorted(MODEL_SPECS))
    parser.add_argument("--epochs", type=int, default=None,
                        help="Prueba corta permitida; el máximo del experimento es 100")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--data-root", type=Path, default=None,
                        help="Directorio processed/ (por defecto ml/data/processed)")
    parser.add_argument("--preset", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true",
                        help="Permite reemplazar checkpoint e historial de esta arquitectura")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def resolve_device(choice: str) -> torch.device:
    if choice != "auto":
        return torch.device(choice)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_preset(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def training_settings(config: dict, preset: dict, args: argparse.Namespace) -> tuple[int, int, int]:
    """Use only the approved optimizer/loss and cap the epoch count at 100."""
    values = {**config["training"], **preset.get("training", {})}
    epochs = int(args.epochs if args.epochs is not None else values["epochs"])
    batch_size = int(values["batch_size"])
    seed = int(args.seed if args.seed is not None else preset.get("seed", config["validation"]["seed"]))
    if not 1 <= epochs <= 100:
        raise ValueError("epochs debe estar entre 1 y el maximo aprobado de 100")
    if batch_size != 64:
        raise ValueError("El batch_size aprobado es 64")
    if values["optimizer"].lower() != "adam" or float(values["learning_rate"]) != 0.001:
        raise ValueError("Este flujo admite exclusivamente Adam con learning rate 0.001")
    if values["loss"] != "cross_entropy":
        raise ValueError("Este flujo admite exclusivamente CrossEntropyLoss")
    if config["input"]["size"] != 224:
        raise ValueError("El tamaño de entrada aprobado es 224 x 224")
    if config["augmentation"] != {"horizontal_flip": 0.5, "rotation_degrees": 10}:
        raise ValueError("La augmentacion aprobada es flip horizontal p=0.5 y rotacion de 10 grados")
    norm = config["normalization"]
    if norm["mean"] != IMAGENET_MEAN or norm["std"] != IMAGENET_STD:
        raise ValueError("La normalizacion aprobada es la de ImageNet")
    return epochs, batch_size, seed


def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module,
             device: torch.device) -> dict[str, float]:
    model.eval()
    loss_sum = 0.0
    correct = seen = 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            loss_sum += criterion(logits, labels).item() * labels.size(0)
            correct += (logits.argmax(1) == labels).sum().item()
            seen += labels.size(0)
    if not seen:
        raise ValueError("El conjunto de validacion esta vacio")
    return {"loss": loss_sum / seen, "accuracy": correct / seen}


def train_one_epoch(model: nn.Module, loader: DataLoader, criterion: nn.Module,
                    optimizer: torch.optim.Optimizer, device: torch.device) -> dict[str, float]:
    model.train()
    set_frozen_batchnorm_eval(model)
    loss_sum = 0.0
    correct = seen = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        loss_sum += loss.item() * labels.size(0)
        correct += (logits.argmax(1) == labels).sum().item()
        seen += labels.size(0)
    if not seen:
        raise ValueError("El conjunto de entrenamiento esta vacio")
    return {"loss": loss_sum / seen, "accuracy": correct / seen}


def run_training(model: nn.Module, train_loader: DataLoader, val_loader: DataLoader,
                 device: torch.device, epochs: int, optimizer: torch.optim.Optimizer,
                 checkpoint_path: Path | None = None, architecture: str = "model",
                 classes: list[str] | None = None) -> tuple[list[dict], dict | None]:
    """Entrena y selecciona por validacion; nunca itera sobre test."""
    criterion = nn.CrossEntropyLoss()
    history: list[dict] = []
    best_checkpoint = None
    best_accuracy = -1.0
    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        train_metrics = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_metrics = evaluate(model, val_loader, criterion, device)
        row = {"epoch": epoch, "train_loss": train_metrics["loss"],
               "train_accuracy": train_metrics["accuracy"],
               "val_loss": val_metrics["loss"], "val_accuracy": val_metrics["accuracy"],
               "seconds": time.perf_counter() - started}
        history.append(row)
        print(f"[{architecture}] epoch {epoch}/{epochs} train_loss={row['train_loss']:.4f} "
              f"train_acc={row['train_accuracy']:.4f} val_loss={row['val_loss']:.4f} "
              f"val_acc={row['val_accuracy']:.4f} ({row['seconds']:.1f}s)")
        if row["val_accuracy"] > best_accuracy:
            best_accuracy = row["val_accuracy"]
            best_checkpoint = {
                "state_dict": copy.deepcopy(model.state_dict()),
                "architecture": architecture,
                "classes": classes or [],
                "class_to_idx": {name: index for index, name in enumerate(classes or [])},
                "epoch": epoch,
                "val_accuracy": best_accuracy,
                "input_size": 224,
                "normalization": {"mode": "imagenet", "mean": IMAGENET_MEAN,
                                  "std": IMAGENET_STD},
            }
            if checkpoint_path is not None:
                torch.save(best_checkpoint, checkpoint_path)
    return history, best_checkpoint


def main() -> None:
    args = parse_args()
    config = load_config(args.model)
    preset = load_preset(args.preset)
    epochs, batch_size, seed = training_settings(config, preset, args)
    set_seed(seed)

    classes = load_classes()
    if len(classes) != 4:
        raise ValueError(f"Se esperaban cuatro clases en labels.json, se encontraron {classes}")
    dest = MODELS_DIR / args.model
    existing = [dest / name for name in ("best.pt", "history.json", "metadata.json")
                if (dest / name).exists()]
    if existing and not args.overwrite:
        raise FileExistsError(f"Ya existen artefactos de {args.model}: {existing}; usa --overwrite")
    dest.mkdir(parents=True, exist_ok=True)

    train_loader, val_loader, _test_loader = build_dataloaders(args.model, root=args.data_root)
    device = resolve_device(args.device)
    model = build_model(args.model, num_classes=len(classes), pretrained=True)
    freeze_backbone(model, args.model)
    model.to(device)
    parameters = list(trainable_parameters(model))
    if not parameters:
        raise RuntimeError("La cabeza clasificadora no tiene parametros entrenables")
    optimizer = torch.optim.Adam(parameters, lr=0.001)

    print(f"[{args.model}] clases={classes}")
    print(f"[{args.model}] distribucion train={class_distribution(train_loader.dataset)}")
    print(f"[{args.model}] dispositivo={device}; cabeza entrenable, backbone congelado")
    history, best = run_training(model, train_loader, val_loader, device, epochs,
                                 optimizer, dest / "best.pt", args.model, classes)
    (dest / "history.json").write_text(json.dumps({
        "model": args.model, "seed": seed, "epochs_requested": epochs,
        "best_val_accuracy": best["val_accuracy"], "history": history,
    }, indent=2), encoding="utf-8")
    (dest / "metadata.json").write_text(json.dumps({
        "architecture": args.model, "torchvision_name": config["torchvision_name"],
        "classes": classes, "class_to_idx": best["class_to_idx"],
        "input_size": 224, "normalization": best["normalization"],
        "best_val_accuracy": best["val_accuracy"], "epoch": best["epoch"],
    }, indent=2), encoding="utf-8")
    print(f"[{args.model}] mejor val_accuracy={best['val_accuracy']:.4f}; checkpoint={dest / 'best.pt'}")


if __name__ == "__main__":
    main()
