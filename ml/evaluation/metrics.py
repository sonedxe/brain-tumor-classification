"""Reproducible evaluation of trained classifiers on the independent test split.

The evaluator reads checkpoints with PyTorch's restricted ``weights_only``
unpickler, validates their class and preprocessing contract, and writes one
metrics JSON and one per-example predictions JSON per model.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import torch
from sklearn.metrics import confusion_matrix, roc_auc_score
from torch.utils.data import DataLoader

_ML_DIR = Path(__file__).resolve().parents[1]
for _candidate in (_ML_DIR, _ML_DIR / "training", _ML_DIR / "dataset", _ML_DIR / "evaluation"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from dataset.download import SUBTYPE_TO_CLASS, normalize_class_name  # noqa: E402
from dataset.preprocessing import load_classes, load_config  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "ml" / "evaluation" / "reports"
PROCESSED_DIR = _ML_DIR / "data" / "processed"
MODEL_NAMES = ("mobilenetv3", "efficientnetb0", "shufflenetv2", "resnet18", "densenet121")
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
TUMOR_CLASSES = ("glioma", "meningioma", "pituitario")


class ManifestMismatchError(ValueError):
    """The manifest does not describe the test images in the selected data root."""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash the exact bytes of a file without loading it all into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def _same_float_list(actual: Any, expected: list[float]) -> bool:
    if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
        return False
    try:
        return all(math.isclose(float(a), float(e), rel_tol=0.0, abs_tol=1e-8)
                   for a, e in zip(actual, expected))
    except (TypeError, ValueError):
        return False


def validate_checkpoint_metadata(
    checkpoint: dict[str, Any], architecture: str, classes: list[str], config: dict[str, Any]
) -> dict[str, int]:
    """Fail closed unless checkpoint labels and preprocessing match evaluation."""
    if not isinstance(checkpoint, dict):
        raise ValueError("Checkpoint inválido: se esperaba un diccionario seguro")
    if checkpoint.get("architecture") != architecture:
        raise ValueError(
            f"Arquitectura incompatible: checkpoint={checkpoint.get('architecture')!r}, "
            f"solicitada={architecture!r}"
        )
    checkpoint_classes = checkpoint.get("classes")
    if checkpoint_classes != classes:
        raise ValueError(
            f"Orden de clases incompatible: checkpoint={checkpoint_classes!r}, "
            f"evaluador={classes!r}"
        )
    expected_mapping = {name: index for index, name in enumerate(classes)}
    checkpoint_mapping = checkpoint.get("class_to_idx")
    if not isinstance(checkpoint_mapping, dict) or checkpoint_mapping != expected_mapping:
        raise ValueError(
            f"class_to_idx incompatible: checkpoint={checkpoint_mapping!r}, "
            f"evaluador={expected_mapping!r}"
        )

    expected_size = int(config["input"]["size"])
    if checkpoint.get("input_size") != expected_size:
        raise ValueError(
            f"Tamaño de entrada incompatible: checkpoint={checkpoint.get('input_size')!r}, "
            f"transformación={expected_size}"
        )
    expected_norm = config["normalization"]
    checkpoint_norm = checkpoint.get("normalization")
    if not isinstance(checkpoint_norm, dict):
        raise ValueError("Checkpoint incompatible: falta el diccionario 'normalization'")
    if checkpoint_norm.get("mode") != expected_norm.get("mode"):
        raise ValueError(
            f"Modo de normalización incompatible: checkpoint={checkpoint_norm.get('mode')!r}, "
            f"transformación={expected_norm.get('mode')!r}"
        )
    for key in ("mean", "std"):
        if not _same_float_list(checkpoint_norm.get(key), expected_norm.get(key, [])):
            raise ValueError(
                f"Normalización incompatible en {key}: checkpoint={checkpoint_norm.get(key)!r}, "
                f"transformación={expected_norm.get(key)!r}"
            )

    if not isinstance(checkpoint.get("state_dict"), dict):
        raise ValueError("Checkpoint inválido: falta un state_dict")
    return expected_mapping


def _manifest_test_output_path(source_relative: str) -> tuple[str, str]:
    """Map a prepare.py source-relative test path to its processed/test path."""
    source_path = PurePosixPath(source_relative)
    if source_path.is_absolute() or ".." in source_path.parts:
        raise ManifestMismatchError(f"Ruta insegura en el manifiesto: {source_relative!r}")
    if len(source_path.parts) < 3 or source_path.parts[0] != "Testing":
        raise ManifestMismatchError(
            f"La ruta de test debe comenzar por Testing/<clase>/: {source_relative!r}"
        )
    raw_class = normalize_class_name(source_path.parts[1])
    canonical_class = SUBTYPE_TO_CLASS.get(raw_class)
    if canonical_class is None:
        raise ManifestMismatchError(f"Clase desconocida en la ruta del manifiesto: {source_relative!r}")
    output_name = "__".join(source_path.parts[-3:]).replace(" ", "_")
    return (PurePosixPath("test", canonical_class, output_name).as_posix(), canonical_class)


def verify_test_manifest(data_root: Path, test_dataset: Any, classes: list[str], *, required: bool = False) -> dict:
    """Verify the processed test file set and labels against splits.json.

    The manifest fingerprint is recorded verbatim; it is intentionally not
    recalculated because it describes source path assignments, not image bytes.
    """
    manifest_path = Path(data_root) / "splits.json"
    try:
        raw_manifest = manifest_path.read_bytes()
    except FileNotFoundError:
        if required:
            raise FileNotFoundError(f"Se requiere el manifiesto: {manifest_path}")
        return {
            "status": "unavailable",
            "reason": "splits.json no existe en la raíz de datos; no se verificó la partición.",
        }
    except OSError as exc:
        if required:
            raise PermissionError(f"No se pudo leer el manifiesto {manifest_path}: {exc}") from exc
        return {"status": "unavailable", "reason": f"No se pudo leer splits.json: {exc}"}

    try:
        manifest = json.loads(raw_manifest)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestMismatchError(f"splits.json no contiene JSON válido: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ManifestMismatchError("La raíz de splits.json debe ser un objeto JSON")
    if manifest.get("classes") != classes:
        raise ManifestMismatchError(
            f"Orden/clases del manifiesto incompatible: {manifest.get('classes')!r} != {classes!r}"
        )
    files = manifest.get("files")
    if not isinstance(files, dict) or not isinstance(files.get("test"), list):
        raise ManifestMismatchError("splits.json debe contener files.test como lista")

    all_split_entries: dict[str, list[str]] = {}
    for split_name in ("train", "val", "test"):
        split_files = files.get(split_name)
        if not isinstance(split_files, list) or not all(isinstance(item, str) for item in split_files):
            raise ManifestMismatchError(f"splits.json debe contener files.{split_name} como lista de rutas")
        duplicates = [path for path, count in Counter(split_files).items() if count > 1]
        if duplicates:
            raise ManifestMismatchError(f"Hay rutas duplicadas en files.{split_name}: {duplicates[:3]}")
        all_split_entries[split_name] = split_files
    train_paths = set(all_split_entries["train"])
    val_paths = set(all_split_entries["val"])
    test_paths = set(all_split_entries["test"])
    if (train_paths & val_paths) or (train_paths & test_paths) or (val_paths & test_paths):
        raise ManifestMismatchError("Hay rutas compartidas entre particiones en splits.json")

    expected: dict[str, str] = {}
    for source_relative in all_split_entries["test"]:
        output_relative, canonical_class = _manifest_test_output_path(source_relative)
        if output_relative in expected:
            raise ManifestMismatchError(
                f"Dos rutas del manifiesto colisionan en {output_relative!r}"
            )
        expected[output_relative] = canonical_class

    base_dataset = getattr(test_dataset, "base", None)
    samples = getattr(base_dataset, "samples", None)
    targets = getattr(test_dataset, "targets", None)
    if samples is None or targets is None or len(samples) != len(targets):
        raise ValueError("No se pudieron obtener rutas y etiquetas del test ImageFolder")
    root_resolved = Path(data_root).resolve()
    actual: dict[str, int] = {}
    for (sample_path, _folder_label), target in zip(samples, targets):
        try:
            relative = Path(sample_path).resolve().relative_to(root_resolved).as_posix()
        except ValueError as exc:
            raise ManifestMismatchError(f"Imagen de test fuera de data_root: {sample_path}") from exc
        if relative in actual:
            raise ManifestMismatchError(f"Ruta de test duplicada en ImageFolder: {relative}")
        actual[relative] = int(target)

    missing = sorted(set(expected) - set(actual))
    additional = sorted(set(actual) - set(expected))
    if missing or additional:
        raise ManifestMismatchError(
            f"El test procesado no coincide con el manifiesto: faltan={missing[:3]}, "
            f"adicionales={additional[:3]}"
        )
    label_mismatches = [
        relative for relative, canonical in expected.items()
        if actual[relative] != classes.index(canonical)
    ]
    if label_mismatches:
        raise ManifestMismatchError(
            f"Etiquetas del test no coinciden con el manifiesto: {label_mismatches[:3]}"
        )

    expected_counts = manifest.get("counts", {}).get("test", {})
    observed_counts = {name: 0 for name in classes}
    for canonical in expected.values():
        observed_counts[canonical] += 1
    normalized_counts = {name: int(expected_counts.get(name, 0)) for name in classes}
    if normalized_counts != observed_counts:
        raise ManifestMismatchError(
            f"Conteos de test inconsistentes: manifiesto={normalized_counts}, "
            f"rutas={observed_counts}"
        )

    return {
        "status": "verified",
        "manifest_path": "splits.json",
        "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
        "split_fingerprint": manifest.get("split_fingerprint"),
        "split_fingerprint_scope": manifest.get("split_fingerprint_scope"),
        "n_samples": len(actual),
        "counts_by_class": observed_counts,
        "path_comparison": "manifest source paths mapped to processed/test paths; image bytes not hashed",
    }


def _mean_defined(values: list[float | None], weights: list[int] | None = None) -> float | None:
    valid = [(index, value) for index, value in enumerate(values) if value is not None]
    if not valid:
        return None
    if weights is None:
        return float(sum(value for _, value in valid) / len(valid))
    total_weight = sum(weights[index] for index, _ in valid)
    if total_weight == 0:
        return None
    return float(sum(value * weights[index] for index, value in valid) / total_weight)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    classes: list[str],
    probabilities: np.ndarray | None = None,
) -> dict:
    """Compute multiclass metrics, preserving undefined values as null."""
    true = np.asarray(y_true, dtype=np.int64)
    pred = np.asarray(y_pred, dtype=np.int64)
    if true.ndim != 1 or pred.ndim != 1 or len(true) != len(pred):
        raise ValueError("y_true y y_pred deben ser vectores del mismo tamaño")
    if not classes or len(set(classes)) != len(classes):
        raise ValueError("La lista de clases debe ser no vacía y sin duplicados")
    if len(true) and (true.min() < 0 or pred.min() < 0 or true.max() >= len(classes) or pred.max() >= len(classes)):
        raise ValueError("Las etiquetas contienen índices fuera del orden de clases")

    matrix = confusion_matrix(true, pred, labels=list(range(len(classes))))
    supports = matrix.sum(axis=1).astype(int).tolist()
    predicted_supports = matrix.sum(axis=0).astype(int).tolist()
    per_class: dict[str, Any] = {}
    reasons: dict[str, str] = {}
    precisions: list[float | None] = []
    recalls: list[float | None] = []
    f1s: list[float | None] = []

    for index, name in enumerate(classes):
        tp = int(matrix[index, index])
        support = supports[index]
        predicted = predicted_supports[index]
        precision = float(tp / predicted) if predicted else None
        recall = float(tp / support) if support else None
        f1_denominator = 2 * tp + (predicted - tp) + (support - tp)
        f1 = float(2 * tp / f1_denominator) if f1_denominator else None
        per_class[name] = {
            "precision": precision,
            "recall": recall,
            "f1-score": f1,
            "support": support,
        }
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        if precision is None:
            reasons[f"per_class.{name}.precision"] = "no hay predicciones de esta clase"
        if recall is None:
            reasons[f"per_class.{name}.recall"] = "no hay ejemplos verdaderos de esta clase"
        if f1 is None:
            reasons[f"per_class.{name}.f1-score"] = "no hay ejemplos verdaderos ni predicciones de esta clase"

    n_samples = int(len(true))
    accuracy = float(np.trace(matrix) / n_samples) if n_samples else None
    if accuracy is None:
        reasons["accuracy"] = "el conjunto evaluado está vacío"
    macro_precision = _mean_defined(precisions)
    macro_recall = _mean_defined(recalls)
    macro_f1 = _mean_defined(f1s)
    weighted_precision = _mean_defined(precisions, supports)
    weighted_recall = _mean_defined(recalls, supports)
    weighted_f1 = _mean_defined(f1s, supports)

    per_class["accuracy"] = accuracy
    per_class["macro avg"] = {
        "precision": macro_precision, "recall": macro_recall, "f1-score": macro_f1,
        "support": n_samples,
    }
    per_class["weighted avg"] = {
        "precision": weighted_precision, "recall": weighted_recall, "f1-score": weighted_f1,
        "support": n_samples,
    }

    tumor_indices = [classes.index(name) for name in TUMOR_CLASSES if name in classes]
    tumor_recalls = [recalls[index] for index in tumor_indices]
    tumor_recall = (
        float(sum(value for value in tumor_recalls if value is not None) / len(tumor_recalls))
        if tumor_recalls and all(value is not None for value in tumor_recalls) else None
    )
    if tumor_recall is None:
        reasons["tumor_recall"] = "falta soporte verdadero para una o más clases tumorales"

    auc_by_class: dict[str, float | None] = {}
    if probabilities is None:
        reasons["roc_auc_macro_ovr"] = "no se proporcionaron probabilidades por clase"
        auc_by_class = {name: None for name in classes}
    else:
        probs = np.asarray(probabilities, dtype=np.float64)
        if probs.shape != (n_samples, len(classes)):
            raise ValueError(
                f"probabilities debe tener forma {(n_samples, len(classes))}, recibida {probs.shape}"
            )
        if not np.isfinite(probs).all():
            raise ValueError("probabilities contiene valores no finitos")
        for index, name in enumerate(classes):
            binary_true = (true == index).astype(np.int64)
            if binary_true.sum() == 0:
                auc_by_class[name] = None
                reasons[f"roc_auc_per_class.{name}"] = "no hay positivos verdaderos de esta clase"
            elif binary_true.sum() == n_samples:
                auc_by_class[name] = None
                reasons[f"roc_auc_per_class.{name}"] = "no hay negativos para el esquema one-vs-rest"
            else:
                try:
                    auc_by_class[name] = float(roc_auc_score(binary_true, probs[:, index]))
                except ValueError as exc:
                    auc_by_class[name] = None
                    reasons[f"roc_auc_per_class.{name}"] = str(exc)
        if all(value is not None for value in auc_by_class.values()):
            auc_macro = float(sum(value for value in auc_by_class.values() if value is not None) / len(classes))
        else:
            auc_macro = None
            reasons["roc_auc_macro_ovr"] = "no todas las clases tienen positivos y negativos para OVR"

    if weighted_precision is None and n_samples:
        reasons["weighted_precision"] = "no hay valores de precision definidos con soporte"
    if weighted_recall is None and n_samples:
        reasons["weighted_recall"] = "no hay valores de recall definidos con soporte"
    if weighted_f1 is None and n_samples:
        reasons["weighted_f1"] = "no hay valores de F1 definidos con soporte"

    return {
        "n_samples": n_samples,
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "tumor_recall": tumor_recall,
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_classes": list(classes),
        "per_class": per_class,
        "roc_auc_macro_ovr": auc_macro,
        "roc_auc_per_class": auc_by_class,
        "undefined_metric_reasons": reasons,
        "macro_aggregation_note": "promedio sobre clases con valor definido; weighted usa soporte verdadero",
    }


def logits_to_predictions(logits: np.ndarray, y_true: np.ndarray) -> tuple[np.ndarray, np.ndarray, float | None]:
    """Convert one evaluation's logits into predictions, probabilities and CE loss."""
    scores = np.asarray(logits, dtype=np.float64)
    true = np.asarray(y_true, dtype=np.int64)
    if scores.ndim != 2 or len(scores) != len(true):
        raise ValueError("logits debe ser una matriz con una fila por etiqueta verdadera")
    if not np.isfinite(scores).all():
        raise ValueError("logits contiene valores no finitos")
    if not len(true):
        return np.empty((0,), dtype=np.int64), np.empty_like(scores), None
    shifted = scores - scores.max(axis=1, keepdims=True)
    exp_scores = np.exp(shifted)
    probabilities = exp_scores / exp_scores.sum(axis=1, keepdims=True)
    if true.min() < 0 or true.max() >= scores.shape[1]:
        raise ValueError("y_true contiene índices fuera del número de logits")
    log_normalizer = np.log(np.exp(shifted).sum(axis=1)) + scores.max(axis=1)
    loss = float(np.mean(log_normalizer - scores[np.arange(len(true)), true]))
    return probabilities.argmax(axis=1).astype(np.int64), probabilities, loss


