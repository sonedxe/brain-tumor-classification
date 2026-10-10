# Datasets

Este trabajo usa MRI de cerebro de Kaggle. Los directorios `ml/data/raw/` y
`ml/data/processed/` estan en `.gitignore`: los datos originales y preparados
son locales y no se versionan. Coloca en `ml/data/raw/` las carpetas
`Training/` y `Testing/`, cada una con sus cuatro carpetas de clase.

## Fuente 1 - 3.264 imagenes, 4 clases (documentacion historica)

Saeedi et al., *A novel deep learning-based approach for classification of
brain tumors*, Springerplus (2023).

Clases: `glioma`, `meningioma`, `pituitario`, `no_tumor`.

## Fuente 2 - Brain Tumor MRI Dataset

Masoud Nickparvar, *Brain Tumor MRI Dataset*, Kaggle.

Incluye las cuatro clases anteriores mas subcategorias de glioma
(`glioma_tumor`, `glioma_A`, `glioma_B`, `glioma_C`, `glioma_D`, `glioma_E`),
que se colapsan en `glioma` para las cuatro salidas del modelo.

## Licencia y atribucion

Ambas fuentes requieren atribucion. Mantener esta seccion actualizada y citar
el origen en el manuscripto. Antes de publicar los resultados, confirmar los
terminos vigentes de Kaggle, que cambian entre versiones del dataset.

## Uso responsable

Las imagenes son datos medicos. No redistribuirlas en este repositorio ni
identificar a los sujetos de las muestras. El modelo se evaluara sobre
conjuntos de prueba y reportara metricas agregadas, nunca predicciones
vinculadas a un paciente.

## Entrenamiento (handoff RTX 5070)

Guia completa para la maquina de entrenamiento: `docs/ml-training-handoff.md`.
Resumen de comandos (desde la raiz del repositorio):

```bash
python ml/smoke_test.py                                   # validacion sin GPU
python ml/dataset/prepare.py
python ml/training/train.py --model mobilenetv3 --preset ml/configs/experiments/initial.yaml --device cuda
python ml/training/run_all.py --preset ml/configs/experiments/initial.yaml --device cuda
# Si ya existen artefactos de estos modelos, añadir --overwrite explícitamente.
python ml/evaluation/metrics.py --model mobilenetv3 --weights ml/models/mobilenetv3/best.pt
```

La preparacion divide solo las 5.600 imagenes de `Training/` con una
permutacion global `randperm`, semilla 42: train (80%, 4.480) y val (20%,
1.120). Conserva las 1.600 imagenes de `Testing/` como
test. Para otras rutas se pueden usar `--source` y `--dest`; entrenamiento y
evaluacion aceptan `--data-root`, tambien propagado por `run_all.py`.
