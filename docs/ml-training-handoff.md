# Handoff: entrenamiento de los cinco modelos (máquina RTX 5070)

Guía para ejecutar el experimento comparativo en una máquina independiente.
Backend y frontend **no se tocan**: siguen funcionando con `MOCK_INFERENCE=true`.
La integración real vendrá después, cuando se elija el modelo ganador.

Modelos: MobileNetV3, EfficientNetB0, ShuffleNetV2, ResNet18 (referencia), DenseNet121.
Clases (`ml/configs/labels.json`, no modificar): `glioma`, `meningioma`, `pituitario`, `no_tumor`.

## 1. Requisitos

- Python 3.12, GPU NVIDIA con CUDA 12.8+ (RTX 5070 Blackwell: exige `torch>=2.7`).
- ~10 GB libres (dataset + pesos + reportes).
- Acceso a Kaggle para descargar el dataset (cuenta + ZIP descargado a mano).

## 2. Instalación

```bash
cd ml
python3.12 -m venv .venv && source .venv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements-ml.txt
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Notas:

- `requirements-ml.txt` pide `torch>=2.7`: la RTX 5070 no funciona con torch 2.5/CUDA 12.4.
- El nombre de distribución de Grad-CAM en PyPI es `grad-cam` (provee el módulo
  `pytorch_grad_cam`). Ya está corregido en el requirements.

## 3. Descarga del dataset

Dataset principal: **saeedi2023** (3264 imágenes, 4 clases nativas, el del artículo base).
Alternativa: **nickparvar2024** (7023 imágenes con subcategorías `glioma_*`, `pituitary*`,
`notumor`/`normal`: se normalizan solas a las 4 canónicas).

```bash
# Desde la RAIZ del repo. <zip> = archivo descargado de Kaggle.
python ml/dataset/download.py --dataset saeedi2023 --archive <zip> --flatten
# Deja las imagenes en ml/dataset/raw/saeedi2023/processed/
```

## 4. Preparación del dataset (UNA sola partición compartida)

Los cinco modelos entrenan sobre **los mismos splits físicos** (comparación justa).
Proporción fijada en el preset: **70% train / 15% val / 15% test, seed=42, estratificado**.

```bash
# Desde la RAIZ del repo:
python ml/dataset/prepare.py --source ml/dataset/raw/saeedi2023/processed --dest ml/dataset/processed
```

Verifica la salida: tabla de conteos por split y clase + `ml/dataset/processed/splits.json`
(manifiesto con seed, ratios y totales). Regenerar exige `--overwrite`.
No dupliques el dataset por modelo: `ml/training/dataloader.py` apunta a este único
`processed/` y valida el conjunto y el orden de clases contra `labels.json`,
remapeando los índices alfabéticos de `ImageFolder` al orden canónico.

Opcional (trazabilidad de la validación cruzada, no obligatorio para entrenar):

```bash
python ml/training/kfold.py --model mobilenetv3   # usa seed=42 y 5 folds del YAML
```

## 5. Smoke test (2 min, sin GPU, sin descargar pesos)

```bash
# Desde la RAIZ del repo:
python ml/smoke_test.py   # debe terminar 7/7 OK, exit 0
```

Comprueba: entorno, labels, `prepare.py` sintético, dataloader idéntico x5,
forward+backward x5, métricas y target layers de Grad-CAM. Si algo falla aquí,
no sigas: reporta el fallo.

## 6. Entrenar UN modelo

```bash
# Desde la RAIZ del repo. Ejemplo con el baseline de referencia:
python ml/training/train.py --model resnet18 --preset ml/configs/experiments/initial.yaml --device cuda
```

Flags útiles: `--epochs N`, `--batch-size N`, `--device cuda|cpu|auto`, `--seed N`,
`--data-root <processed alternativo>`, `--fold N` (solo informativo junto a kfold).
Hiperparámetros del preset (`ml/configs/experiments/initial.yaml`, no editar sin motivo):
epochs 30, batch 32, AdamW lr=1e-4 wd=1e-4, scheduler cosine, early stopping paciencia 7,
seed 42. Transfer learning: backbone congelado (head entrenable) hasta la época 15,
luego fine-tuning completo.

## 7. Entrenar LOS CINCO (experimento oficial)

```bash
# Desde la RAIZ del repo, una sola línea:
python ml/training/run_all.py --preset ml/configs/experiments/initial.yaml --device cuda
```

Variantes: `--models mobilenetv3 resnet18` (subconjunto), `--skip-train` (solo evaluar),
`--skip-eval` (solo entrenar). Al final escribe `ml/evaluation/reports/comparison.json`
e imprime la tabla comparativa. Equivalente manual por modelo: el comando de la
sección 6 con `--model <uno-de-los-cinco>`.

Detalle relevante: ShuffleNetV2 se construye con **torchvision** (`shufflenet_v2_x1_0`,
pesos `IMAGENET1K_V1`) porque timm 1.x no incluye ningún ShuffleNet. El esquema
freeze→fine-tuning, el head de 4 clases con dropout 0.3 y las condiciones de
entrenamiento son las mismas que en los otros cuatro.

## 8. Evaluación

Automática dentro de `run_all.py`. Manual por modelo:

```bash
python ml/evaluation/metrics.py --model <nombre> --weights ml/models/<nombre>/best.pt
```

Genera `ml/evaluation/reports/<nombre>_metrics.json` con: accuracy, macro
precision/recall/F1, weighted F1, tumor recall, tumor sensitivity, specificity
no_tumor, confusion matrix, classification report, ms/imagen, nº de parámetros
y tamaño del checkpoint en MB. Con esos JSON se rellena `docs/tabla-comparativa.md`
(la columna "Apto móvil" NO se calcula: criterio posterior, no automático).

## 9. Grad-CAM

Una vez exista `best.pt`, con una imagen cualquiera del test:

```bash
python ml/evaluation/gradcam.py --model <nombre> \
    --weights ml/models/<nombre>/best.pt \
    --image ml/dataset/processed/test/glioma/<archivo>.png \
    --output ml/evaluation/reports/<nombre>_ejemplo.png