def _evaluate_logits(model: torch.nn.Module, loader: DataLoader, device: torch.device):
    model.eval()
    truths: list[np.ndarray] = []
    logits_rows: list[np.ndarray] = []
    with torch.no_grad():
        for images, labels in loader:
            logits = model(images.to(device))
            truths.append(labels.detach().cpu().numpy())
            logits_rows.append(logits.detach().cpu().numpy())
    if not truths:
        classes = len(getattr(loader.dataset, "classes", []))
        y_true = np.empty((0,), dtype=np.int64)
        logits = np.empty((0, classes), dtype=np.float64)
    else:
        y_true = np.concatenate(truths).astype(np.int64)
        logits = np.concatenate(logits_rows)
    y_pred, probabilities, loss = logits_to_predictions(logits, y_true)
    return y_true, y_pred, probabilities, loss, logits


@torch.no_grad()
def predict_all(model: torch.nn.Module, loader: DataLoader, device: torch.device):
    """Backward-compatible prediction API; the evaluator also retains logits loss."""
    y_true, y_pred, probabilities, _loss, _logits = _evaluate_logits(model, loader, device)
    if not len(y_true):
        raise ValueError("El conjunto de evaluación está vacío")
    return y_true, y_pred, probabilities


@torch.no_grad()
def evaluate_all(model: torch.nn.Module, loader: DataLoader, device: torch.device):
    y_true, y_pred, probabilities, loss, logits = _evaluate_logits(model, loader, device)
    if not len(y_true):
        raise ValueError("El conjunto de evaluación está vacío")
    return y_true, y_pred, probabilities, loss, logits


