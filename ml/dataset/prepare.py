"""Prepare reproducible train/validation/test splits without changing raw data.

Only ``Training/`` is split, using the approved global ``torch.randperm``
protocol. ``Testing/`` is copied intact to the independent test split.

The fingerprint in ``splits.json`` hashes split assignments and source-relative
paths; it does not hash the binary contents of the images.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

_HERE = Path(__file__).resolve().parent
_ML_DIR = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from download import SUPPORTED_EXTENSIONS, SUBTYPE_TO_CLASS, normalize_class_name  # noqa: E402

LABELS_PATH = _ML_DIR / "configs" / "labels.json"
EXPECTED_RAW_CLASS_MAP = {
    "glioma": "glioma",
    "meningioma": "meningioma",
    "notumor": "no_tumor",
    "pituitary": "pituitario",
}
EXPECTED_COUNTS = {
    "Training": {raw: 1400 for raw in EXPECTED_RAW_CLASS_MAP},
    "Testing": {raw: 400 for raw in EXPECTED_RAW_CLASS_MAP},
}
TRAIN_RATIO = 0.80
SPLITS = ("train", "val", "test")


def load_canonical_classes() -> list[str]:
    """Load and validate the project's canonical label order."""
    with LABELS_PATH.open(encoding="utf-8") as stream:
        labels = json.load(stream)
    classes = labels.get("classes")
    if not isinstance(classes, list) or not classes or not all(
        isinstance(name, str) and name for name in classes
    ):
        raise ValueError(f"Contrato de clases inválido en {LABELS_PATH}: 'classes'")
    expected_indices = {name: index for index, name in enumerate(classes)}
    if len(expected_indices) != len(classes):
        raise ValueError(f"Hay etiquetas duplicadas en {LABELS_PATH}")
    if labels.get("num_classes") != len(classes):
        raise ValueError(f"num_classes no coincide con classes en {LABELS_PATH}")
    if labels.get("label_to_index") != expected_indices:
        raise ValueError(f"label_to_index no respeta el orden de classes en {LABELS_PATH}")
    return list(classes)


CANONICAL_CLASSES = load_canonical_classes()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=_ML_DIR / "data" / "raw",
        help="Raíz con Training/ y Testing/ (por defecto ml/data/raw)",
    )
    parser.add_argument(
        "--dest", type=Path, default=_ML_DIR / "data" / "processed",
        help="Directorio de salida (por defecto ml/data/processed)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Reemplaza el destino existente solo después de validar y preparar la salida",
    )
    return parser.parse_args()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def paths_overlap(first: Path, second: Path) -> bool:
    """Whether resolved paths are equal or one contains the other."""
    return _is_within(first, second) or _is_within(second, first)


def validate_paths(source: Path, dest: Path) -> tuple[Path, Path]:
    """Resolve paths and ensure output cannot touch any part of the source tree."""
    source = Path(source).resolve(strict=True)
    requested_dest = Path(dest)
    if requested_dest.is_symlink():
        raise ValueError(f"No se admite un destino que sea enlace simbólico: {requested_dest}")
    dest = requested_dest.resolve(strict=False)
    if paths_overlap(source, dest):
        raise ValueError(
            f"El destino {dest} se solapa con la fuente {source}; "
            "debe ser una ruta independiente de Training/, Testing/ y sus directorios superiores"
        )
    if dest.exists() and not dest.is_dir():
        raise NotADirectoryError(f"El destino existe y no es un directorio: {dest}")
    return source, dest


def validate_class_contract() -> None:
    if len(CANONICAL_CLASSES) != 4:
        raise ValueError(
            f"Se requieren cuatro clases canónicas en {LABELS_PATH}; se encontraron {CANONICAL_CLASSES}"
        )
    for raw_name, canonical_name in EXPECTED_RAW_CLASS_MAP.items():
        mapped = SUBTYPE_TO_CLASS.get(normalize_class_name(raw_name))
        if canonical_name not in CANONICAL_CLASSES or mapped != canonical_name:
            raise ValueError(
                f"Discrepancia de etiquetas: {raw_name!r} debe mapear a {canonical_name!r}; "
                f"labels.json={CANONICAL_CLASSES}, mapeo actual={mapped!r}"
            )


