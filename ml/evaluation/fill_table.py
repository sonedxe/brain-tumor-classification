"""Rellena docs/tabla-comparativa.md con los artefactos de entrenamiento.

Lee, sin volver a evaluar:
  - ml/models/<modelo>/metadata.json          -> val_accuracy y epoca (siempre presentes)
  - ml/evaluation/reports/runs/<run>/comparison.json  -> metricas de test (si existe)
  - ml/models/<modelo>/best.pt                -> tamano del checkpoint (si existe)
  - ml/evaluation/reports/**/<modelo>*.png    -> si se genero un Grad-CAM

y escribe las tres tablas entre los marcadores `<!-- BEGIN:x -->` / `<!-- END:x -->`
de docs/tabla-comparativa.md. Las celdas sin dato quedan vacias, de modo que el
documento nunca muestra numeros inventados.

Uso:
    python ml/evaluation/fill_table.py            # usa la ultima corrida de evaluacion
    python ml/evaluation/fill_table.py --run runs/20260101T000000Z-abcd1234
    python ml/evaluation/fill_table.py --dry-run  # imprime sin escribir
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "ml" / "models"
REPORTS_DIR = REPO_ROOT / "ml" / "evaluation" / "reports"
RUNS_DIR = REPORTS_DIR / "runs"
TABLE_PATH = REPO_ROOT / "docs" / "tabla-comparativa.md"

MODELS = ["mobilenetv3", "efficientnetb0", "shufflenetv2", "densenet121", "resnet18"]

DISPLAY_NAMES = {
    "mobilenetv3": "MobileNetV3",
    "efficientnetb0": "EfficientNetB0",
    "shufflenetv2": "ShuffleNetV2",
    "densenet121": "DenseNet121",
    "resnet18": "ResNet18",
}


def _read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


def latest_run_dir() -> Path | None:
    if not RUNS_DIR.is_dir():
        return None
    runs = sorted((p for p in RUNS_DIR.iterdir() if p.is_dir()), key=lambda p: p.name)
    return runs[-1] if runs else None


def load_test_metrics(run_dir: Path | None) -> dict[str, dict]:
    """Devuelve {modelo: metricas} desde comparison.json o los informes por modelo."""
    if run_dir is None:
        return {}

    comparison = _read_json(run_dir / "comparison.json")
    if comparison:
        return comparison

    metrics: dict[str, dict] = {}
    for model in MODELS:
        report = _read_json(run_dir / f"{model}_metrics.json")
        if report:
            metrics[model] = report
    return metrics


def load_checkpoint_metadata(model: str) -> dict:
    return _read_json(MODELS_DIR / model / "metadata.json")


def has_gradcam(model: str) -> bool:
    if not REPORTS_DIR.is_dir():
        return False
    return any(REPORTS_DIR.rglob(f"{model}*.png"))


def _fmt(value, *, percent: bool = False, decimals: int = 2) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value
    if percent:
        return f"{value * 100:.{decimals}f} %"
    return f"{value:.{decimals}f}"


def render_principal(metrics: dict[str, dict]) -> list[str]:
    lines = [
        "| Modelo | Params (M) | Tamano (MB) | Exactitud test | Macro F1 test | Recall tumor | ROC-AUC OVR | ms/imagen | Apto movil |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for model in MODELS:
        row = metrics.get(model, {})
        name = DISPLAY_NAMES[model]
        if model == "resnet18":
            name = "**ResNet18 (ref.)**"
        lines.append(
            "| {name} | {params} | {size} | {acc} | {f1} | {recall} | {auc} | {ms} |  |".format(
                name=name,
                params=_fmt(row.get("num_parameters_m")),
                size=_fmt(row.get("checkpoint_mb")),
                acc=_fmt(row.get("accuracy"), percent=True),
                f1=_fmt(row.get("macro_f1"), percent=True),
                recall=_fmt(row.get("tumor_recall"), percent=True),
                auc=_fmt(row.get("roc_auc_macro_ovr"), decimals=4),
                ms=_fmt(row.get("ms_per_image")),
            )
        )
    return lines


def render_checkpoint() -> list[str]:
    lines = [
        "| Modelo | Mejor val_accuracy | Epoca |",
        "| --- | --- | --- |",
    ]
    for model in MODELS:
        metadata = load_checkpoint_metadata(model)
        lines.append(
            "| {name} | {acc} | {epoch} |".format(
                name=DISPLAY_NAMES[model],
                acc=_fmt(metadata.get("best_val_accuracy"), percent=True),
                epoch=metadata.get("epoch", ""),
            )
        )
    return lines


def render_interpretability() -> list[str]:
    lines = [
        "| Modelo | Grad-CAM generado | Zona de activacion coherente con la lesion |",
        "| --- | --- | --- |",
    ]
    for model in MODELS:
        generated = "Si" if has_gradcam(model) else "No"
        lines.append(f"| {DISPLAY_NAMES[model]} | {generated} |  |")
    return lines


BLOCKS = {
    "principal": render_principal,
    "checkpoint": lambda _metrics: render_checkpoint(),
    "interpretabilidad": lambda _metrics: render_interpretability(),
}


def replace_block(text: str, name: str, body: list[str]) -> str:
    pattern = re.compile(
        rf"(<!-- BEGIN:{name} -->\n).*?(\n<!-- END:{name} -->)",
        re.DOTALL,
    )
    replacement = r"\g<1>" + "\n".join(body) + r"\g<2>"
    new_text, count = pattern.subn(replacement, text)
    if count == 0:
        raise ValueError(f"No se encontro el marcador BEGIN/END:{name} en {TABLE_PATH}")
    return new_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=None,
                        help="Directorio de una corrida (por defecto, la ultima en reports/runs)")
    parser.add_argument("--dry-run", action="store_true", help="No escribe el archivo")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = args.run if args.run else latest_run_dir()
    if run_dir is not None and not run_dir.is_absolute():
        candidate = RUNS_DIR / run_dir
        run_dir = candidate if candidate.exists() else run_dir

    metrics = load_test_metrics(run_dir)
    text = TABLE_PATH.read_text(encoding="utf-8")
    for name, renderer in BLOCKS.items():
        text = replace_block(text, name, renderer(metrics))

    if args.dry_run:
        print(text)
        print(f"\n[DRY-RUN] corrida evaluada: {run_dir or 'ninguna'}")
        return

    TABLE_PATH.write_text(text, encoding="utf-8")
    print(f"tabla actualizada: {TABLE_PATH}")
    print(f"corrida evaluada: {run_dir or 'ninguna (solo val_accuracy)'}")
    if not metrics:
        print("Aviso: no hay comparison.json; la tabla principal quedo con los placeholders vacios.")


if __name__ == "__main__":
    main()
