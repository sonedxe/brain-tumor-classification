"""Entrena y evalua los cinco modelos con el mismo preset experimental.

Evita editar codigo para cambiar de modelo: un comando por modelo, o uno
para todos.

Uso (desde la raiz del repositorio):
    python ml/training/run_all.py --preset ml/configs/experiments/initial.yaml
    python ml/training/run_all.py --models mobilenetv3 resnet18 --device cuda
    python ml/training/run_all.py --skip-train        # solo evalua best.pt existentes
    python ml/training/run_all.py --skip-eval         # solo entrena

Un solo modelo (equivalente, sin este script):
    python ml/training/train.py --model mobilenetv3 --preset ml/configs/experiments/initial.yaml

Al final escribe ml/evaluation/reports/comparison.json con una fila por
modelo para rellenar docs/tabla-comparativa.md. La columna "Apto movil" NO
se genera: es un criterio posterior, no automatico.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[2]
MODELS_DIR = REPO_ROOT / "ml" / "models"
REPORTS_DIR = REPO_ROOT / "ml" / "evaluation" / "reports"

ALL_MODELS = ["mobilenetv3", "efficientnetb0", "shufflenetv2", "resnet18", "densenet121"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", type=Path,
                        default=REPO_ROOT / "ml" / "configs" / "experiments" / "initial.yaml")
    parser.add_argument("--models", nargs="+", default=None,
                        help=f"Subconjunto a ejecutar. Por defecto, los cinco: {ALL_MODELS}")
    parser.add_argument("--device", default=None,
                        help="Sobrescribe el device del preset (p. ej. cuda en la RTX 5070)")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")
    return parser.parse_args()


def run(cmd: list[str]) -> int:
    print(f"$ {' '.join(str(c) for c in cmd)}")
    proc = subprocess.run(cmd, cwd=REPO_ROOT)
    return proc.returncode


def main() -> int:
    args = parse_args()
    with args.preset.open(encoding="utf-8") as fh:
        preset = yaml.safe_load(fh)
    models = args.models or preset.get("models", ALL_MODELS)
    unknown = [m for m in models if m not in ALL_MODELS]
    if unknown:
        raise ValueError(f"Modelos desconocidos: {unknown}. Validos: {ALL_MODELS}")
    device = args.device or preset.get("device", "auto")

    failures: list[str] = []
    if not args.skip_train:
        for model in models:
            cmd = [sys.executable, "ml/training/train.py", "--model", model,
                   "--preset", str(args.preset), "--device", device]
            if args.epochs:
                cmd += ["--epochs", str(args.epochs)]
            if run(cmd) != 0:
                failures.append(f"train:{model}")

    if not args.skip_eval:
        for model in models:
            weights = MODELS_DIR / model / "best.pt"
            if not weights.exists():
                failures.append(f"eval:{model} (sin {weights})")
                continue
            if run([sys.executable, "ml/evaluation/metrics.py", "--model", model,
                    "--weights", str(weights)]) != 0:
                failures.append(f"eval:{model}")

    comparison = {}
    for model in models:
        path = REPORTS_DIR / f"{model}_metrics.json"
        if path.exists():
            with path.open(encoding="utf-8") as fh:
                report = json.load(fh)
            comparison[model] = {
                "accuracy": report.get("accuracy"),
                "macro_f1": report.get("macro_f1"),
                "tumor_recall": report.get("tumor_recall"),
                "ms_per_image": report.get("ms_per_image"),
                "num_parameters_m": report.get("num_parameters_m"),
                "checkpoint_mb": report.get("checkpoint_mb"),
                "best_val_accuracy": report.get("best_val_accuracy"),
            }
    if comparison:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORTS_DIR / "comparison.json"
        out.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
        print(f"\nComparativa escrita en {out}")
        print(f"{'modelo':<16}{'acc':>8}{'macroF1':>9}{'tRecall':>9}{'ms/img':>9}{'paramsM':>9}")
        for model, row in comparison.items():
            fmt = lambda v: f"{v:.4f}" if isinstance(v, float) else str(v)
            print(f"{model:<16}{fmt(row['accuracy']):>8}{fmt(row['macro_f1']):>9}"
                  f"{fmt(row['tumor_recall']):>9}{fmt(row['ms_per_image'] or 0):>9}"
                  f"{fmt(row['num_parameters_m'] or 0):>9}")

    if failures:
        print(f"\nFALLOS: {failures}")
        return 1
    print("\nOK: los cinco modelos (o el subconjunto pedido) completados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
