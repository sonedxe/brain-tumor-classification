"""Metricas de clasificacion y matrices de confusion (OE2, OE4).

Uso:
    python metrics.py --model mobilenetv3 --weights ../models/mobilenetv3/best.pt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader

_ML_DIR = Path(__file__).resolve().parents[1]
for _candidate in (_ML_DIR, _ML_DIR / "training", _ML_DIR / "dataset", _ML_DIR / "evaluation"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from dataset.preprocessing import load_classes

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "ml" / "evaluation" / "reports"

TUMOR_CLASSES = ("glioma", "meningioma", "pituitario")


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, classes: list[str]) -> dict:
    matrix = confusion_matrix(y_true, y_pred, labels=list(range(len(classes))))
    per_class = classification_report(
        y_true, y_pred, labels=list(range(len(classes))), target_names=classes, output_dict=True, zero_division=0
    )

    tumor_mask = np.isin(y_true, [classes.index(c) for c in TUMOR_CLASSES])
    tumor_pred_mask = np.isin(y_pred, [classes.index(c) for c in TUMOR_CLASSES])

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_precision": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "macro_recall": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "tumor_recall": recall_score(
            y_true, y_pred, labels=[classes.index(c) for c in TUMOR_CLASSES], average="macro", zero_division=0
        ),
        "tumor_sensitivity": float(
            (tumor_pred_mask[tumor_mask] == y_true[tumor_mask]).mean()
        ),
        "specificity_no_tumor": per_class[classes[-1]]["recall"],
        "confusion_matrix": matrix.tolist(),
        "per_class": per_class,
    }


@torch.no_grad()
def predict_all(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    truths, preds, probabilities = [], [], []
    for images, labels in loader:
        images = images.to(device)
        logits = model(images)
        probs = torch.softmax(logits, dim=1).cpu().numpy()
        truths.append(labels.numpy())
        preds.append(probs.argmax(axis=1))
        probabilities.append(probs)
    return np.concatenate(truths), np.concatenate(preds), np.concatenate(probabilities)


@torch.no_grad()
def measure_inference_time(model: torch.nn.Module, loader: DataLoader, device: torch.device, warmup: int = 5) -> float:
    import time

    batches = []
    for index, (images, _) in enumerate(loader):
        batches.append(images.to(device))
        if index == warmup:
            break
    for images in batches:
        model(images)

    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps":
        torch.mps.synchronize()

    started = time.perf_counter()
    for images in batches:
        model(images)
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps":
        torch.mps.synchronize()
    elapsed_ms = (time.perf_counter() - started) * 1000 / len(batches)
    return elapsed_ms / batches[0].size(0)


def format_confusion_matrix(matrix: np.ndarray, classes: list[str]) -> str:
    width = max(len(c) for c in classes) + 2
    header = " " * width + "".join(f"{c:>{max(len(c), 6)}}" for c in classes)
    lines = [header]
    for name, row in zip(classes, matrix):
        cells = "".join(f"{v:>{max(len(name), 6)}}" for v in row)
        lines.append(f"{name:>{width - 1}}{cells}")
    return "\n".join(lines)


def count_parameters(model: torch.nn.Module) -> tuple[int, int]:
    """Devuelve (totales, entrenables). Para docs/tabla-comparativa.md."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def checkpoint_size_mb(path: Path) -> float:
    """Tamano aproximado del modelo en disco, en MB."""
    return path.stat().st_size / (1024 * 1024)


def save_report(model_name: str, metrics: dict, extra: dict | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"model": model_name, "classes": load_classes(), **metrics, **(extra or {})}
    path = REPORTS_DIR / f"{model_name}_metrics.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--data-root", type=Path, default=None,
                        help="processed/ alternativo (por defecto ml/dataset/processed)")
    args = parser.parse_args()

    from dataloader import build_dataloaders
    from train import build_model, resolve_device

    from dataset.preprocessing import load_config

    config = load_config(args.model)
    classes = load_classes()
    device = resolve_device("auto")

    checkpoint = torch.load(args.weights, map_location=device, weights_only=False)
    model = build_model(config, len(classes))
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device)

    _, _, test_loader = build_dataloaders(args.model, root=args.data_root, batch_size=args.batch_size)
    y_true, y_pred, _ = predict_all(model, test_loader, device)
    metrics = compute_metrics(y_true, y_pred, classes)
    ms_per_image = measure_inference_time(model, test_loader, device)
    total_params, trainable_params = count_parameters(model)

    extra = {
        "ms_per_image": ms_per_image,
        "num_parameters": total_params,
        "trainable_parameters": trainable_params,
        "num_parameters_m": round(total_params / 1e6, 3),
        "checkpoint_mb": round(checkpoint_size_mb(args.weights), 3),
        "input_size": checkpoint.get("input_size"),
        "normalization": checkpoint.get("normalization"),
        "best_val_accuracy": checkpoint.get("val_accuracy"),
    }
    path = save_report(args.model, metrics, extra)
    print(f"accuracy      = {metrics['accuracy']:.4f}")
    print(f"macro F1      = {metrics['macro_f1']:.4f}")
    print(f"weighted F1   = {metrics['weighted_f1']:.4f}")
    print(f"tumor recall  = {metrics['tumor_recall']:.4f}")
    print(f"ms/imagen     = {ms_per_image:.2f}")
    print(f"parametros    = {total_params} ({total_params / 1e6:.2f}M)")
    print(f"checkpoint    = {extra['checkpoint_mb']:.2f} MB")
    print(format_confusion_matrix(np.array(metrics["confusion_matrix"]), classes))
    print(f"reporte: {path}")


if __name__ == "__main__":
    main()