def _validate_image(path: Path) -> str | None:
    """Return a diagnostic for a file that cannot be fully decoded as an image."""
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return f"extensión no admitida ({path.suffix or 'sin extensión'})"
    try:
        with Image.open(path) as image:
            image.verify()
        # verify() checks the file structure but does not necessarily decode all pixels.
        with Image.open(path) as image:
            image.load()
    except (OSError, EOFError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        return f"imagen ilegible ({type(exc).__name__}: {exc})"
    return None


def collect_images(
    split_root: Path,
) -> tuple[dict[str, list[Path]], Counter, Counter, list[str]]:
    """Collect readable supported images and report every unexpected file."""
    by_class: dict[str, list[Path]] = {name: [] for name in CANONICAL_CLASSES}
    raw_counts: Counter = Counter()
    canonical_counts: Counter = Counter()
    issues: list[str] = []

    expected_raw = set(EXPECTED_RAW_CLASS_MAP)
    found_raw: dict[str, Path] = {}
    for child in split_root.iterdir():
        if not child.is_dir():
            continue
        raw_name = normalize_class_name(child.name)
        if raw_name in found_raw:
            issues.append(f"Directorios de clase duplicados tras normalizar: {found_raw[raw_name]} y {child}")
        found_raw[raw_name] = child
        if raw_name not in expected_raw:
            issues.append(f"Directorio de clase desconocido: {child}")
    for raw_name in sorted(expected_raw - set(found_raw)):
        issues.append(f"Falta el directorio de clase esperado: {split_root / raw_name}")

    for path in sorted(split_root.rglob("*")):
        if path.is_symlink():
            issues.append(f"Archivo o directorio simbólico no admitido: {path}")
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(split_root)
        raw_name = normalize_class_name(relative.parts[0]) if len(relative.parts) > 1 else ""
        canonical = SUBTYPE_TO_CLASS.get(raw_name)
        if raw_name not in expected_raw:
            issues.append(f"Clase desconocida para el archivo {path}: {raw_name or '(sin carpeta de clase)'}")

        image_issue = _validate_image(path)
        if image_issue:
            issues.append(f"{path}: {image_issue}")
            continue
        if raw_name not in expected_raw or canonical not in CANONICAL_CLASSES:
            continue

        by_class[canonical].append(path)
        raw_counts[raw_name] += 1
        canonical_counts[canonical] += 1

    return by_class, raw_counts, canonical_counts, issues


def split_training(
    paths: list[tuple[str, Path]], train_ratio: float, seed: int
) -> dict[str, list[tuple[str, Path]]]:
    """Apply the approved global randperm split; Testing is not involved."""
    import torch

    permutation = torch.randperm(
        len(paths), generator=torch.Generator().manual_seed(seed)
    ).tolist()
    n_train = int(round(len(paths) * train_ratio))
    return {
        "train": [paths[index] for index in permutation[:n_train]],
        "val": [paths[index] for index in permutation[n_train:]],
    }


def unique_name(path: Path) -> str:
    """Flatten path suffix into a stable filename; callers must check collisions."""
    return "__".join(path.parts[-3:]).replace(" ", "_")


def _validate_counts(
    root: Path, split_name: str, raw_counts: Counter, issues: list[str]
) -> None:
    for raw_name, expected_count in EXPECTED_COUNTS[split_name].items():
        detected = raw_counts[raw_name]
        if detected != expected_count:
            issues.append(
                f"Conteo incorrecto en {root / raw_name} (clase {raw_name}): "
                f"esperado {expected_count}, detectado {detected}"
            )


def _validate_partition(
    training_files: list[tuple[str, Path]],
    testing_files: list[tuple[str, Path]],
    partitions: dict[str, list[tuple[str, Path]]],
) -> None:
    expected_training = Counter(path.resolve() for _, path in training_files)
    assigned_training = Counter(
        path.resolve() for split in ("train", "val") for _, path in partitions[split]
    )
    if assigned_training != expected_training or any(count != 1 for count in assigned_training.values()):
        raise RuntimeError("La partición no asigna cada imagen de Training exactamente una vez a train o val")

    testing_paths = {path.resolve() for _, path in testing_files}
    if testing_paths & set(assigned_training):
        raise RuntimeError("Se detectó fuga: una ruta de Testing aparece en train o val")
    if len(testing_paths) != len(testing_files):
        raise RuntimeError("Hay rutas de Testing duplicadas")


def _plan_outputs(
    partitions: dict[str, list[tuple[str, Path]]],
    testing_by_class: dict[str, list[Path]],
) -> dict[str, list[tuple[str, Path, str]]]:
    planned: dict[str, list[tuple[str, Path, str]]] = {split: [] for split in SPLITS}
    owners: dict[tuple[str, str, str], Path] = {}
    for split in ("train", "val"):
        for class_name, path in partitions[split]:
            planned[split].append((class_name, path, unique_name(path)))
    for class_name, paths in testing_by_class.items():
        planned["test"].extend((class_name, path, unique_name(path)) for path in paths)

    for split, entries in planned.items():
        for class_name, path, output_name in entries:
            # The processed tree is commonly consumed on Windows, where file
            # names are case-insensitive. Treat case-only differences as a collision.
            key = (split.casefold(), class_name.casefold(), output_name.casefold())
            if key in owners:
                raise ValueError(
                    f"Colisión de nombre en {split}/{class_name}/{output_name}: "
                    f"{owners[key]} y {path} generarían el mismo archivo de destino"
                )
            owners[key] = path
    return planned


def _existing_payload(dest: Path) -> list[Path]:
    if not dest.exists():
        return []
    return [
        path for path in dest.rglob("*")
        if path.is_dir() or path.is_symlink() or (path.is_file() and path.name != ".gitkeep")
    ]


def _copy_placeholders(dest: Path, staging: Path) -> None:
    if not dest.exists():
        return
    for placeholder in dest.rglob(".gitkeep"):
        if placeholder.is_symlink():
            raise ValueError(f"No se admite un .gitkeep simbólico en el destino: {placeholder}")
        if placeholder.is_file():
            relative = placeholder.relative_to(dest)
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(placeholder, target)


def _publish(staging: Path, dest: Path) -> None:
    """Publish a complete staging directory, rolling back an old destination on failure."""
    backup_container: Path | None = None
    backup: Path | None = None
    if dest.exists():
        backup_container = Path(tempfile.mkdtemp(prefix=f".{dest.name}.backup-", dir=dest.parent))
        backup = backup_container / "previous"
        try:
            os.replace(dest, backup)
        except Exception:
            shutil.rmtree(backup_container, ignore_errors=True)
            raise

    try:
        os.replace(staging, dest)
    except Exception as publish_error:
        if backup is not None and backup.exists():
            try:
                os.replace(backup, dest)
            except Exception as restore_error:
                raise RuntimeError(
                    f"Publicación fallida y no se pudo restaurar el destino anterior. "
                    f"Los datos anteriores se conservan en {backup}"
                ) from restore_error
        if backup_container is not None:
            shutil.rmtree(backup_container, ignore_errors=True)
        raise publish_error

    if backup_container is not None:
        try:
            shutil.rmtree(backup_container)
        except OSError as exc:
            warnings.warn(
                f"La salida se publicó, pero no se pudo limpiar el respaldo {backup_container}: {exc}",
                RuntimeWarning,
            )


def prepare(source: Path, dest: Path, seed: int = 42, overwrite: bool = False) -> dict:
    source, dest = validate_paths(source, dest)
    training_root = source / "Training"
    testing_root = source / "Testing"
    if not training_root.is_dir() or not testing_root.is_dir():
        raise ValueError(f"Se requieren las carpetas Training/ y Testing/ en {source}")
    if training_root.is_symlink() or testing_root.is_symlink():
        raise ValueError("Training/ y Testing/ no pueden ser enlaces simbólicos")
    validate_class_contract()

    payload = _existing_payload(dest)
    if payload and not overwrite:
        raise FileExistsError(
            f"{dest} contiene archivos o directorios existentes; usa --overwrite explícitamente"
        )

    train_by_class, train_raw_counts, _, train_issues = collect_images(training_root)
    test_by_class, test_raw_counts, _, test_issues = collect_images(testing_root)
    issues = train_issues + test_issues
    _validate_counts(training_root, "Training", train_raw_counts, issues)
    _validate_counts(testing_root, "Testing", test_raw_counts, issues)
    if issues:
        details = "\n".join(f" - {issue}" for issue in issues)
        raise ValueError(
            f"Validación de entrada fallida ({len(issues)} problema(s)); no se preparó la salida:\n{details}"
        )

    train_files = sorted(
        ((class_name, path) for class_name, paths in train_by_class.items() for path in paths),
        key=lambda item: str(item[1]).lower(),
    )
    testing_files = sorted(
        ((class_name, path) for class_name, paths in test_by_class.items() for path in paths),
        key=lambda item: str(item[1]).lower(),
    )
    partitions = split_training(train_files, TRAIN_RATIO, seed)
    _validate_partition(train_files, testing_files, partitions)
    planned = _plan_outputs(partitions, test_by_class)

    # Build and verify everything beside dest before publishing it.
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{dest.name}.staging-", dir=dest.parent))
    try:
        _copy_placeholders(dest, staging)
        manifest: dict = {
            "source": str(source),
            "seed": seed,
            "ratios": {"train": TRAIN_RATIO, "val": 1.0 - TRAIN_RATIO},
            "test_source": "Testing/ (completo)",
            "classes": CANONICAL_CLASSES,
            "counts": {split: {name: 0 for name in CANONICAL_CLASSES} for split in SPLITS},
            "files": {split: [] for split in SPLITS},
            "total": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for split, entries in planned.items():
            for class_name, path, output_name in entries:
                output_path = staging / split / class_name / output_name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, output_path)
                manifest["counts"][split][class_name] += 1
                manifest["files"][split].append(path.relative_to(source).as_posix())
                manifest["total"] += 1

        if manifest["counts"]["test"] != test_raw_counts_as_canonical(test_by_class):
            raise RuntimeError("La salida test no conserva todas las imágenes esperadas por clase")
        if manifest["total"] != sum(len(paths) for paths in train_by_class.values()) + sum(
            len(paths) for paths in test_by_class.values()
        ):
            raise RuntimeError("El total de archivos publicados no coincide con las entradas validadas")

        fingerprint = hashlib.sha256()
        for split in SPLITS:
            for relative_path in sorted(manifest["files"][split]):
                fingerprint.update(f"{split}:{relative_path}\n".encode("utf-8"))
        manifest["split_fingerprint"] = fingerprint.hexdigest()
        manifest["split_fingerprint_scope"] = (
            "SHA-256 de las asignaciones split/ruta relativa de origen; no incluye el contenido binario de las imágenes."
        )
        (staging / "splits.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        _publish(staging, dest)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    return manifest


def test_raw_counts_as_canonical(testing_by_class: dict[str, list[Path]]) -> dict[str, int]:
    return {
        canonical: sum(
            len(paths) for raw_name, paths in testing_by_class.items()
            if SUBTYPE_TO_CLASS.get(raw_name) == canonical
        )
        for canonical in CANONICAL_CLASSES
    }


def report(manifest: dict) -> str:
    lines = [f"Total: {manifest['total']} imágenes (seed={manifest['seed']})"]
    header = f"{'clase':<12}" + "".join(f"{split:>10}" for split in SPLITS)
    lines.append(header)
    for class_name in CANONICAL_CLASSES:
        lines.append(
            f"{class_name:<12}"
            + "".join(f"{manifest['counts'][split][class_name]:>10}" for split in SPLITS)
        )
    lines.append("Manifiesto: splits.json en destino")
    lines.append("Fingerprint: asignaciones de rutas, no contenido binario de imágenes")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    manifest = prepare(args.source, args.dest, args.seed, args.overwrite)
    print(report(manifest))


if __name__ == "__main__":
    raise SystemExit(main())
