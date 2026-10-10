# Handoff: entrenamiento de los cinco modelos (Windows / CUDA 13.0)

Guía para ejecutar el experimento comparativo en una máquina independiente.
Backend y frontend **no se tocan**: siguen funcionando con `MOCK_INFERENCE=true`.
La integración real vendrá después, cuando se elija el modelo ganador.

Modelos: MobileNetV3, EfficientNetB0, ShuffleNetV2, ResNet18 (referencia), DenseNet121.
Clases (`ml/configs/labels.json`, no modificar): `glioma`, `meningioma`, `pituitario`, `no_tumor`.

## 1. Requisitos

- Python 3.12.
- Para GPU: Windows, GPU NVIDIA y controladores compatibles con CUDA 13.0.
- Para otros equipos o validaciones breves: la variante CPU.
- ~10 GB libres (dataset + pesos + reportes) y acceso a Kaggle para descargar
  el dataset de Masoud Nickparvar.

## 2. Instalación en Windows (PowerShell)

Ejecuta desde la raíz del repositorio. Instala primero el par exacto de PyTorch
y torchvision desde el índice oficial de la variante elegida. El archivo
`ml/requirements-ml.txt` contiene solo dependencias generales y excluye ambos
paquetes, de modo que el segundo paso no sustituye la variante CUDA o CPU.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
# GPU NVIDIA, CUDA 13.0: índice oficial de PyTorch
.\.venv\Scripts\python.exe -m pip install torch==2.14.1+cu130 torchvision==0.29.1+cu130 --index-url https://download.pytorch.org/whl/cu130
.\.venv\Scripts\python.exe -m pip install -r ml/requirements-ml.txt
```

Para ejecutar los comandos `python ...` de las secciones siguientes, activa el
entorno en la sesión de PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell no permite activar scripts, prefija esos comandos con
`.\.venv\Scripts\python.exe` en lugar de `python`.

Para CPU, usa este primer comando en lugar del comando CUDA y después instala
el mismo requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.14.1+cpu torchvision==0.29.1+cpu --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r ml/requirements-ml.txt
```

Comprueba las versiones y dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe -c "import torch, torchvision; print('torch', torch.__version__, 'torchvision', torchvision.__version__, 'CUDA', torch.cuda.is_available())"
.\.venv\Scripts\python.exe -m pip check
```

PyTorch publica el par CUDA 13.0 y su variante CPU para Windows. No se instala
`torchaudio`, porque el proyecto no lo utiliza. El nombre de distribución de
Grad-CAM en PyPI es `grad-cam` (provee el módulo `pytorch_grad_cam`). La receta
está documentada, pero no se ha ejecutado en este entorno.

## 3. Ubicación del dataset

Descarga el Brain Tumor MRI Dataset de Masoud Nickparvar desde Kaggle y coloca
sus imágenes originales dentro de `ml/data/raw/`, conservando esta estructura:

```text
ml/data/raw/
├── Training/
│   ├── glioma/
│   ├── meningioma/
│   ├── pituitary/
│   └── notumor/
└── Testing/
    ├── glioma/
    ├── meningioma/
    ├── pituitary/
    └── notumor/
