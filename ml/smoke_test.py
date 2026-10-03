"""Smoke test del pipeline ML: dataset -> dataloader -> model -> forward -> evaluation.

NO entrena (solo 1 paso de optimizador sobre datos sinteticos). Valida que el
pipeline este funcional antes del entrenamiento pesado en la RTX 5070.

Uso (desde la raiz del repositorio):
    python ml/smoke_test.py

Comprueba, en orden:
  1. entorno: torch, CUDA disponible o no, nombre de GPU si existe;
  2. labels.json: 4 clases canonicas y orden;
  3. prepare.py sobre imagenes sinteticas -> processed/{train,val,test} + splits.json;
  4. dataloader compartido: mismos splits para los 5 modelos, clases validadas;
  5. los 5 modelos timm se construyen (pesos aleatorios, sin descargar) y el
     forward pass funciona, incluida 1 backward;
  6. metricas sobre predicciones ficticias;
  7. resolucion del target layer de Grad-CAM por modelo.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_ML_DIR = Path(__file__).resolve().parent
for _candidate in (_ML_DIR, _ML_DIR / "training", _ML_DIR / "dataset", _ML_DIR / "evaluation"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

import numpy as np
import torch
from PIL import Image

from dataset.prepare import CANONICAL_CLASSES, prepare
from dataset.preprocessing import load_classes, load_config

MODELS = ["mobilenetv3", "efficientnetb0", "shufflenetv2", "resnet18", "densenet121"]

_results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, ok, detail))
    print(f"[{'OK' if ok else 'FALLO'}] {name} {detail}")


def main() -> int:
    # 1. Entorno.
    cuda = torch.cuda.is_available()
    gpu = torch.cuda.get_device_name(0) if cuda else "sin GPU (CPU)"
    check("entorno torch", True, f"torch={torch.__version__} cuda={cuda} gpu={gpu}")

    # 2. Labels.
    try:
        classes = load_classes()
        check("labels.json", classes == CANONICAL_CLASSES, str(classes))
    except Exception as exc:  # noqa: BLE001
        check("labels.json", False, str(exc))
        classes = []

    # 3. prepare.py sobre datos sinteticos.
    try:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "raw_demo"
            for cls in CANONICAL_CLASSES:
                (src / cls).mkdir(parents=True)
                for i in range(12):
                    arr = (np.random.default_rng(i).random((64, 64, 3)) * 255).astype(np.uint8)
                    Image.fromarray(arr).save(src / cls / f"img_{i:02d}.png")
            dest = Path(tmp) / "processed"
            manifest = prepare(src, dest, overwrite=True)
            counts = manifest["counts"]
            ok = (
                manifest["total"] == 48
                and all(counts[s][c] > 0 for s in ("train", "val", "test") for c in CANONICAL_CLASSES)
                and (dest / "splits.json").exists()
            )
            check("prepare.py sintetico", ok, f"total={manifest['total']} {counts['train']}")

            # 4. Dataloader compartido para los 5 modelos.
            from dataloader import build_dataloaders  # noqa: E402

            sizes = set()
            for model in MODELS:
                train_loader, val_loader, test_loader = build_dataloaders(
                    model, root=dest, batch_size=4, num_workers=0)
                sizes.add((len(train_loader.dataset), len(val_loader.dataset), len(test_loader.dataset)))
                assert train_loader.dataset.classes == CANONICAL_CLASSES
            check("dataloader x5 identico", len(sizes) == 1, str(sizes.pop()))

            # 5. Construccion + forward + backward de los 5 modelos.
            from train import build_model, build_optimizer  # noqa: E402

            for model in MODELS:
                config = load_config(model)
                net = build_model({**config, "pretrained": False}, len(CANONICAL_CLASSES))
                net.train()
                images = torch.randn(2, 3, config["input"]["size"], config["input"]["size"])
                labels = torch.tensor([0, 3])
                loss = torch.nn.CrossEntropyLoss()(net(images), labels)
                opt = build_optimizer(net, config)
                opt.zero_grad()
                loss.backward()
                opt.step()
            check("forward+backward x5", True, "batch=2, 1 paso")

            # 6. Metricas.
            from evaluation.metrics import compute_metrics  # noqa: E402

            y_true = np.array([0, 1, 2, 3, 0, 1, 2, 3])
            y_pred = np.array([0, 1, 2, 3, 0, 2, 2, 3])
            m = compute_metrics(y_true, y_pred, CANONICAL_CLASSES)
            check("metrics", abs(m["accuracy"] - 0.875) < 1e-9, f"acc={m['accuracy']:.3f}")

            # 7. Target layers de Grad-CAM.
            from evaluation.gradcam import resolve_target_layers  # noqa: E402

            for model in MODELS:
                config = load_config(model)
                net = build_model({**config, "pretrained": False}, len(CANONICAL_CLASSES))
                layers = resolve_target_layers(net, config["gradcam"].get("target_layer"))
                assert len(layers) == 1
            check("gradcam target_layer x5", True, "1 capa por modelo")
    except Exception as exc:  # noqa: BLE001
        check("pipeline sintetico", False, f"{type(exc).__name__}: {exc}")

    failed = [n for n, ok, _ in _results if not ok]
    print(f"\n{len(_results) - len(failed)}/{len(_results)} comprobaciones OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
