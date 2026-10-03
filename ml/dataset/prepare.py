"""Preparacion reproducible del dataset con splits compartidos.

Genera UNA particion train/val/test estratificada que usan los cinco modelos,
para que la comparacion sea justa: mismas imagenes, mismos labels, mismo orden
de clases. No se duplica el dataset por modelo.

Estructura de salida::

    processed/
        train/ | val/ | test/
            glioma/  meningioma/  pituitario/  no_tumor/

Uso:
    python ml/dataset/prepare.py --source ml/dataset/raw/saeedi2023 --dest ml/dataset/processed
    python ml/dataset/prepare.py --source <dir> --dest <dir> --seed 42

El dataset principal es saeedi2023 (3264 imagenes, 4 clases nativas, el del
articulo base). Si la fuente es nickparvar2024 (7023 imagenes con
subcategorias), los nombres se normalizan a las 4 clases canonicas de
ml/configs/labels.json mediante SUBTYPE_TO_CLASS de download.py.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from download import SUBTYPE_TO_CLASS, is_valid_image, normalize_class_name  # noqa: E402

CANONICAL_CLASSES = ["glioma", "meningioma", "pituitario", "no_tumor"]
SPLITS = ("train", "val", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Directorio con las imagenes crudas (tras extraer el ZIP)")
    parser.add_argument("--dest", type=Path, required=True,
                        help="Directorio de salida, p. ej. ml/dataset/processed")
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--overwrite", action="store_true",
                        help="Vaciar --dest si ya existe")
    return parser.parse_args()


def collect_images(source: Path) -> tuple[dict[str, list[Path]], Counter]:
    """Agrupa imagenes validas por clase canonica. Omite nombres desconocidos."""
    by_class: dict[str, list[Path]] = {c: [] for c in CANONICAL_CLASSES}
    skipped = Counter()
    for path in sorted(source.rglob("*")):
        if not path.is_file() or not is_valid_image(path):
            continue
        raw_class = normalize_class_name(path.parent.name)
        target = SUBTYPE_TO_CLASS.get(raw_class)
        if target is None:
            skipped[raw_class] += 1
            continue
        by_class[target].append(path)
    return by_class, skipped


def stratified_split(paths: list[Path], train_ratio: float, val_ratio: float,
                      seed: int) -> dict[str, list[Path]]:
    """Particion estratificada por clase con seed fijo. Sin data leakage:
    cada archivo va a un unico split."""
    import numpy as np

    rng = np.random.default_rng(seed)
    indices = np.arange(len(paths))
    rng.shuffle(indices)
    n = len(paths)
    n_train = int(round(n * train_ratio))
    n_val = int(round(n * val_ratio))
    return {
        "train": [paths[i] for i in indices[:n_train]],
        "val": [paths[i] for i in indices[n_train:n_train + n_val]],
        "test": [paths[i] for i in indices[n_train + n_val:]],
    }


def unique_name(path: Path) -> str:
    """Nombre estable y unico: aplana la ruta relativa para evitar colisiones
    cuando dos subcarpetas traen el mismo nombre de archivo."""
    return "__".join(path.parts[-3:]).replace(" ", "_")


def prepare(source: Path, dest: Path, train_ratio: float = 0.70,
            val_ratio: float = 0.15, test_ratio: float = 0.15,
            seed: int = 42, overwrite: bool = False) -> dict:
    if not source.is_dir():
        raise FileNotFoundError(f"Fuente inexistente: {source}")
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-9:
        raise ValueError("Los ratios deben sumar 1.0")
    if dest.exists() and any(dest.iterdir()) and not overwrite:
        raise FileExistsError(f"{dest} no esta vacio; usar --overwrite para regenerar")
    if overwrite and dest.exists():
        shutil.rmtree(dest)

    by_class, skipped = collect_images(source)
    for cls, paths in by_class.items():
        if not paths:
            raise ValueError(f"Clase '{cls}' sin imagenes en {source}")

    manifest: dict = {
        "source": str(source),
        "seed": seed,
        "ratios": {"train": train_ratio, "val": val_ratio, "test": test_ratio},
        "classes": CANONICAL_CLASSES,
        "counts": {s: {} for s in SPLITS},
        "total": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    for cls, paths in by_class.items():
        # Seed por clase derivado del global: misma particion global,
        # reproducible y estratificada por construccion.
        parts = stratified_split(paths, train_ratio, val_ratio, seed + hash(cls) % (2 ** 31))
        for split, subset in parts.items():
            out_dir = dest / split / cls
            out_dir.mkdir(parents=True, exist_ok=True)
            for path in subset:
                shutil.copy2(path, out_dir / unique_name(path))
            manifest["counts"][split][cls] = len(subset)
            manifest["total"] += len(subset)
    if skipped:
        manifest["skipped_unknown_classes"] = dict(skipped)

    (dest / "splits.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def report(manifest: dict) -> str:
    lines = [f"Total: {manifest['total']} imagenes (seed={manifest['seed']})"]
    header = f"{'clase':<12}" + "".join(f"{s:>10}" for s in SPLITS)
    lines.append(header)
    for cls in CANONICAL_CLASSES:
        lines.append(f"{cls:<12}" + "".join(f"{manifest['counts'][s][cls]:>10}" for s in SPLITS))
    if manifest.get("skipped_unknown_classes"):
        lines.append(f"Omitidas (clase desconocida): {manifest['skipped_unknown_classes']}")
    lines.append(f"Manifiesto: splits.json en destino")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    manifest = prepare(args.source, args.dest, args.train_ratio, args.val_ratio,
                       args.test_ratio, args.seed, args.overwrite)
    print(report(manifest))


if __name__ == "__main__":
    main()
