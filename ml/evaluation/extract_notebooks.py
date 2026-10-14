"""Extrae las metricas de test y las figuras de los notebooks de entrenamiento.

Los notebooks (`ml/notebooks/*-checkpoint.ipynb`) contienen la evaluacion
completa sobre el conjunto de prueba: accuracy, reporte por clase, ROC-AUC
multiclase y las figuras (curvas de entrenamiento, matriz de confusion y curvas
ROC). Este script las convierte en artefactos reutilizables:

  ml/evaluation/reports/<modelo>_notebook_metrics.json   metricas por modelo
  ml/evaluation/reports/comparison.json                  resumen para fill_table.py
  ml/evaluation/reports/<modelo>_confusion.png           matriz de confusion
  ml/evaluation/reports/<modelo>_roc.png                 curvas ROC
  ml/evaluation/reports/<modelo>_training.png            curvas de entrenamiento

Nota de trazabilidad: estas metricas provienen de la corrida de los notebooks,
no necesariamente de los checkpoints `ml/models/<modelo>/best.pt` (que pueden
ser de otra ejecucion). Re-evaluar los pesos desplegados con
`python ml/training/run_all.py --skip-train` queda como paso opcional.

Uso (desde la raiz del repositorio):
    python ml/evaluation/extract_notebooks.py
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOKS_DIR = REPO_ROOT / "ml" / "notebooks"
REPORTS_DIR = REPO_ROOT / "ml" / "evaluation" / "reports"

MODELS = ["mobilenetv3", "efficientnetb0", "shufflenetv2", "densenet121", "resnet18"]

# Nombre del archivo del notebook -> clave del modelo.
NOTEBOOK_FILES = {
    "MovileNetV3-checkpoint.ipynb": "mobilenetv3",
    "EfficientNetB0-checkpoint.ipynb": "efficientnetb0",
    "ShuffleNetV2-checkpoint.ipynb": "shufflenetv2",
    "DenseNet121-checkpoint.ipynb": "densenet121",
    "ResNet18-checkpoint.ipynb": "resnet18",
}

# Clases del notebook (ImageFolder, orden alfabetico) -> clases canonicas.
NOTEBOOK_CLASSES = {"glioma": "glioma", "meningioma": "meningioma",
                    "pituitary": "pituitario", "notumor": "no_tumor"}
TUMOR_CLASSES = ("glioma", "meningioma", "pituitario")

_REPORT_ROW = re.compile(r"^\s*(glioma|meningioma|notumor|pituitary)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s*$", re.MULTILINE)
_MACRO_ROW = re.compile(r"^\s*macro avg\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$", re.MULTILINE)


def _texts(cell: dict) -> str:
    chunks: list[str] = []
    for output in cell.get("outputs", []):
        if "text" in output:
            chunks.append("".join(output["text"]))
    return "".join(chunks)


def _images(cell: dict) -> list[bytes]:
    result: list[bytes] = []
    for output in cell.get("outputs", []):
        data = output.get("data", {})
        if "image/png" in data:
            payload = data["image/png"]
            if isinstance(payload, list):
                payload = "".join(payload)
            result.append(base64.b64decode(payload))
    return result


def parse_notebook(path: Path) -> tuple[dict, dict[str, bytes]]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    text = "\n".join(_texts(cell) for cell in notebook.get("cells", []) if cell.get("cell_type") == "code")

    accuracy = re.search(r"Test Accuracy:\s*([0-9.]+)", text)
    params = re.search(r"Par[aá]metros totales:\s*(\d+)", text)
    roc_macro = re.search(r"ROC-AUC Macro:\s*([0-9.]+)", text)
    macro_row = _MACRO_ROW.search(text)

    per_class: dict[str, dict[str, float]] = {}
    for name, precision, recall, f1, support in _REPORT_ROW.findall(text):
        per_class[NOTEBOOK_CLASSES[name]] = {
            "precision": float(precision), "recall": float(recall),
            "f1": float(f1), "support": int(support),
        }

    macro_f1 = float(macro_row.group(3)) if macro_row else (
        sum(c["f1"] for c in per_class.values()) / len(per_class) if per_class else None
    )
    tumor_recall = (
        sum(per_class[c]["recall"] for c in TUMOR_CLASSES) / len(TUMOR_CLASSES)
        if all(c in per_class for c in TUMOR_CLASSES) else None
    )
    total_params = int(params.group(1)) if params else None

    metrics = {
        "accuracy": float(accuracy.group(1)) if accuracy else None,
        "macro_f1": macro_f1,
        "tumor_recall": tumor_recall,
        "roc_auc_macro_ovr": float(roc_macro.group(1)) if roc_macro else None,
        "num_parameters": total_params,
        "num_parameters_m": round(total_params / 1e6, 3) if total_params else None,
        "per_class": per_class,
    }

    figures: dict[str, bytes] = {}
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        for image in _images(cell):
            if "confusion_matrix" in source:
                figures["confusion"] = image
            elif "roc_curve" in source:
                figures["roc"] = image
            elif "confusion" not in figures and "roc" not in figures:
                figures.setdefault("training", image)
    return metrics, figures


def checkpoint_mb(model: str) -> float | None:
    path = REPO_ROOT / "ml" / "models" / model / "best.pt"
    return round(path.stat().st_size / (1024 * 1024), 3) if path.exists() else None


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    comparison: dict[str, dict] = {
        "_source": "ml/notebooks/*-checkpoint.ipynb (evaluacion de test)",
        "_note": "Corrida de los notebooks; puede diferir de ml/models/*/best.pt. "
                 "Re-evaluar con run_all.py --skip-train es opcional.",
    }

    for filename, model in NOTEBOOK_FILES.items():
        path = NOTEBOOKS_DIR / filename
        if not path.exists():
            print(f"[AVISO] falta {path}, se omite {model}")
            continue
        metrics, figures = parse_notebook(path)

        (REPORTS_DIR / f"{model}_notebook_metrics.json").write_text(
            json.dumps({"model": model, **metrics}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        for kind, data in figures.items():
            (REPORTS_DIR / f"{model}_{kind}.png").write_bytes(data)

        comparison[model] = {
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "tumor_recall": metrics["tumor_recall"],
            "roc_auc_macro_ovr": metrics["roc_auc_macro_ovr"],
            "num_parameters_m": metrics["num_parameters_m"],
            "checkpoint_mb": checkpoint_mb(model),
            "ms_per_image": None,
        }
        print(f"[OK] {model}: acc={metrics['accuracy']}, macroF1={metrics['macro_f1']}, "
              f"figuras={sorted(figures)}")

    (REPORTS_DIR / "comparison.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\ncomparison.json escrito en {REPORTS_DIR / 'comparison.json'}")


if __name__ == "__main__":
    main()
