# Tabla comparativa (OE2)

Formato de resultados para las cinco arquitecturas. Las metricas de test y la
tabla de validacion se generan con `ml/evaluation/fill_table.py` a partir de los
artefactos de entrenamiento (`metadata.json`) y del resumen de evaluacion
(`ml/evaluation/reports/comparison.json`).

> **Trazabilidad.** La tabla de test usa las metricas extraidas de los notebooks
> de entrenamiento (`ml/evaluation/extract_notebooks.py`), que es la corrida
> documentada en el ANEXO comparativo. Los checkpoints `ml/models/*/best.pt`
> pueden provenir de una corrida posterior con mayor exactitud de validacion;
> re-evaluarlos con `python ml/training/run_all.py --skip-train` y volver a
> correr `fill_table.py` es un paso **opcional** para alinear ambas.

## Tabla principal

<!-- BEGIN:principal -->
| Modelo | Params (M) | Tamano (MB) | Exactitud test | Macro F1 test | Recall tumor | ROC-AUC OVR | ms/imagen | Apto movil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MobileNetV3 | 5.48 | 16.25 | 87.19 % | 86.97 % | 83.08 % | 0.9710 |  |  |
| EfficientNetB0 | 5.29 | 15.59 | 87.06 % | 86.73 % | 82.75 % | 0.9711 |  |  |
| ShuffleNetV2 | 2.28 | 4.96 | 82.56 % | 82.15 % | 77.08 % | 0.9539 |  |  |
| DenseNet121 | 7.98 | 27.12 | 87.56 % | 87.41 % | 84.00 % | 0.9677 |  |  |
| **ResNet18 (ref.)** | 11.69 | 42.72 | 85.69 % | 85.37 % | 81.42 % | 0.9644 |  |  |
<!-- END:principal -->

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

<!-- BEGIN:checkpoint -->
| Modelo | Mejor val_accuracy | Epoca |
| --- | --- | --- |
| MobileNetV3 | 93.75 % | 91 |
| EfficientNetB0 | 94.55 % | 100 |
| ShuffleNetV2 | 90.98 % | 98 |
| DenseNet121 | 91.79 % | 93 |
| ResNet18 | 90.98 % | 77 |
<!-- END:checkpoint -->

## Interpretabilidad

<!-- BEGIN:interpretabilidad -->
| Modelo | Grad-CAM generado | Zona de activacion coherente con la lesion |
| --- | --- | --- |
| MobileNetV3 | No |  |
| EfficientNetB0 | No |  |
| ShuffleNetV2 | No |  |
| DenseNet121 | No |  |
| ResNet18 | No |  |
<!-- END:interpretabilidad -->

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
