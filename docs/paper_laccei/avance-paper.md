# Avance del artículo científico (formato LACCEI)

> Estado: **borrador v0.2**. Las secciones I–III están desarrolladas; los
> resultados (IV–V) esperan los pesos entrenados. Todo número es placeholder y
> se sustituye con la salida de `ml/evaluation/reports/`.

## Clasificación de tumores cerebrales en imágenes de resonancia magnética
## mediante CNN ligeras y Grad-CAM

**Autores.** *Integrantes del equipo — Universidad Nacional Mayor de San Marcos.*
**Área temática.** Ingeniería de software, inteligencia artificial aplicada a la salud.

### Resumen

Se propone un aplicativo móvil que apoya la clasificación multiclase de tumores
cerebrales (glioma, meningioma, tumor pituitario y ausencia de tumor) en
imágenes de resonancia magnética. Se comparan cuatro arquitecturas CNN ligeras
(MobileNetV3, EfficientNetB0, ShuffleNetV2 y DenseNet121) contra ResNet18 como
referencia, todas por *transfer learning* con pesos ImageNet y bajo un mismo
protocolo. La interpretabilidad se aborda con Grad-CAM y el despliegue con una
API REST consumida por una app Flutter con arquitectura MVVM. Los resultados
cuantitativos se incorporan en la versión final del manuscrito.

**Palabras clave.** tumores cerebrales, aprendizaje profundo, CNN, Grad-CAM,
aplicación móvil.

### Abstract

We propose a mobile application that supports multiclass classification of
brain tumors (glioma, meningioma, pituitary tumor, and no tumor) in MRI
images. Four lightweight CNN architectures (MobileNetV3, EfficientNetB0,
ShuffleNetV2, and DenseNet121) are compared against ResNet18 as a baseline,
all by transfer learning with ImageNet weights under a single protocol.
Interpretability uses Grad-CAM, and deployment uses a REST API consumed by a
Flutter app with MVVM architecture. Quantitative results are added in the
final manuscript.

**Keywords.** brain tumors, deep learning, CNN, Grad-CAM, mobile application.

## I. Introducción

Los tumores cerebrales primarios son una causa relevante de mortalidad y su
diagnóstico depende de la lectura de imágenes de resonancia magnética (MRI) por
un radiólogo. La escasez de especialistas en zonas con recursos limitados
motiva herramientas de apoyo al diagnóstico que prioricen la accesibilidad.

Este trabajo estudia si **arquitecturas CNN ligeras** pueden clasificar MRI de
cerebro con exactitud competitiva y costo de inferencia apto para un
dispositivo móvil, y si su decisión es **explicable** mediante mapas de calor.
El objetivo no es reemplazar al radiólogo sino ofrecer un apoyo educativo con
un aviso explícito de uso responsable.

**Objetivos específicos:**

- **OE1.** Identificar y evaluar arquitecturas CNN ligeras para la
  clasificación multiclase.
- **OE2.** Seleccionar la más adecuada según exactitud, tiempo de inferencia e
  interpretabilidad.
- **OE3.** Integrarla en un aplicativo móvil mediante comunicación
  cliente-servidor.
- **OE4.** Validar el rendimiento en un conjunto de prueba independiente y
  compararlo con el estado del arte.

## II. Trabajo relacionado

La revisión bibliográfica se registra en `docs/literatura/` y comprende los
trabajos [11]–[24] del manuscrito base. Los enfoques revisados usan
`ImageDataGenerator` (Keras/TensorFlow) como capa de aumento de datos; este
trabajo se aparta de esa elección por una razón de cobertura de modelos (ver
§III.C y `docs/notas-correccion-paper.md` §1).

## III. Metodología

### A. Dataset

Se usa el *Brain Tumor MRI Dataset* de Kaggle (Nickparvar): 5.600 imágenes de
entrenamiento + 1.600 de prueba, con cuatro clases nativas. Las subcategorías
de glioma se colapsan a `glioma`, de modo que las etiquetas coinciden con
`ml/configs/labels.json`. Solo el conjunto `Training/` se divide, con una
permutación global (`randperm`, `seed=42`), en **80 % entrenamiento / 20 %
validación**; las 1.600 imágenes de `Testing/` se conservan íntegras como
prueba. El manifiesto queda en `ml/data/processed/splits.json` para garantizar
reproducibilidad.

### B. Preprocesamiento y aumento de datos

Las imágenes se redimensionan a **224×224** y se convierten a RGB. Las cinco
arquitecturas comparten la **normalización de ImageNet**
(`mean=[0.485,0.456,0.406]`, `std=[0.229,0.224,0.225]`), declarada en
`ml/configs/<modelo>.yaml`. El tensor de entrada de PyTorch es `3×224×224`. El
aumento de datos usa `torchvision.transforms`: *flip* horizontal (`p=0.5`) y
rotación de hasta 10°; validación y prueba usan solo *resize*, *tensor* y la
misma normalización.

