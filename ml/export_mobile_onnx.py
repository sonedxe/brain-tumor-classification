"""Exporta el checkpoint activo a un ONNX autocontenido para la app movil.

El modo offline de Flutter carga `frontend/assets/models/model.onnx`, que debe
ser el mismo `best.pt` que sirve el backend. Este script reproduce el
preprocesamiento del backend (224x224, normalizacion ImageNet) y deja el archivo
en un unico binario, sin pesos externos.

Requisitos (en el venv del backend):

    pip install onnx onnxscript

Uso (desde la raiz del repositorio):

    backend/.venv/bin/python ml/export_mobile_onnx.py --model mobilenetv3

Salida por defecto: frontend/assets/models/model.onnx
Verificacion opcional con onnxruntime:

    backend/.venv/bin/python ml/export_mobile_onnx.py --model mobilenetv3 --verify
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ML_DIR = Path(__file__).resolve().parent
for _candidate in (_ML_DIR, _ML_DIR / "training", _ML_DIR / "dataset"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

REPO_ROOT = _ML_DIR.parent
DEFAULT_OUTPUT = REPO_ROOT / "frontend" / "assets" / "models" / "model.onnx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="mobilenetv3", help="Arquitectura del checkpoint")
    parser.add_argument(
        "--weights",
        type=Path,
        default=None,
        help="Checkpoint (por defecto ml/models/<modelo>/best.pt)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Compara la salida ONNX con torch usando onnxruntime",
    )
    return parser.parse_args()


def consolidate(src: Path, dest: Path) -> None:
    """Une los pesos externos (.data) en un unico archivo ONNX."""
    import onnx

    model_proto = onnx.load(str(src))
    dest.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model_proto, str(dest), save_as_external_data=False)


def main() -> int:
    args = parse_args()
    weights = args.weights or (_ML_DIR / "models" / args.model / "best.pt")
    if not weights.exists():
        raise SystemExit(f"No hay pesos en {weights}; entrena o copia el best.pt")

    import numpy as np
    import torch

    from dataset.preprocessing import load_classes
    from model_factory import build_model

    classes = load_classes()
    checkpoint = torch.load(weights, map_location="cpu", weights_only=False)
    architecture = checkpoint.get("architecture", args.model)
    if architecture != args.model:
        raise SystemExit(f"El checkpoint es de {architecture}, no de {args.model}")

    model = build_model(architecture, num_classes=len(classes), pretrained=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    temp = args.output.with_suffix(".tmp.onnx")
    dummy = torch.randn(1, 3, 224, 224)
    torch.onnx.export(
        model,
        dummy,
        str(temp),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=args.opset,
    )
    consolidate(temp, args.output)
    temp.unlink(missing_ok=True)
    # El exportador nuevo puede dejar un .data junto al temporal.
    temp.with_suffix(".tmp.onnx.data").unlink(missing_ok=True)

    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"ONNX autocontenido: {args.output} ({size_mb:.1f} MB)")
    print(f"Clases: {classes} · entrada 224x224 · normalizacion ImageNet")

    if args.verify:
        import onnxruntime as ort

        session = ort.InferenceSession(
            str(args.output), providers=["CPUExecutionProvider"]
        )
        with torch.no_grad():
            reference = model(dummy).numpy()
        exported = session.run(None, {session.get_inputs()[0].name: dummy.numpy()})[0]
        diff = float(np.abs(reference - exported).max())
        print(f"Verificacion torch vs onnxruntime: max |diff| = {diff:.2e}")
        if diff > 1e-3:
            raise SystemExit("La diferencia excede la tolerancia; revisa la exportacion.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
