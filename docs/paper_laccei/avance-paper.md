# Avance del artículo científico (formato LACCEI)

> Estado: **borrador v0.3**. Secciones I–VI desarrolladas. Los resultados
> provienen de `ml/evaluation/reports/` (extraídos de los notebooks de
> entrenamiento con `extract_notebooks.py`); re-evaluar los checkpoints
> desplegados es un control opcional de reproducibilidad.

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

## IV. Resultados

Los cinco modelos se evaluaron una única vez sobre el conjunto de prueba
(1.600 imágenes) tras seleccionar la época por *accuracy* de validación. La
tabla siguiente resume el desempeño; la fuente completa y las matrices de
confusión están en `docs/tabla-comparativa.md` y `ml/evaluation/reports/`.

| Modelo | Params (M) | Tamaño (MB) | Exactitud | Macro F1 | Recall tumor | ROC-AUC OVR |
| --- | --- | --- | --- | --- | --- | --- |
| DenseNet121 | 7.98 | 27.12 | **87.56 %** | **87.41 %** | **84.00 %** | 0.9677 |
| MobileNetV3 | 5.48 | 16.25 | 87.19 % | 86.97 % | 83.08 % | 0.9710 |
| EfficientNetB0 | 5.29 | 15.59 | 87.06 % | 86.73 % | 82.75 % | **0.9711** |
| ResNet18 (ref.) | 11.69 | 42.72 | 85.69 % | 85.37 % | 81.42 % | 0.9644 |
| ShuffleNetV2 | 2.28 | 4.96 | 82.56 % | 82.15 % | 77.08 % | 0.9539 |

Observaciones:

- Las cuatro CNN ligeras superan o igualan a la referencia ResNet18 en exactitud
  y macro F1, con menos parámetros, salvo ShuffleNetV2.
- **Glioma es la clase más difícil** para todos los modelos (recall 0.68–0.71);
  *no tumor* es la más fácil (recall ≥ 0.99). El *recall* tumoral agregado está
  dominado por la detección de glioma.
- El Grad-CAM (`ml/evaluation/gradcam.py` y `backend/app/services/gradcam.py`)
  genera mapas por arquitectura; la validación cualitativa de coherencia con la
  lesión queda como revisión manual sobre un conjunto fijo de imágenes.

## V. Discusión

**Selección del modelo.** DenseNet121 obtiene las mejores métricas brutas
(exactitud, macro F1 y *recall* tumoral), pero es el más pesado (~8 M de
parámetros). MobileNetV3 y EfficientNetB0 están prácticamente empatados:
MobileNetV3 gana por un margen mínimo en exactitud y macro F1, y EfficientNetB0
en ROC-AUC y tamaño. Siguiendo el criterio declarado —exactitud/F1, *recall*
tumoral, tiempo de inferencia, tamaño y facilidad de conversión a TFLite, y
calidad del mapa de calor— **MobileNetV3** es la opción recomendada para el
despliegue móvil: ofrece un desempeño casi idéntico al líder con un modelo
menos de la mitad de pesado y diseñado explícitamente para dispositivos. La
medición de milisegundos por imagen requiere el mismo hardware de destino y se
deja como paso de validación.

**Integración.** El backend carga el checkpoint (`best.pt`) y ejecuta la
inferencia real y el Grad-CAM sin cambiar el contrato HTTP; el modo
`MOCK_INFERENCE` queda solo como respaldo cuando no hay pesos. Así, la capa de
modelo y la de software evolucionan de forma independiente.

**Limitaciones.** Los resultados provienen de una única partición de prueba; no
se realizó validación cruzada. Las métricas reportadas corresponden a la corrida
documentada; re-evaluar el *checkpoint* desplegado con el mismo manifiesto es un
control de reproducibilidad pendiente.

## VI. Conclusiones

1. Se compararon cinco arquitecturas bajo un protocolo homogéneo y reproducible
   (224×224, normalización ImageNet, *transfer learning* con *backbone*
   congelado, Adam, una partición fija con `seed=42`).
2. Las CNN ligeras alcanzan una exactitud competitiva (hasta 87.6 %) sin
   *fine-tuning* del *backbone*; MobileNetV3 ofrece el mejor equilibrio
   exactitud/tamaño para el despliegue móvil.
3. La decisión del modelo se interpreta con Grad-CAM por arquitectura, y el
   sistema se integra de extremo a extremo (datos → modelo → API → app).
4. Trabajo futuro: conversión a TFLite para inferencia *on-device*, validación
   cruzada, un conjunto de prueba más amplio y la re-evaluación de los
   *checkpoints* desplegados.

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
