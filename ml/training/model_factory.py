"""Construccion compartida de las cinco arquitecturas torchvision."""

from __future__ import annotations

from collections.abc import Iterable

from torch import nn
from torchvision import models

MODEL_SPECS = {
    "mobilenetv3": ("mobilenet_v3_large", "MobileNet_V3_Large_Weights"),
    "efficientnetb0": ("efficientnet_b0", "EfficientNet_B0_Weights"),
    "shufflenetv2": ("shufflenet_v2_x1_0", "ShuffleNet_V2_X1_0_Weights"),
    "resnet18": ("resnet18", "ResNet18_Weights"),
    "densenet121": ("densenet121", "DenseNet121_Weights"),
}


def build_model(architecture: str, num_classes: int = 4, pretrained: bool = True) -> nn.Module:
    """Crea una arquitectura torchvision y reemplaza su cabeza final."""
    if architecture not in MODEL_SPECS:
        raise ValueError(f"Arquitectura desconocida: {architecture}. Opciones: {sorted(MODEL_SPECS)}")
    if num_classes != 4:
        raise ValueError("El contrato de etiquetas del proyecto requiere exactamente cuatro clases")

    factory_name, weights_name = MODEL_SPECS[architecture]
    factory = getattr(models, factory_name)
    weights_enum = getattr(models, weights_name)
    model = factory(weights=weights_enum.DEFAULT if pretrained else None)

    if architecture == "mobilenetv3":
        features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(features, num_classes)
    elif architecture == "efficientnetb0":
        features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(features, num_classes)
    elif architecture in {"shufflenetv2", "resnet18"}:
        features = model.fc.in_features
        model.fc = nn.Linear(features, num_classes)
    else:  # DenseNet121
        features = model.classifier.in_features
        model.classifier = nn.Linear(features, num_classes)
    return model


def classifier_module(model: nn.Module, architecture: str) -> nn.Module:
    if architecture in {"mobilenetv3", "efficientnetb0"}:
        return model.classifier[-1]
    if architecture in {"shufflenetv2", "resnet18"}:
        return model.fc
    if architecture == "densenet121":
        return model.classifier
    raise ValueError(f"Arquitectura desconocida: {architecture}")


def freeze_backbone(model: nn.Module, architecture: str) -> None:
    """Congela toda la red y habilita solo los parámetros de la cabeza."""
    model.requires_grad_(False)
    classifier_module(model, architecture).requires_grad_(True)


def set_frozen_batchnorm_eval(model: nn.Module) -> None:
    """Keep BatchNorm running statistics fixed for modules with frozen affine params.

    ``model.train()`` recursively switches BatchNorm layers back to training
    mode, so the training loop must call this immediately afterwards.
    """
    for module in model.modules():
        if isinstance(module, nn.modules.batchnorm._BatchNorm):
            own_parameters = module.parameters(recurse=False)
            if not any(parameter.requires_grad for parameter in own_parameters):
                module.eval()


def trainable_parameters(model: nn.Module) -> Iterable[nn.Parameter]:
    """Itera únicamente los parámetros marcados como entrenables."""
    return (parameter for parameter in model.parameters() if parameter.requires_grad)