@torch.no_grad()
def measure_inference_time(model: torch.nn.Module, loader: DataLoader, device: torch.device, warmup: int = 5) -> float:
    import time

    batches = []
    for index, (images, _) in enumerate(loader):
        batches.append(images.to(device))
        if index == warmup:
            break
    if not batches:
        raise ValueError("No se puede medir inferencia con un conjunto vacío")
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


def count_parameters(model: torch.nn.Module) -> tuple[int, None]:
    """Return total parameters; original trainable count is not stored reliably."""
    return sum(parameter.numel() for parameter in model.parameters()), None


def checkpoint_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def preprocessing_metadata(config: dict[str, Any]) -> dict[str, Any]:
    size = int(config["input"]["size"])
    normalization = config["normalization"]
    return {
        "input_size": size,
        "normalization": {
            "mode": normalization["mode"],
            "mean": list(normalization["mean"]),
            "std": list(normalization["std"]),
        },
        "transforms": [
            {"name": "RGB", "source": "torchvision.datasets.ImageFolder PIL loader"},
            {"name": "Resize", "size": [size, size], "interpolation": "bilinear (torchvision default)"},
            {"name": "ToTensor", "scale": "uint8 [0,255] to float [0,1]"},
            {"name": "Normalize", "mean": list(normalization["mean"]), "std": list(normalization["std"])},
        ],
    }


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {"python": platform.python_version()}
    for package, distribution in (
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("scikit_learn", "scikit-learn"),
        ("Pillow", "Pillow"),
    ):
        try:
            versions[package] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def prediction_payload(
    *, run_id: str, model_name: str, architecture: str, checkpoint_sha256: str,
    classes: list[str], y_true: np.ndarray, y_pred: np.ndarray,
    probabilities: np.ndarray, identifiers: list[str],
) -> dict[str, Any]:
    if not (len(y_true) == len(y_pred) == len(probabilities) == len(identifiers)):
        raise ValueError("Las predicciones, probabilidades, etiquetas e identificadores no tienen igual longitud")
    rows = []
    for index, identifier in enumerate(identifiers):
        if Path(identifier).is_absolute() or ".." in PurePosixPath(identifier).parts:
            raise ValueError(f"Identificador de predicción no relativo/estable: {identifier!r}")
        rows.append({
            "id": PurePosixPath(identifier).as_posix(),
            "y_true": classes[int(y_true[index])],
            "y_pred": classes[int(y_pred[index])],
            "probabilities": {name: float(probabilities[index, class_index])
                              for class_index, name in enumerate(classes)},
        })
    return {
        "schema_version": 1,
        "run_id": run_id,
        "model": model_name,
        "architecture": architecture,
        "split": "test",
        "checkpoint_sha256": checkpoint_sha256,
        "classes": list(classes),
        "class_to_idx": {name: index for index, name in enumerate(classes)},
        "n_samples": len(rows),
        "predictions": rows,
    }


