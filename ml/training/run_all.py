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

Al evaluar, guarda informes y comparison.json en un directorio único bajo
ml/evaluation/reports/runs/. --skip-eval no lee informes previos ni genera
comparaciones. La columna "Apto movil" NO se genera: es un criterio posterior.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
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
    parser.add_argument("--data-root", type=Path, default=None,
                        help="processed/ alternativo (por defecto ml/data/processed)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Permite reemplazar los artefactos existentes de cada modelo")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")
    return parser.parse_args()


def run(cmd: list[str]) -> int:
    print(f"$ {' '.join(str(c) for c in cmd)}")
    try:
        proc = subprocess.run(cmd, cwd=REPO_ROOT)
    except OSError as exc:
        print(f"No se pudo iniciar el subproceso: {exc}")
        return 127
    return proc.returncode


def new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


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
    trained_successfully: set[str] = set()
    if not args.skip_train:
        for model in models:
            cmd = [sys.executable, "ml/training/train.py", "--model", model,
                   "--preset", str(args.preset), "--device", device]
            if args.data_root:
                cmd += ["--data-root", str(args.data_root)]
            if args.overwrite:
                cmd.append("--overwrite")
            if args.epochs:
                cmd += ["--epochs", str(args.epochs)]
            return_code = run(cmd)
            if return_code != 0:
                failures.append(f"train:{model}")
                print(f"[FALLO] entrenamiento {model} (código {return_code})")
            elif not (MODELS_DIR / model / "best.pt").is_file():
                failures.append(f"train:{model} (sin best.pt al finalizar)")
                print(f"[FALLO] entrenamiento {model}: no produjo best.pt")
            else:
                trained_successfully.add(model)
                print(f"[OK] entrenamiento {model} completado en esta ejecución")

    current_reports: dict[str, dict] = {}
    run_reports_dir: Path | None = None
    if args.skip_eval:
        print("Evaluación omitida; no se leyeron informes previos ni se generó comparación.")
    else:
        run_id = new_run_id()
        run_reports_dir = REPORTS_DIR / "runs" / run_id
        # A unique run directory keeps this execution's outputs separate and
        # refuses a collision instead of replacing previous reports.
        run_reports_dir.mkdir(parents=True, exist_ok=False)
        for model in models:
            if not args.skip_train and model not in trained_successfully:
                print(f"[OMITIDO] evaluación {model}: su entrenamiento falló en esta ejecución")
                continue
            weights = MODELS_DIR / model / "best.pt"
            if not weights.exists():
                failures.append(f"eval:{model} (sin {weights})")
                continue
            cmd = [sys.executable, "ml/evaluation/metrics.py", "--model", model,
                   "--weights", str(weights), "--reports-dir", str(run_reports_dir)]
            if args.data_root:
                cmd += ["--data-root", str(args.data_root)]
            return_code = run(cmd)
            if return_code != 0:
                failures.append(f"eval:{model}")
                print(f"[FALLO] evaluación {model} (código {return_code})")
                continue
            report_path = run_reports_dir / f"{model}_metrics.json"
            if not report_path.is_file():
                failures.append(f"eval:{model} (sin informe {report_path})")
                print(f"[FALLO] evaluación {model}: no produjo su informe")
                continue
            with report_path.open(encoding="utf-8") as fh:
                current_reports[model] = json.load(fh)

    if not args.skip_eval and current_reports:
        comparison = {
            model: {
                "accuracy": report.get("accuracy"),
                "macro_precision": report.get("macro_precision"),
                "macro_recall": report.get("macro_recall"),
                "macro_f1": report.get("macro_f1"),
                "roc_auc_macro_ovr": report.get("roc_auc_macro_ovr"),
                "tumor_recall": report.get("tumor_recall"),
                "ms_per_image": report.get("ms_per_image"),
                "num_parameters_m": report.get("num_parameters_m"),
                "checkpoint_mb": report.get("checkpoint_mb"),
                "best_val_accuracy": report.get("best_val_accuracy"),
            }
            for model, report in current_reports.items()
        }
        out = run_reports_dir / "comparison.json"
        with out.open("x", encoding="utf-8") as fh:
            json.dump(comparison, fh, indent=2)
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
    if args.skip_eval:
        print("\nOK: entrenamiento completado; evaluación y comparación omitidas.")
    else:
        print(f"\nOK: ejecución completada; informes actuales en {run_reports_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
