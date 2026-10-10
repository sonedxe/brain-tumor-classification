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
- **OE4.** Validar el rendimiento con validación cruzada y compararlo con el
  estado del arte.

## II. Trabajo relacionado

La revisión bibliográfica se registra en `docs/literatura/` y comprende los
trabajos [11]–[24] del manuscrito base. Los enfoques revisados usan
`ImageDataGenerator` (Keras/TensorFlow) como capa de aumento de datos; este
trabajo se aparta de esa elección por una razón de cobertura de modelos (ver
§III.C y `docs/notas-correccion-paper.md` §1).

## III. Metodología

### A. Dataset

Se usa el conjunto público de 3.264 imágenes con cuatro clases nativas
(*Saeedi et al.*), con la alternativa de 7.023 imágenes de Kaggle cuyas
subcategorías de glioma se colapsan a `glioma`. La partición es única y
compartida por los cinco modelos: **70 % entrenamiento / 15 % validación /
15 % prueba, estratificada, `seed=42`**. El manifiesto queda en
`ml/dataset/processed/splits.json` para garantizar reproducibilidad.

### B. Preprocesamiento y aumento de datos

Las imágenes se redimensionan a **256×256** y se convierten a RGB. La
normalización se define **por modelo** en `ml/configs/<modelo>.yaml`: rango
[-1, 1] (`mean=std=0.5`) para MobileNetV3, EfficientNetB0, ShuffleNetV2 y
DenseNet121, y medias/desviaciones de ImageNet para ResNet18. El tensor de
entrada de PyTorch es `3×256×256`. El aumento de datos usa
`torchvision.transforms` (rotación, zoom, *flip* horizontal).

### C. Arquitecturas y protocolo de entrenamiento

Cinco modelos, mismo *head* de 4 clases con `Dropout(0.3)`:

| Modelo | Fuente de pesos | Capa objetivo Grad-CAM |
| --- | --- | --- |
| MobileNetV3 | timm (`mobilenetv3_large_100`) | `conv_head` |
| EfficientNetB0 | timm | `conv_head` |
| ShuffleNetV2 | torchvision (`shufflenet_v2_x1_0`) | `conv5` |
| DenseNet121 | timm | `features.denseblock4` |
| ResNet18 (ref.) | timm | `layer4[-1]` |

Protocolo común: transfer learning con *backbone* congelado hasta la época 15 y
*fine-tuning* completo después; AdamW (`lr=1e-4`, `wd=1e-4`), scheduler
coseno, *early stopping* con paciencia 7, 30 épocas como máximo, `seed=42`.
ShuffleNetV2 se construye con torchvision porque timm 1.x no lo incluye.

### D. Validación y métricas

Validación cruzada estratificada de **5 folds** sobre el entrenamiento. Se
reportan: exactitud, macro precisión/recall/F1, F1 ponderado, *recall* de la
clase tumoral, especificidad de `no_tumor`, matriz de confusión, milisegundos
por imagen, número de parámetros y tamaño del checkpoint. La interpretabilidad
se evalúa cualitativamente con Grad-CAM sobre un conjunto fijo de imágenes de
prueba.

### E. Integración móvil

El modelo ganador se expone como servicio REST (FastAPI, contrato JSON) y se
persiste solo el **hash SHA-256** de cada imagen junto a etiqueta, confianza,
versión del modelo y tiempo de inferencia. La app Flutter consume la API con
arquitectura **MVVM** (Model–View–ViewModel) y ofrece cuatro pantallas
consolidadas. Mientras el modelo definitivo no esté disponible, la API opera
con `MOCK_INFERENCE=true` (predicción ficticia determinista) para no bloquear
el desarrollo del cliente.

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
| III.D Validación | `ml/training/kfold.py`, `ml/evaluation/metrics.py` |
| III.E Integración | `backend/`, `frontend/`, `docs/diseno-pantallas.md` |
| IV Resultados | `docs/tabla-comparativa.md`, `ml/evaluation/reports/` |
