"""Construccion de las cinco arquitecturas torchvision para inferencia real.

Espejo autocontenido de `ml/training/model_factory.py`: se replica aqui para que
la imagen Docker del backend no dependa de `ml/training` (que no se copia en el
`Dockerfile`). El contrato de arquitecturas y la capa objetivo de Grad-CAM
siguen declarados en `ml/configs/<modelo>.yaml`; cualquier cambio alli debe
reflejarse aqui y en `docs/notas-correccion-paper.md` §4.

`torch`/`torchvision` se importan dentro de las funciones (no en el modulo) para
que el backend pueda arrancar en modo mock sin tener PyTorch instalado.
"""

from __future__ import annotations

import re
from typing import Any

# Nombre de la arquitectura -> (fabrica de torchvision, enum de pesos).
# Debe coincidir con `MODEL_SPECS` de ml/training/model_factory.py.
MODEL_SPECS: dict[str, tuple[str, str]] = {
    "mobilenetv3": ("mobilenet_v3_large", "MobileNet_V3_Large_Weights"),
    "efficientnetb0": ("efficientnet_b0", "EfficientNet_B0_Weights"),
    "shufflenetv2": ("shufflenet_v2_x1_0", "ShuffleNet_V2_X1_0_Weights"),
    "resnet18": ("resnet18", "ResNet18_Weights"),
    "densenet121": ("densenet121", "DenseNet121_Weights"),
}

# Capa objetivo de Grad-CAM por arquitectura (ver docs/notas-correccion-paper.md §4).
GRADCAM_TARGET_LAYERS: dict[str, str] = {
    "mobilenetv3": "features[-1]",
    "efficientnetb0": "features[-1]",
    "shufflenetv2": "conv5",
    "densenet121": "features.denseblock4",
    "resnet18": "layer4[-1]",
}

_SEGMENT = re.compile(r"^([A-Za-z_]\w*)(?:\[(-?\d+)\])?$")


def build_model(architecture: str, num_classes: int = 4, pretrained: bool = False) -> Any:
    """Crea una arquitectura torchvision y reemplaza su cabeza final.

    `pretrained=False` es lo habitual al cargar un checkpoint local: no se
    descargan los pesos de ImageNet porque se sobreescriben con el `state_dict`.
    """
    from torch import nn
    from torchvision import models

    if architecture not in MODEL_SPECS:
        raise ValueError(
            f"Arquitectura desconocida: {architecture}. Opciones: {sorted(MODEL_SPECS)}"
        )

    factory_name = MODEL_SPECS[architecture][0]
    factory = getattr(models, factory_name)
    model = factory(weights=None)

    if architecture in {"mobilenetv3", "efficientnetb0"}:
        model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    elif architecture in {"shufflenetv2", "resnet18"}:
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    else:  # DenseNet121
        model.classifier = nn.Linear(model.classifier.in_features, num_classes)
    return model


def resolve_target_layers(model: Any, spec: str | None) -> list[Any]:
    """Resuelve `features[-1]`, `layer4[-1]` o `conv5` a modulos reales."""
    if spec:
        current: Any = model
        for part in spec.split("."):
            match = _SEGMENT.match(part)
            if match is None:
                raise ValueError(f"Segmento de capa no valido: {part!r} (spec {spec!r})")
            current = getattr(current, match.group(1))
            if match.group(2) is not None:
                current = current[int(match.group(2))]
        return [current]

    last_conv: list[Any] = []
    for module in model.modules():
        if module.__class__.__name__ == "Conv2d":
            last_conv = [module]
    if not last_conv:
        raise ValueError("No se encontro ninguna capa Conv2d en el modelo")
    return last_conv
