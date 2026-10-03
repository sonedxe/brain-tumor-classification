"""Entrenamiento con transfer learning.

Uso:
    python train.py --model mobilenetv3
    python train.py --model mobilenetv3 --preset ../configs/experiments/initial.yaml --device cuda
    python train.py --model resnet18 --fold 0
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import timm
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

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = REPO_ROOT / "ml" / "configs"
MODELS_DIR = REPO_ROOT / "ml" / "models"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Nombre del YAML en ml/configs")
    parser.add_argument("--fold", type=int, default=None, help="Fold de kfold, omitir para holdout")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--data-root", type=Path, default=None,
                        help="processed/ alternativo (por defecto ml/dataset/processed)")
    parser.add_argument("--preset", type=Path, default=None,
                        help="YAML de experimento (p. ej. ml/configs/experiments/initial.yaml)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Sobrescribe el seed del preset/YAML")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    """Fija el seed global para repetir el experimento."""
    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_preset(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def apply_preset(config: dict, preset: dict, args: argparse.Namespace) -> int:
    """El preset centraliza lo comun; el YAML del modelo conserva arquitectura,
    normalizacion, transfer y Grad-CAM. Precedencia: CLI > preset > YAML."""
    training = preset.get("training", {})
    for key in ("batch_size", "epochs", "optimizer", "learning_rate",
                "weight_decay", "scheduler", "early_stopping_patience"):
        if key in training:
            config["training"][key] = training[key]
    seed = args.seed if args.seed is not None else preset.get("seed", 42)
    return int(seed)


def write_metadata(dest: Path, model_name: str, config: dict, classes: list[str],
                   version: str, best_accuracy: float, epoch: int) -> Path:
    """Contrato del artefacto que eventualmente consumira backend.

    ml/models/<modelo>/best.pt + metadata.json con lo minimo para inferir:
    arquitectura timm, clases, tamano de entrada y normalizacion exacta.
    """
    norm = config["normalization"]
    path = dest / "metadata.json"
    path.write_text(json.dumps({
        "model": model_name,
        "version": version,
        "timm_name": config["timm_name"],
        "classes": classes,
        "num_classes": len(classes),
        "input_size": config["input"]["size"],
        "normalization": {"mode": norm["mode"], "mean": norm["mean"], "std": norm["std"]},
        "best_val_accuracy": best_accuracy,
        "epoch": epoch,
    }, indent=2), encoding="utf-8")
    return path


def resolve_device(choice: str) -> torch.device:
    if choice != "auto":
        return torch.device(choice)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def build_model(config: dict, num_classes: int) -> nn.Module:
    """Construye el modelo con pesos ImageNet y head de 4 clases.

    Fuente `timm` (4 modelos) o `torchvision` (ShuffleNetV2: timm 1.x no lo
    incluye; torchvision si ofrece `shufflenet_v2_x1_0` con pesos
    IMAGENET1K_V1, decision documentada en docs/notas-correccion-paper.md).
    """
    if config.get("source", "timm") == "torchvision":
        import torchvision

        factory = getattr(torchvision.models, config["timm_name"])
        weights = config.get("torchvision_weights", "IMAGENET1K_V1") if config["pretrained"] else None
        model = factory(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(p=config["head"]["dropout"]),
            nn.Linear(in_features, num_classes),
        )
        return model
    return timm.create_model(
        config["timm_name"],
        pretrained=config["pretrained"],
        num_classes=num_classes,
        drop_rate=config["head"]["dropout"],
    )


def freeze_backbone(model: nn.Module, freeze: bool) -> None:
    """Congela el backbone pero mantiene entrenable el clasificador.

    Sin la segunda parte, el optimizador recibiria una lista de parametros
    vacia y el entrenamiento abortaria (ValueError de AdamW).
    """
    for param in model.parameters():
        param.requires_grad = not freeze
    if freeze:
        if hasattr(model, "get_classifier"):
            head = model.get_classifier()
        else:  # torchvision (ShuffleNetV2): head reemplazado en build_model
            head = model.fc
        for param in head.parameters():
            param.requires_grad = True


def build_criterion(config: dict) -> nn.Module:
    if config["training"]["loss"] != "cross_entropy":
        raise ValueError(f"Perdida no soportada: {config['training']['loss']}")
    return nn.CrossEntropyLoss()


def build_optimizer(model: nn.Module, config: dict) -> torch.optim.Optimizer:
    params = config["training"]
    if params["optimizer"] != "adamw":
        raise ValueError(f"Optimizador no soportado: {params['optimizer']}")
    return torch.optim.AdamW(
        model.parameters(),
        lr=params["learning_rate"],
        weight_decay=params["weight_decay"],
    )


def build_scheduler(optimizer: torch.optim.Optimizer, config: dict) -> torch.optim.lr_scheduler.LRScheduler:
    if config["training"]["scheduler"] != "cosine":
        raise ValueError(f"Scheduler no soportado: {config['training']['scheduler']}")
    return torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config["training"]["epochs"]
    )


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device) -> dict:
    model.eval()
    total_loss = 0.0
    correct = 0
    seen = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        logits = model(images)
        total_loss += criterion(logits, labels).item() * labels.size(0)
        correct += (logits.argmax(dim=1) == labels).sum().item()
        seen += labels.size(0)
    return {"loss": total_loss / seen, "accuracy": correct / seen}


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    running = 0.0
    seen = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(images), labels)
        loss.backward()
        optimizer.step()
        running += loss.item() * labels.size(0)
        seen += labels.size(0)
    return running / seen


def output_dir(model_name: str, fold: int | None) -> Path:
    folder = MODELS_DIR / model_name
    if fold is not None:
        folder = folder / f"fold{fold}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def main() -> None:
    args = parse_args()
    config = load_config(args.model)
    preset = load_preset(args.preset)
    seed = apply_preset(config, preset, args)
    set_seed(seed)
    version = f"{args.model}-{preset.get('version', 'v1')}"
    if args.epochs:
        config["training"]["epochs"] = args.epochs

    classes = load_classes()
    device = resolve_device(args.device)
    dest = output_dir(args.model, args.fold)

    train_loader, val_loader, _ = build_dataloaders(
        args.model, root=args.data_root, batch_size=args.batch_size
    )
    print(f"[{args.model}] clases={classes}")
    print(f"[{args.model}] distribucion train={class_distribution(train_loader.dataset)}")
    print(f"[{args.model}] dispositivo={device}")

    model = build_model(config, len(classes)).to(device)
    criterion = build_criterion(config)

    transfer = config["transfer"]
    if transfer["freeze_backbone"]:
        freeze_backbone(model, True)
        optimizer = torch.optim.AdamW(
            [p for p in model.parameters() if p.requires_grad],
            lr=config["training"]["learning_rate"],
            weight_decay=config["training"]["weight_decay"],
        )
    else:
        optimizer = build_optimizer(model, config)
    scheduler = build_scheduler(optimizer, config)

    history: list[dict] = []
    best_accuracy = 0.0
    patience = config["training"]["early_stopping_patience"]
    epochs_without_gain = 0

    for epoch in range(1, config["training"]["epochs"] + 1):
        if transfer["freeze_backbone"] and epoch == transfer["unfreeze_from_epoch"]:
            freeze_backbone(model, False)
            optimizer = build_optimizer(model, config)
            scheduler = build_scheduler(optimizer, config)
            print(f"[{args.model}] epoch {epoch}: fine-tuning del backbone")

        started = time.perf_counter()
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_metrics = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.perf_counter() - started

        history.append({"epoch": epoch, "train_loss": train_loss, **val_metrics})
        print(
            f"[{args.model}] epoch {epoch}/{config['training']['epochs']} "
            f"train_loss={train_loss:.4f} val_loss={val_metrics['loss']:.4f} "
            f"val_acc={val_metrics['accuracy']:.4f} ({elapsed:.1f}s)"
        )

        if val_metrics["accuracy"] > best_accuracy:
            best_accuracy = val_metrics["accuracy"]
            epochs_without_gain = 0
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "model": config["timm_name"],
                    "classes": classes,
                    "normalization": config["normalization"],
                    "input_size": config["input"]["size"],
                    "epoch": epoch,
                    "val_accuracy": best_accuracy,
                },
                dest / "best.pt",
            )
            write_metadata(dest, args.model, config, classes, version, best_accuracy, epoch)
        else:
            epochs_without_gain += 1
            if epochs_without_gain >= patience:
                print(f"[{args.model}] early stopping en epoch {epoch}")
                break

    (dest / "history.json").write_text(
        json.dumps(
            {
                "model": args.model,
                "version": version,
                "seed": seed,
                "preset": str(args.preset) if args.preset else None,
                "role": config["role"],
                "fold": args.fold,
                "normalization": config["normalization"]["mode"],
                "best_val_accuracy": best_accuracy,
                "history": history,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[{args.model}] mejor exactitud de validacion: {best_accuracy:.4f}")
    print(f"[{args.model}] pesos guardados en {dest / 'best.pt'}")
    print(f"[{args.model}] metadatos para backend en {dest / 'metadata.json'}")


if __name__ == "__main__":
    main()
