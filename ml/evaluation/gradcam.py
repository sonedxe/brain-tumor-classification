"""Grad-CAM: mapa de calor de la zona que el modelo usa para decidir (OE2).

La capa objetivo no es la misma en las cinco arquitecturas. equivocarse
produce un mapa vacio o ruido sin ningun error visible, por eso el valor vive
en `gradcam_target_layer` de cada YAML y este modulo lo resuelve solo cuando
no se indica.

Uso:
    python gradcam.py --model mobilenetv3 --weights ../models/mobilenetv3/best.pt \
        --image ../../dataset/raw/ejemplo.png --output reports/mobilenetv3_ejemplo.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from augmentation import build_val_transform
from dataset.preprocessing import load_classes, load_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_target_layers(model: nn.Module, spec: str | None) -> list[nn.Module]:
    """Resuelve gradcam_target_layer del YAML a un modulo real del modelo."""
    if spec:
        layers: list[nn.Module] = []
        current: nn.Module = model
        for part in spec.split("."):
            current = current[int(part)] if part.lstrip("-").isdigit() else getattr(current, part)
        layers.append(current)
        return layers

    last_conv: list[nn.Module] = []
    for module in model.modules():
        if isinstance(module, nn.Conv2d):
            last_conv = [module]
    if not last_conv:
        raise ValueError("No se encontro ninguna capa Conv2d en el modelo")
    return last_conv


def load_model(model_name: str, weights: Path, device: torch.device) -> tuple[nn.Module, dict]:
    from train import build_model

    config = load_config(model_name)
    classes = load_classes()
    checkpoint = torch.load(weights, map_location=device, weights_only=False)
    model = build_model(config, len(classes))
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device).eval()
    return model, config


def overlay_heatmap(
    original: Image.Image, heatmap: np.ndarray, alpha: float = 0.45
) -> Image.Image:
    heatmap_rgb = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_rgb, cv2.COLOR_BGR2RGB)
    heatmap_rgb = cv2.resize(heatmap_rgb, original.size)

    base = np.asarray(original.convert("RGB"), dtype=np.float32)
    blended = (1 - alpha) * base + alpha * heatmap_rgb.astype(np.float32)
    return Image.fromarray(np.uint8(np.clip(blended, 0, 255)))


def compute_gradcam(
    model: nn.Module,
    config: dict,
    image: Image.Image,
    classes: list[str],
    device: torch.device,
) -> tuple[Image.Image, np.ndarray, int]:
    target_layers = resolve_target_layers(model, config["gradcam"].get("target_layer"))

    tensor = build_val_transform(config["model"])(image).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
    predicted_index = int(logits.argmax(dim=1).item())

    with GradCAM(model=model, target_layers=target_layers) as cam:
        grayscale = cam(
            input_tensor=tensor,
            targets=[ClassifierOutputTarget(predicted_index)],
            eigen_smooth=False,
        )
    heatmap = grayscale[0]

    return overlay_heatmap(image, heatmap), heatmap, predicted_index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    from train import resolve_device

    device = resolve_device(args.device)
    classes = load_classes()
    model, config = load_model(args.model, args.weights, device)

    with Image.open(args.image) as image:
        rgb = image.convert("RGB")
        result, _, predicted_index = compute_gradcam(model, config, rgb, classes, device)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)
    print(f"clase predicha: {classes[predicted_index]}")
    print(f"mapa de calor: {args.output}")


if __name__ == "__main__":
    main()
