"""Exporta un checkpoint de ml/ a ONNX y, si hay stack TensorFlow, a TFLite.

Pensado para la version on-device (misma red que sirve el backend). No se
ejecuta en el desarrollo en modo mock: necesita los pesos entrenados y, para el
paso final, TensorFlow.

Cadena de conversion:
    best.pt  --(torch.onnx.export)-->  <modelo>.onnx
             --(onnx2tf, opcional)-->  <modelo>.tflite

Instala las dependencias opcionales (no estan en requirements-ml.txt):
    pip install onnx onnxruntime onnx2tf tensorflow

Uso (desde la raiz del repositorio):
    python ml/export_tflite.py --model mobilenetv3
    python ml/export_tflite.py --model mobilenetv3 --weights ml/models/mobilenetv3/best.pt
    python ml/export_tflite.py --model mobilenetv3 --onnx-only   # sin TensorFlow

Salida: ml/models/exports/<modelo>.onnx y (si aplica) <modelo>.tflite.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ML_DIR = Path(__file__).resolve().parent
for _candidate in (_ML_DIR, _ML_DIR / "training", _ML_DIR / "dataset", _ML_DIR / "evaluation"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

REPO_ROOT = _ML_DIR
MODELS_DIR = REPO_ROOT / "models"
EXPORTS_DIR = MODELS_DIR / "exports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="mobilenetv3, efficientnetb0, ...")
    parser.add_argument("--weights", type=Path, default=None,
                        help="Por defecto ml/models/<modelo>/best.pt")
    parser.add_argument("--output-dir", type=Path, default=EXPORTS_DIR)
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument("--onnx-only", action="store_true",
                        help="Detente tras exportar ONNX (no requiere TensorFlow)")
    return parser.parse_args()


def export_onnx(model, num_classes: int, output: Path, opset: int) -> None:
    import torch

    output.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.randn(1, 3, 224, 224)
    torch.onnx.export(
        model,
        dummy,
        output,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=opset,
    )
    print(f"ONNX exportado: {output}")


def export_tflite(onnx_path: Path, output: Path, num_classes: int) -> None:
    try:
        import onnx2tf  # noqa: F401
    except ImportError:
        print(
            "onnx2tf no esta instalado; se omite el paso TFLite.\n"
            "  pip install onnx2tf tensorflow"
        )
        return

    import onnx2tf

    output.parent.mkdir(parents=True, exist_ok=True)
    onnx2tf.convert(
        input_onnx_file_path=str(onnx_path),
        output_folder_path=str(output.parent / f"{output.stem}_saved_model"),
        non_verbose=True,
    )
    print(f"TFLite generado en {output.parent / f'{output.stem}_saved_model'}")
    print(
        "Nota: la salida de onnx2tf es un SavedModel; la conversion a .tflite se "
        "completa con el convertidor de TensorFlow. El SavedModel ya es apto para "
        "TFLiteConverter.from_saved_model(...)."
    )


def main() -> None:
    args = parse_args()
    weights = args.weights or (MODELS_DIR / args.model / "best.pt")
    if not weights.exists():
        raise SystemExit(f"No hay pesos en {weights}; entrena primero (ver docs/ml-training-handoff.md)")

    import torch

    from dataset.preprocessing import load_classes
    from model_factory import build_model

    classes = load_classes()
    checkpoint = torch.load(weights, map_location="cpu", weights_only=False)
    architecture = checkpoint.get("architecture", args.model)
    if architecture != args.model:
        raise SystemExit(f"El checkpoint es de {architecture}, no de --model {args.model}")

    model = build_model(architecture, num_classes=len(classes), pretrained=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    onnx_path = args.output_dir / f"{args.model}.onnx"
    export_onnx(model, len(classes), onnx_path, args.opset)

    if args.onnx_only:
        print("Exportacion detenida en ONNX (--onnx-only).")
        return

    export_tflite(onnx_path, args.output_dir / f"{args.model}.tflite", len(classes))


if __name__ == "__main__":
    main()