def _write_json_exclusive(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
    return path


def save_report(model_name: str, payload: dict, reports_dir: Path = REPORTS_DIR) -> Path:
    return _write_json_exclusive(Path(reports_dir) / f"{model_name}_metrics.json", payload)


def save_predictions(model_name: str, payload: dict, reports_dir: Path = REPORTS_DIR) -> Path:
    return _write_json_exclusive(Path(reports_dir) / f"{model_name}_predictions.json", payload)


def _relative_path(path: Path, base: Path) -> str:
    return Path(os.path.relpath(path.resolve(), base.resolve())).as_posix()


def main() -> None:
    from dataloader import build_dataloaders
    from model_factory import MODEL_SPECS, build_model
    from train import resolve_device

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, choices=MODEL_NAMES)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--data-root", type=Path, default=None,
                        help="Raíz processed/ (por defecto ml/data/processed)")
    parser.add_argument("--reports-dir", type=Path, default=None,
                        help="Directorio de salida; por defecto se crea una corrida única")
    parser.add_argument("--run-id", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--require-manifest", action="store_true",
                        help="Detiene la evaluación si splits.json no está disponible o no coincide")
    args = parser.parse_args()

    architecture = args.model
    config = load_config(args.model)
    classes = load_classes()
    data_root = (args.data_root or PROCESSED_DIR).resolve()
    weights_path = args.weights.resolve()
    if not weights_path.is_file():
        raise FileNotFoundError(f"No existe el checkpoint: {weights_path}")
    run_id = args.run_id or new_run_id()
    if args.reports_dir is None:
        reports_dir = REPORTS_DIR / "runs" / run_id
    else:
        reports_dir = args.reports_dir.resolve()
    metrics_output = reports_dir / f"{args.model}_metrics.json"
    predictions_output = reports_dir / f"{args.model}_predictions.json"
    existing_outputs = [path for path in (metrics_output, predictions_output) if path.exists()]
    if existing_outputs:
        raise FileExistsError(f"La corrida no reemplaza informes existentes: {existing_outputs}")

    device = resolve_device("auto")
    checkpoint_hash = sha256_file(weights_path)
    try:
        checkpoint = torch.load(weights_path, map_location=device, weights_only=True)
    except TypeError as exc:
        raise RuntimeError(
            "Esta versión de PyTorch no admite carga weights_only=True; "
            "actualiza el entorno de evaluación de forma controlada. No se usó carga insegura."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"No se pudo cargar el checkpoint en modo seguro (weights_only=True): {exc}"
        ) from exc

    class_to_idx = validate_checkpoint_metadata(checkpoint, architecture, classes, config)
    model = build_model(architecture, num_classes=len(classes), pretrained=False)
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.to(device)

    train_loader, val_loader, test_loader = build_dataloaders(
        args.model, root=data_root, batch_size=args.batch_size
    )
    del train_loader, val_loader
    manifest_info = verify_test_manifest(
        data_root, test_loader.dataset, classes, required=args.require_manifest
    )
    y_true, y_pred, probabilities, test_loss, _logits = evaluate_all(model, test_loader, device)
    metrics = compute_metrics(y_true, y_pred, classes, probabilities)
    metrics["loss"] = test_loss
    if test_loss is None:
        metrics["undefined_metric_reasons"]["loss"] = "el conjunto evaluado está vacío"
    ms_per_image = measure_inference_time(model, test_loader, device)
    total_params, _original_trainable_params = count_parameters(model)

    base_dataset = test_loader.dataset.base
    identifiers = [
        Path(path).resolve().relative_to(data_root).as_posix()
        for path, _target in base_dataset.samples
    ]
    checkpoint_relative = _relative_path(weights_path, REPO_ROOT)
    data_root_relative = _relative_path(data_root, REPO_ROOT)
    timestamp = datetime.now(timezone.utc).isoformat()
    prep = preprocessing_metadata(config)
    common = {
        "schema_version": 1,
        "run_id": run_id,
        "evaluated_at": timestamp,
        "model": args.model,
        "architecture": architecture,
        "checkpoint_path": checkpoint_relative,
        "checkpoint_sha256": checkpoint_hash,
        "split": "test",
        "data_root": data_root_relative,
        "n_samples": len(y_true),
        "classes": list(classes),
        "class_to_idx": class_to_idx,
        "preprocessing": prep,
        "versions": package_versions(),
        "manifest": manifest_info,
        "test_set_caveat": (
            "Evaluacion comparativa actualizada: Testing ya intervino en la seleccion previa "
            "de arquitectura y no es una prueba final independiente."
        ),
    }
    report = {
        **common,
        **metrics,
        "best_val_accuracy": checkpoint.get("val_accuracy"),
        "checkpoint_epoch": checkpoint.get("epoch"),
        "ms_per_image": ms_per_image,
        "num_parameters": total_params,
        "num_parameters_m": round(total_params / 1e6, 3),
        "checkpoint_mb": round(checkpoint_size_mb(weights_path), 3),
    }
    predictions = prediction_payload(
        run_id=run_id,
        model_name=args.model,
        architecture=architecture,
        checkpoint_sha256=checkpoint_hash,
        classes=classes,
        y_true=y_true,
        y_pred=y_pred,
        probabilities=probabilities,
        identifiers=identifiers,
    )
    predictions.update({
        "evaluated_at": timestamp,
        "checkpoint_path": checkpoint_relative,
        "data_root": data_root_relative,
        "manifest": manifest_info,
    })
    metrics_path = save_report(args.model, report, reports_dir=reports_dir)
    predictions_path = save_predictions(args.model, predictions, reports_dir=reports_dir)

    print(f"accuracy      = {metrics['accuracy']}")
    print(f"macro F1      = {metrics['macro_f1']}")
    print(f"weighted F1   = {metrics['weighted_f1']}")
    print(f"ROC-AUC macro = {metrics['roc_auc_macro_ovr']}")
    print(f"loss          = {metrics['loss']}")
    print(f"checkpoint    = {checkpoint_relative} ({checkpoint_hash})")
    print(f"manifest      = {manifest_info['status']}")
    print(f"metrics       = {metrics_path}")
    print(f"predictions   = {predictions_path}")


if __name__ == "__main__":
    main()