```

Los datos originales y preparados están excluidos de Git. No se requiere la
carpeta experimental. Las clases `pituitary` y `notumor` se normalizan como
`pituitario` y `no_tumor` según `ml/configs/labels.json`.

```bash
# Opcional: el descargador extrae el ZIP bajo ml/data/raw/<dataset>/original/.
python ml/dataset/download.py --dataset nickparvar2024 --archive <zip>
```

Si extraes con ese comando, pasa `ml/data/raw/nickparvar2024/original` como
`--source`; para usar los valores predeterminados, coloca `Training/` y
`Testing/` directamente dentro de `ml/data/raw/`.

## 4. Preparacion del dataset (splits compartidos)

Los cinco modelos entrenan sobre los mismos splits. Solo `Training/` se divide
con una permutacion global `randperm`, seed=42: 80% train / 20% val. Las 1.600 imagenes de
`Testing/` se conservan integras como test y no seleccionan checkpoints.

```bash
# Desde la RAIZ del repo:
python ml/dataset/prepare.py
```

Verifica la salida: tabla de conteos por split y clase + `ml/data/processed/splits.json`
(manifiesto con seed, ratios y totales). Regenerar exige `--overwrite`.
No dupliques el dataset por modelo: `ml/training/dataloader.py` apunta a este unico
`processed/` y valida el conjunto y el orden de clases contra `labels.json`,
remapeando los indices alfabeticos de `ImageFolder` al orden canunico.

Opcional (trazabilidad de la validacion cruzada, no obligatorio para entrenar):

```bash
python ml/training/kfold.py --model mobilenetv3
```

## 5. Validacion rapida

```bash
python ml/smoke_test.py
```

El smoke test usa imagenes sinteticas y pesos aleatorios: valida aliases de
clase, reproducibilidad de la particion, que no se sobrescriba un destino,
construccion de las cinco arquitecturas, cuatro logits, cabeza entrenable,
forward/backward, una epoca sintetica de train/validacion, metricas y Grad-CAM.
No usa el conjunto real ni ejecuta el test para seleccionar checkpoints.

## 6. Entrenar un modelo

```bash
python ml/training/train.py --model resnet18 --preset ml/configs/experiments/initial.yaml --device cuda
```

Usa batch 64, hasta 100 epocas, Adam con learning rate 0.001 y CrossEntropyLoss.
Para una corrida corta de comprobacion se puede pasar `--epochs 1`. Si ya existe
`ml/models/resnet18/best.pt` o su historial, la ejecucion se detiene; agrega
`--overwrite` para autorizar reemplazarlos. `--data-root` permite indicar otro
processed/.

## 7. Entrenar los cinco modelos

```bash
python ml/training/run_all.py --preset ml/configs/experiments/initial.yaml --device cuda
```

Opcional: `--data-root <ruta>` para una particion procesada alternativa y
`--overwrite` para autorizar el reemplazo de artefactos de entrenamiento por
arquitectura. Los informes de evaluación se guardan en un directorio único por
ejecución y no reemplazan resultados anteriores. `--skip-eval` omite test y no
lee informes anteriores ni escribe una comparación.
Tambien se aceptan `--models mobilenetv3 resnet18`, `--skip-train` y
`--skip-eval`. Cada arquitectura tiene su propio directorio `ml/models/<modelo>/`.

Todos usan torchvision y sus pesos ImageNet. ShuffleNetV2 usa
`shufflenet_v2_x1_0`; MobileNetV3 usa MobileNetV3 Large. Cada una reemplaza su
cabeza segun la API de torchvision y entrena solo la capa de salida nueva.

## 8. Evaluacion

`run_all.py` evalua cada checkpoint en el split test despues de completar el
entrenamiento de esa arquitectura. Si su entrenamiento falla, no evalua ningun
checkpoint previo de ese modelo. Para evaluar manualmente un modelo:

```bash
python ml/evaluation/metrics.py --model resnet18 --weights ml/models/resnet18/best.pt
```

El comando manual se detiene si ya existe `resnet18_metrics.json`; usa
`--overwrite-report` solo si deseas reemplazarlo. `run_all.py` pasa un directorio
de salida único por ejecución y guarda allí los informes y `comparison.json`.

Guarda un JSON por arquitectura en `ml/evaluation/reports/` con accuracy,
precision/recall/F1 macro y weighted, matriz de confusion, reporte por clase,
ROC-AUC multiclase one-vs-rest macro y AUC por clase cuando se puedan calcular.
El test solo se usa en esta evaluacion final, nunca para escoger la epoca.

## 9. Grad-CAM

Una vez exista `best.pt`, con una imagen cualquiera del test:

```bash
python ml/evaluation/gradcam.py --model <nombre> \
    --weights ml/models/<nombre>/best.pt \
    --image ml/data/processed/test/glioma/<archivo>.png \
    --output ml/evaluation/reports/<nombre>_ejemplo.png
```

El target layer correcto por arquitectura ya está en cada `ml/configs/<modelo>.yaml`
(`conv_head`, `conv5`, `layer4[-1]`, `features.denseblock4`); el script lo resuelve
solo. Guarda el PNG y muestra la clase predicha.

## 10. Artefactos por arquitectura

```text
ml/models/<modelo>/best.pt                 checkpoint elegido por val_accuracy
ml/models/<modelo>/history.json            historial train/validacion
ml/models/<modelo>/metadata.json           arquitectura, clases, preproceso y checkpoint
ml/evaluation/reports/runs/<run-id>/<modelo>_metrics.json metricas y matriz
ml/evaluation/reports/runs/<run-id>/comparison.json      resumen de esta ejecucion
ml/data/processed/splits.json              archivos y huella de la particion
```

## 11. Qué entregarme al finalizar

1. Los 5 `best.pt` + sus `metadata.json` (o el del modelo ganador si así se acuerda).
2. Los 5 `<modelo>_metrics.json` + `comparison.json`.
3. `splits.json` del `processed/` usado (o confirmación de que es el regenerado con seed 42).
4. 1 PNG Grad-CAM por modelo sobre imagen de test (misma imagen idealmente).
5. La tabla `docs/tabla-comparativa.md` rellena (solo columnas medidas).
6. Nota de cualquier desviacion del protocolo, incidencias de GPU y tiempos aproximados por modelo.

### Contrato `metadata.json` (lo que backend consumirá después)

```json
{
  "architecture": "mobilenetv3",
  "torchvision_name": "mobilenet_v3_large",
  "classes": ["glioma", "meningioma", "pituitario", "no_tumor"],
  "class_to_idx": {"glioma": 0, "meningioma": 1, "pituitario": 2, "no_tumor": 3},
  "input_size": 224,
  "normalization": {"mode": "imagenet", "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
  "best_val_accuracy": null,
  "epoch": null
}
```

Backend aún NO lo consume (sigue en mock). No modificar `backend/` ni `frontend/`.
