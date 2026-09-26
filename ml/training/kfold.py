"""Validacion cruzada estratificada de 5 folds (OE4).

Uso:
    python kfold.py --model mobilenetv3
    python kfold.py --model resnet18 --folds 5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import Subset

from dataloader import build_datasets
from dataset.preprocessing import load_classes, load_config

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "ml" / "evaluation" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--folds", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def build_folds(dataset, n_splits: int, seed: int) -> list[tuple[list[int], list[int]]]:
    targets = np.asarray(dataset.targets)
    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(splitter.split(np.zeros(len(targets)), targets))


def run(model_name: str, n_splits: int, seed: int) -> dict:
    config = load_config(model_name)
    train_ds, _, _ = build_datasets(model_name)
    splits = build_folds(train_ds, n_splits, seed)

    print(f"[{model_name}] {len(train_ds)} imagenes, {n_splits} folds estratificados")
    for fold, (train_idx, val_idx) in enumerate(splits):
        train_counts = np.bincount(np.asarray(train_ds.targets)[train_idx], minlength=4)
        val_counts = np.bincount(np.asarray(train_ds.targets)[val_idx], minlength=4)
        print(f"  fold {fold}: train={train_counts.tolist()} val={val_counts.tolist()}")
        print(f"    indices guardados en reports/{model_name}_fold{fold}_split.npy")
        np.save(REPORTS_DIR / f"{model_name}_fold{fold}_train_idx.npy", train_idx)
        np.save(REPORTS_DIR / f"{model_name}_fold{fold}_val_idx.npy", val_idx)

    return {
        "model": model_name,
        "role": config["role"],
        "n_splits": n_splits,
        "seed": seed,
        "classes": load_classes(),
    }


def aggregate(fold_metrics: list[dict]) -> dict:
    """Media y desviacion de cada metrica a traves de los folds."""
    keys = [k for k in fold_metrics[0] if k not in {"confusion_matrix", "per_class"}]
    summary = {}
    for key in keys:
        values = np.asarray([m[key] for m in fold_metrics], dtype=float)
        summary[key] = {"mean": float(values.mean()), "std": float(values.std())}
    matrix = np.sum([m["confusion_matrix"] for m in fold_metrics], axis=0)
    summary["confusion_matrix"] = matrix.tolist()
    return summary


def main() -> None:
    args = parse_args()
    config = load_config(args.model)
    validation = config["validation"]
    n_splits = args.folds or validation["k_folds"]
    seed = args.seed or validation["seed"]

    if not validation["stratified"]:
        raise NotImplementedError("La validacion no estratificada no esta contemplada")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = run(args.model, n_splits, seed)
    (REPORTS_DIR / f"{args.model}_folds.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"[{args.model}] manifest de folds escrito en {REPORTS_DIR}")

    print(
        "Ahora ejecutar train.py --model "
        f"{args.model} --fold <0..{n_splits - 1}> y evaluar con metrics.py"
    )


def make_subsets(dataset, train_idx: list[int], val_idx: list[int]) -> tuple[Subset, Subset]:
    return Subset(dataset, train_idx), Subset(dataset, val_idx)


if __name__ == "__main__":
    main()
