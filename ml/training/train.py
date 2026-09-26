"""Entrenamiento con transfer learning.

Uso:
    python train.py --model mobilenetv3
    python train.py --model resnet18 --fold 0
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import timm
import torch
import torch.nn as nn
import yaml
from torch.utils.data import DataLoader

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
    return parser.parse_args()


def resolve_device(choice: str) -> torch.device:
    if choice != "auto":
        return torch.device(choice)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def build_model(config: dict, num_classes: int) -> nn.Module:
    model = timm.create_model(
        config["timm_name"],
        pretrained=config["pretrained"],
        num_classes=num_classes,
        drop_rate=config["head"]["dropout"],
    )
    return model


def freeze_backbone(model: nn.Module, freeze: bool) -> None:
    for param in model.parameters():
        param.requires_grad = not freeze


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
    if args.epochs:
        config["training"]["epochs"] = args.epochs

    classes = load_classes()
    device = resolve_device(args.device)
    dest = output_dir(args.model, args.fold)

    train_loader, val_loader, _ = build_dataloaders(
        args.model, batch_size=args.batch_size
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
        else:
            epochs_without_gain += 1
            if epochs_without_gain >= patience:
                print(f"[{args.model}] early stopping en epoch {epoch}")
                break

    (dest / "history.json").write_text(
        json.dumps(
            {
                "model": args.model,
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


if __name__ == "__main__":
    main()