### C. Arquitecturas y protocolo de entrenamiento

Cinco modelos, todos provistos por **torchvision** con pesos ImageNet y la
misma cabeza lineal de 4 clases:

| Modelo | Arquitectura torchvision | Capa objetivo Grad-CAM |
| --- | --- | --- |
| MobileNetV3 | `mobilenet_v3_large` | `features[-1]` |
| EfficientNetB0 | `efficientnet_b0` | `features[-1]` |
| ShuffleNetV2 | `shufflenet_v2_x1_0` | `conv5` |
| DenseNet121 | `densenet121` | `features.denseblock4` |
| ResNet18 (ref.) | `resnet18` | `layer4[-1]` |

Protocolo común (`ml/training/train.py`): *transfer learning* con el
*backbone* congelado durante todo el entrenamiento —solo se optimiza la capa
de salida nueva—, optimizador **Adam** (`lr=1e-3`), `CrossEntropyLoss`, batch
64, hasta **100 épocas**, `seed=42`. La época se selecciona por *accuracy* de
validación. Se usó torchvision de forma uniforme porque provee las cinco
arquitecturas con pesos ImageNet equivalentes.

### D. Validación y métricas

Validación *holdout* **80/20** sobre `Training/` (la partición de prueba quedó
aislada). Se reportan: exactitud, macro precisión/recall/F1, F1 ponderado,
*recall* de la clase tumoral, ROC-AUC multiclase (uno-contra-resto), matriz de
confusión, milisegundos por imagen y número de parámetros. La
interpretabilidad se evalúa cualitativamente con Grad-CAM sobre un conjunto
fijo de imágenes de prueba.

### E. Integración móvil

El modelo ganador se expone como servicio REST (FastAPI, contrato JSON) y se
persiste solo el **hash SHA-256** de cada imagen junto a etiqueta, confianza,
versión del modelo y tiempo de inferencia. La app Flutter consume la API con
arquitectura **MVVM** (Model–View–ViewModel) y ofrece cuatro pantallas
consolidadas. La carga del modelo real (pesos torchvision + Grad-CAM) ya está
implementada en el backend; `MOCK_INFERENCE=true` actúa solo como respaldo
cuando no hay pesos en disco, para no bloquear el desarrollo del cliente. La
cuenta es opcional y usa **JWT real** con sesión persistente en el dispositivo.

## IV. Resultados (pendiente)

Se completará con la tabla comparativa de `docs/tabla-comparativa.md` y las
matrices de confusión de `ml/evaluation/reports/`. Placeholders:

| Modelo | Params (M) | Exactitud | Macro F1 | Recall tumor | ms/imagen |
| --- | --- | --- | --- | --- | --- |
| MobileNetV3 | — | — | — | — | — |
| EfficientNetB0 | — | — | — | — | — |
| ShuffleNetV2 | — | — | — | — | — |
| DenseNet121 | — | — | — | — | — |
| ResNet18 (ref.) | — | — | — | — | — |

## V. Discusión (pendiente)

Criterio de selección, en orden: exactitud y macro F1 sostenidos en los 5
folds; *recall* de la clase tumoral (el falso negativo es el error más grave);
tiempo de inferencia en el mismo hardware; tamaño del modelo y facilidad de
conversión a TFLite; y calidad del mapa Grad-CAM.

## VI. Conclusiones (pendiente)

Se redactarán tras la selección del modelo. Contribución anticipada: un
protocolo reproducible y homogéneo para comparar CNN ligeras, con
interpretabilidad y despliegue móvil de extremo a extremo, y un aviso de uso
responsable por tratarse de apoyo académico y no de un dispositivo médico.

## Referencias

Se mantendrán en el formato de la plantilla LACCEI. La lista vigente se
conserva en el manuscrito base; las notas de corrección entre el paper original
y el repositorio están en `docs/notas-correccion-paper.md`.

## Apéndice A — Correspondencia con el repositorio

| Sección del paper | Artefacto del repositorio |
| --- | --- |
| III.A Dataset | `ml/dataset/`, `docs/ml-training-handoff.md` |
| III.B Preprocesamiento | `ml/dataset/preprocessing.py`, `ml/configs/*.yaml` |
| III.C Arquitecturas | `ml/configs/`, `ml/training/train.py` |
| III.D Validación | `ml/training/train.py`, `ml/evaluation/metrics.py` |
| III.E Integración | `backend/`, `frontend/`, `docs/diseno-pantallas.md` |
| IV Resultados | `docs/tabla-comparativa.md`, `ml/evaluation/reports/` |
