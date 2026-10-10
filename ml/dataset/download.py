"""Descarga y organizacion del dataset de MRI cerebral."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from PIL import Image

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

DATASETS = {
    "saeedi2023": {
        "description": "Saeedi et al. 2023, 3264 imagenes, 4 clases",
        "size_images": 3264,
    },
    "nickparvar2024": {
        "description": "Masoud Nickparvar, 7023 imagenes, 4 clases + subcategorias",
        "size_images": 7023,
    },
}

SUBTYPE_TO_CLASS = {
    # Nombres canonicos (p. ej. saeedi2023 ya trae estas 4 carpetas): identidad.
    "glioma": "glioma",
    "meningioma": "meningioma",
    "pituitario": "pituitario",
    "no_tumor": "no_tumor",
    "glioma_tumor": "glioma",
    "glioma_a": "glioma",
    "glioma_b": "glioma",
    "glioma_c": "glioma",
    "glioma_d": "glioma",
    "glioma_e": "glioma",
    "meningioma": "meningioma",
    "notumor": "no_tumor",
    "no_tumor": "no_tumor",
    "normal": "no_tumor",
    "pituitary": "pituitario",
    "pituitary_tumor": "pituitario",
}

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--archive", type=Path, required=True, help="ZIP descargado de Kaggle")
    parser.add_argument("--dest", type=Path, default=RAW_DIR)
    parser.add_argument("--flatten", action="store_true", help="Colapsar subcarpetas a 4 clases")
    return parser.parse_args()


def extract(archive: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)
    return dest


def normalize_class_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def is_valid_image(path: Path) -> bool:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False
    try:
        with Image.open(path) as img:
            img.verify()
    except (OSError, ValueError):
        return False
    return True


def flatten(source: Path, dest: Path) -> int:
    """Reorganiza las subcarpetas de glioma en la clase unica glioma."""
    count = 0
    for path in sorted(source.rglob("*")):
        if not path.is_file() or not is_valid_image(path):
            continue
        raw_class = normalize_class_name(path.parent.name)
        target_class = SUBTYPE_TO_CLASS.get(raw_class)
        if target_class is None:
            continue
        target_dir = dest / target_class
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / path.name).write_bytes(path.read_bytes())
        count += 1
    return count


def main() -> None:
    args = parse_args()
    extracted = extract(args.archive, args.dest / args.dataset / "original")
    if args.flatten:
        total = flatten(extracted, args.dest / args.dataset / "processed")
        print(f"{total} imagenes organizadas en 4 clases")
    else:
        print(f"Extraido en {extracted}")


if __name__ == "__main__":
    main()