```

El target layer correcto por arquitectura ya está en cada `ml/configs/<modelo>.yaml`
(`conv_head`, `conv5`, `layer4[-1]`, `features.denseblock4`); el script lo resuelve
solo. Guarda el PNG y muestra la clase predicha.

## 10. Dónde queda cada resultado

```text
ml/models/<modelo>/best.pt          checkpoint ganador (gitignored)
ml/models/<modelo>/history.json     curva train_loss/val_loss/val_acc por época
ml/models/<modelo>/metadata.json    contrato para backend (ver sección 11)
ml/evaluation/reports/<modelo>_metrics.json   métricas + matriz + tiempos + params
ml/evaluation/reports/comparison.json         fila resumen por modelo
ml/evaluation/reports/<modelo>_*.png          ejemplos Grad-CAM
ml/dataset/processed/splits.json    manifiesto de la partición usada
```

## 11. Qué entregarme al finalizar

1. Los 5 `best.pt` + sus `metadata.json` (o el del modelo ganador si así se acuerda).
2. Los 5 `<modelo>_metrics.json` + `comparison.json`.
3. `splits.json` del `processed/` usado (o confirmación de que es el regenerado con seed 42).
4. 1 PNG Grad-CAM por modelo sobre imagen de test (misma imagen idealmente).
5. La tabla `docs/tabla-comparativa.md` rellena (solo columnas medidas).
6. Nota de cualquier desviación del preset (épocas reales por early stopping,
   incidencias de GPU, tiempos aproximados por modelo).

### Contrato `metadata.json` (lo que backend consumirá después)

```json
{
  "model": "mobilenetv3",
  "version": "mobilenetv3-v1",
  "timm_name": "mobilenetv3_large_100",
  "classes": ["glioma", "meningioma", "pituitario", "no_tumor"],
  "num_classes": 4,
  "input_size": 256,
  "normalization": {"mode": "tanh", "mean": [0.5, 0.5, 0.5], "std": [0.5, 0.5, 0.5]},
  "best_val_accuracy": 0.93,
  "epoch": 22
}
```

Backend aún NO lo consume (sigue en mock). No modificar `backend/` ni `frontend/`.
