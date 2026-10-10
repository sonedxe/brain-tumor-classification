"""Smoke test del pipeline ML: dataset -> dataloader -> model -> forward -> evaluation.

NO entrena (solo 1 paso de optimizador sobre datos sinteticos). Valida que el
pipeline este funcional antes del entrenamiento pesado en la RTX 5070.

Uso (desde la raiz del repositorio):
    python ml/smoke_test.py

Comprueba, en orden:
  1. entorno: torch, CUDA disponible o no, nombre de GPU si existe;
  2. labels.json: 4 clases canonicas y orden;
  3. prepare.py sobre Training/Testing sinteticos -> processed/{train,val,test} + splits.json;
  4. dataloader compartido: mismos splits para los 5 modelos, clases validadas;
  5. los 5 modelos torchvision se construyen (pesos aleatorios, sin descargar) y el
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
RAW_CLASSES = {
    "glioma": "glioma", "meningioma": "meningioma",
    "pituitary": "pituitario", "notumor": "no_tumor",
}

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
            for raw_cls in RAW_CLASSES:
                (src / "Training" / raw_cls).mkdir(parents=True)
                (src / "Testing" / raw_cls).mkdir(parents=True)
                for i in range(12):
                    arr = (np.random.default_rng(i).random((64, 64, 3)) * 255).astype(np.uint8)
                    Image.fromarray(arr).save(src / "Training" / raw_cls / f"train_{i:02d}.png")
                for i in range(4):
                    arr = (np.random.default_rng(100 + i).random((64, 64, 3)) * 255).astype(np.uint8)
                    Image.fromarray(arr).save(src / "Testing" / raw_cls / f"test_{i:02d}.png")
            dest = Path(tmp) / "processed"
            # This smoke test deliberately uses a tiny synthetic dataset; the
            # CLI and real preparation retain the production count contract.
            from unittest import mock

            synthetic_counts = {
                "Training": {name: 12 for name in RAW_CLASSES},
                "Testing": {name: 4 for name in RAW_CLASSES},
            }
            with mock.patch("dataset.prepare.EXPECTED_COUNTS", synthetic_counts):
                manifest = prepare(src, dest, overwrite=True)
                counts = manifest["counts"]
                second = prepare(src, Path(tmp) / "processed_again")
                existing_destination_blocked = False
                try:
                    prepare(src, dest)
                except FileExistsError:
                    existing_destination_blocked = True
            ok = (
                manifest["total"] == 64
                and sum(counts["train"].values()) == 38
                and sum(counts["val"].values()) == 10
                and sum(counts["test"].values()) == 16
                and manifest["split_fingerprint"] == second["split_fingerprint"]
                and existing_destination_blocked
                and all(counts[s][c] > 0 for s in ("train", "val", "test") for c in CANONICAL_CLASSES)
                and (dest / "splits.json").exists()
            )
            check("prepare.py splits + class aliases", ok,
                  f"fingerprint={manifest['split_fingerprint'][:12]} counts={counts}")

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
            from model_factory import (  # noqa: E402
                build_model, classifier_module, freeze_backbone,
                set_frozen_batchnorm_eval, trainable_parameters,
            )

            for model in MODELS:
                net = build_model(model, num_classes=len(CANONICAL_CLASSES), pretrained=False)
                freeze_backbone(net, model)
                head = classifier_module(net, model)
                assert all(p.requires_grad for p in head.parameters())
                head_ids = {id(p) for p in head.parameters()}
                assert all(not p.requires_grad for p in net.parameters() if id(p) not in head_ids)
                net.train()
                batchnorms = [
                    module for module in net.modules()
                    if isinstance(module, torch.nn.modules.batchnorm._BatchNorm)
                ]
                buffers_before = [
                    buffer.detach().clone()
                    for module in batchnorms
                    for buffer in (module.running_mean, module.running_var, module.num_batches_tracked)
                    if buffer is not None
                ]
                set_frozen_batchnorm_eval(net)
                assert all(not module.training for module in batchnorms)
                images = torch.randn(2, 3, 224, 224)
                labels = torch.tensor([0, 3])
                logits = net(images)
                assert logits.shape == (2, len(CANONICAL_CLASSES))
                loss = torch.nn.CrossEntropyLoss()(logits, labels)
                opt = torch.optim.Adam(list(trainable_parameters(net)), lr=0.001)
                opt.zero_grad()
                loss.backward()
                opt.step()
                assert all(p.grad is None for p in net.parameters() if id(p) not in head_ids)
                assert all(p.grad is not None for p in head.parameters())
                buffers_after = [
                    buffer
                    for module in batchnorms
                    for buffer in (module.running_mean, module.running_var, module.num_batches_tracked)
                    if buffer is not None
                ]
                assert all(torch.equal(before, after) for before, after in zip(buffers_before, buffers_after))
                # Every epoch starts with model.train(); the helper must restore frozen BN eval mode.
                net.train()
                set_frozen_batchnorm_eval(net)
                assert all(not module.training for module in batchnorms)
            check("forward+backward x5", True, "batch=2, 1 paso")

            # Una epoca comun sintetica demuestra train + validacion sin leer test.
            from torch.utils.data import DataLoader, TensorDataset  # noqa: E402
            from train import run_training  # noqa: E402

            tiny = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(3 * 8 * 8, 4))
            tiny_optimizer = torch.optim.Adam(tiny.parameters(), lr=0.001)
            toy = TensorDataset(torch.randn(4, 3, 8, 8), torch.tensor([0, 1, 2, 3]))
            train_history, selected = run_training(
                tiny, DataLoader(toy, batch_size=2), DataLoader(toy, batch_size=2),
                torch.device("cpu"), 1, tiny_optimizer, architecture="synthetic",
                classes=CANONICAL_CLASSES,
            )
            check("train+validation sinteticos", len(train_history) == 1 and selected is not None,
                  f"val_accuracy={selected['val_accuracy']:.3f}")

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
                net = build_model(model, num_classes=len(CANONICAL_CLASSES), pretrained=False)
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
