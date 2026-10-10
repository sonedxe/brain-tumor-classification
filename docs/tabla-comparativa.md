# Tabla comparativa (OE2)

Formato de resultados para las cinco arquitecturas. Los placeholders se
completan con los artefactos de entrenamiento y `ml/evaluation/metrics.py`.

## Tabla principal

| Modelo | Params (M) | Tamano (MB) | Exactitud test | Macro F1 test | Recall tumor | ROC-AUC OVR | ms/imagen | Apto movil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MobileNetV3 | | | | | | | | |
| EfficientNetB0 | | | | | | | | |
| ShuffleNetV2 | | | | | | | | |
| DenseNet121 | | | | | | | | |
| **ResNet18 (ref.)** | | | | | | | | |

## Matrices de confusion

Una por modelo, generadas en `ml/evaluation/reports/`. Orden de las clases
segun `ml/configs/labels.json`:

```
                 pred: glioma  meningioma  pituitario  no_tumor
real: glioma
     meningioma
     pituitario
     no_tumor
```

## Seleccion del checkpoint por validacion

La seleccion del checkpoint usa exclusivamente `val_accuracy`. Test se conserva
aislado y se evalua una vez terminada la seleccion.

| Modelo | Mejor val_accuracy | Epoca |
| --- | --- | --- |
| MobileNetV3 | | |
| EfficientNetB0 | | |
| ShuffleNetV2 | | |
| DenseNet121 | | |
| ResNet18 | | |

## Interpretabilidad

| Modelo | Grad-CAM generado | Zona de activacion coherente con la lesion |
| --- | --- | --- |
| MobileNetV3 | | |
| EfficientNetB0 | | |
| ShuffleNetV2 | | |
| DenseNet121 | | |
| ResNet18 | | |

## Criterio de seleccion

El modelo elegido debe ponderarse en este orden:

1. **Exactitud y Macro F1** en el test independiente, junto con la mejor exactitud de validacion.
2. **Recall de la clase tumoral**: en un apoyo diagnostico, el falso negativo
   es mas grave que el falso positivo.
3. **Tiempo de inferencia por imagen** medido en el mismo hardware que se
   documentara en la app.
4. **Tamano del modelo** y facilidad de conversion a TFLite para la version
   on-device.
5. **Calidad del mapa de calor** de Grad-CAM, valorada sobre un conjunto fijo
   de imagenes de prueba.

Registrar aqui la decision final y la justificacion, porque es la evidencia que
sustenta el OE2.
