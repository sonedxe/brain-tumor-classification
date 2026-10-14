# Informe de Proyecto

## Clasificación de tumores cerebrales en imágenes de resonancia magnética mediante CNN ligeras, Grad-CAM y una aplicación móvil con arquitectura MVVM

---

**Universidad:** Universidad Nacional Mayor de San Marcos
**Facultad / Escuela:** Ingeniería de Sistemas e Informática *(ajustar)*
**Curso:** Taller de Desarrollo de Proyectos de Software *(ajustar)*
**Docente:** Ing. *(ajustar)*
**Integrantes:** *(completar nombres y códigos)*
**Semana del avance:** 7
**Fecha:** Octubre de 2026

---

## Índice

1. [Resumen](#1-resumen)
2. [Introducción](#2-introducción)
3. [Planteamiento del problema](#3-planteamiento-del-problema)
4. [Objetivos](#4-objetivos)
5. [Justificación](#5-justificación)
6. [Marco teórico](#6-marco-teórico)
7. [Metodología de desarrollo](#7-metodología-de-desarrollo)
8. [Desarrollo e implementación](#8-desarrollo-e-implementación)
9. [Resultados](#9-resultados)
10. [Discusión](#10-discusión)
11. [Conclusiones](#11-conclusiones)
12. [Recomendaciones y trabajo futuro](#12-recomendaciones-y-trabajo-futuro)
13. [Referencias](#13-referencias)
14. [Anexos](#14-anexos)

---

## 1. Resumen

El presente informe documenta el avance del proyecto **Clasificación de tumores
cerebrales en imágenes de resonancia magnética (MRI)**, cuyo propósito es apoyar
la identificación automática de cuatro categorías —glioma, meningioma, tumor
pituitario y ausencia de tumor— mediante aprendizaje profundo, y poner ese
resultado a disposición del usuario final a través de una aplicación móvil.

El proyecto compara cuatro arquitecturas de red neuronal convolucional (CNN)
ligeras —MobileNetV3, EfficientNetB0, ShuffleNetV2 y DenseNet121— contra
ResNet18 como modelo de referencia, todas bajo un protocolo homogéneo de
*transfer learning* con pesos ImageNet y sobre una partición única y
reproducible del conjunto de datos. La interpretabilidad del modelo se aborda
mediante mapas de calor **Grad-CAM**, y el despliegue se resuelve con una
arquitectura cliente–servidor: una API REST en FastAPI que ejecuta la
inferencia y persiste únicamente el *hash* de la imagen, y una aplicación
**Flutter** construida bajo el patrón **MVVM**.

El estado actual corresponde a la **semana 8**. El pipeline de entrenamiento,
la API, la aplicación móvil y su documentación están implementados y
verificados. La inferencia real (carga de pesos + Grad-CAM) está implementada y
en funcionamiento, sin cambiar el contrato HTTP.

**Palabras clave:** tumores cerebrales, aprendizaje profundo, CNN, Grad-CAM,
MVVM, Flutter, FastAPI, Scrum.

## 2. Introducción

Los tumores cerebrales constituyen una de las patologías neurológicas de mayor
impacto en la mortalidad y en la calidad de vida de los pacientes. Su
diagnóstico se apoya fuertemente en la lectura de imágenes de resonancia
magnética por parte de un médico radiólogo, un recurso especializado que no
siempre está disponible, especialmente en establecimientos de salud con
recursos limitados.

En este contexto, las técnicas de aprendizaje profundo han demostrado ser
capaces de clasificar imágenes médicas con un desempeño cercano al humano en
tareas acotadas. Sin embargo, trasladar un modelo experimental a una herramienta
que un profesional pueda usar plantea tres retos que este proyecto aborda de
forma conjunta:

1. **Eficiencia computacional:** el modelo debe poder ejecutarse en un entorno
   de servidor modesto y, a futuro, en un dispositivo móvil.
2. **Explicabilidad:** el especialista debe poder ver *por qué* el modelo tomó
   una decisión, no solo la clase asignada.
3. **Integración de software:** el modelo debe quedar embebido en un sistema
   real, con interfaz de usuario, comunicación cliente–servidor y trazabilidad.

El proyecto integra estos tres aspectos y, de manera transversal, aplica una
metodología ágil (**Scrum**) y produce como entregable académico un artículo
científico.

> **Aviso de uso responsable.** La herramienta tiene fines académicos y de
> apoyo. **No constituye un dispositivo médico ni sustituye el criterio de un
> radiólogo.** No se persiste ningún dato que permita reidentificar a un
> paciente.

## 3. Planteamiento del problema

Actualmente, un radiólogo debe revisar manualmente cada estudio de resonancia
magnética, lo que demanda tiempo y depende de su disponibilidad. La detección
tardía o la falta de una segunda lectura puede retrasar decisiones clínicas.
Por otro lado, existen múltiples arquitecturas de aprendizaje profundo, pero no
es evidente cuál ofrece el mejor equilibrio entre **exactitud**, **tiempo de
inferencia** e **interpretabilidad** en el escenario concreto de cuatro clases
y recursos limitados.

Se plantea entonces la siguiente pregunta de investigación:

> ¿Es posible construir un aplicativo móvil de apoyo que clasifique cuatro
> tipos de hallazgos en imágenes de MRI con una CNN ligera, cuyo desempeño sea
> competitivo y cuya decisión sea explicable, empleando un desarrollo guiado por
> una metodología ágil?

## 4. Objetivos

**Objetivo general**

Desarrollar un aplicativo móvil de apoyo al diagnóstico que clasifique
multiclase tumores cerebrales en imágenes de resonancia magnética mediante
redes neuronales convolucionales ligeras, con interpretabilidad mediante
Grad-CAM y comunicación cliente–servidor.

**Objetivos específicos**

| Código | Objetivo específico |
| --- | --- |
| **OE1** | Identificar y evaluar arquitecturas CNN ligeras para la clasificación multiclase de tumores cerebrales en MRI. |
| **OE2** | Seleccionar el modelo más adecuado según exactitud, tiempo de inferencia e interpretabilidad con Grad-CAM. |
| **OE3** | Integrar el modelo seleccionado en un aplicativo móvil mediante comunicación cliente–servidor. |
| **OE4** | Validar el rendimiento en un conjunto de prueba independiente y compararlo con el estado del arte. |

## 5. Justificación

- **Académica:** el proyecto permite aplicar, sobre un caso real, conocimientos
  de aprendizaje profundo, visión por computador, arquitectura de software,
  desarrollo móvil y metodologías ágiles.
- **Social:** una herramienta de apoyo que prioriza el *recall* de la clase
  tumoral (reducir los falsos negativos) puede contribuir a un tamizaje más
  rápido donde escasean especialistas.
- **Técnica:** la comparación homogénea de cinco arquitecturas y el énfasis en
  la reproducibilidad (partición fija, semillas, manifiestos) producen evidencia
  objetiva para elegir un modelo desplegable.
- **Formativa:** el proyecto obliga a integrar tres capas (ML, backend y
  frontend) bajo una misma definición de "terminado", lo que simula el trabajo
  real de un equipo de desarrollo.

## 6. Marco teórico

### 6.1 Redes neuronales convolucionales (CNN)

Una CNN es una arquitectura de aprendizaje profundo diseñada para datos con
estructura de rejilla, como las imágenes. Mediante capas de convolución,
*pooling* y funciones de activación, extrae de forma jerárquica características
locales (bordes, texturas) y luego globales (formas, lesiones). En
clasificación, la salida final es una distribución de probabilidad sobre las
clases mediante la función *softmax*.

### 6.2 Transfer learning

El *transfer learning* reutiliza un modelo previamente entrenado en un dominio
grande (por ejemplo, ImageNet) y lo adapta a uno nuevo y más pequeño. En lugar
de entrenar desde cero con pocas imágenes —insuficientes para converger—, se
congela el *backbone* preentrenado y se entrena únicamente una cabeza
clasificadora nueva. Esto da una ventaja de convergencia y una comparación más
justa entre arquitecturas.

### 6.3 Arquitecturas ligeras

| Modelo | Idea central | Relevancia para móvil |
| --- | --- | --- |
| **MobileNetV3** | Convoluciones separables en profundidad + *squeeze-and-excitation* | Muy bajo costo |
| **EfficientNetB0** | Escalado compuesto equilibrado de profundidad, ancho y resolución | Buen accuracy/parámetro |
| **ShuffleNetV2** | *Channel shuffle* y convoluciones agrupadas | Muy eficiente en cómputo |
| **DenseNet121** | Conexiones densas entre capas | Reutilización de features |
| **ResNet18** | Conexiones residuales (*skip connections*) | Referencia estándar |

> Se eligió **torchvision** como biblioteca principal porque provee las cinco
> arquitecturas (`mobilenet_v3_large`, `efficientnet_b0`, `shufflenet_v2_x1_0`,
> `densenet121` y `resnet18`) con pesos ImageNet equivalentes bajo una misma
> API.

### 6.4 Grad-CAM

Grad-CAM (*Gradient-weighted Class Activation Mapping*) genera un mapa de calor
que resalta las regiones de la imagen que más contribuyeron a la clase
predicha, usando los gradientes de la clase respecto de la última capa
convolucional. Es un mecanismo de **interpretabilidad póstuma** y no requiere
modificar el modelo. La capa objetivo difiere por arquitectura, por lo que se
define en la configuración de cada modelo.

### 6.5 Patrón MVVM

Model–View–ViewModel separa la interfaz de la lógica:

- **Model:** datos y reglas de negocio (DTOs, repositorios, servicios).
- **ViewModel:** estado y reglas que la vista observa; notifica cambios.
- **View:** presentación y captura de intenciones del usuario; no contiene
  lógica de red ni de negocio.

Su ventaja es la **testeabilidad**: la lógica se prueba sin levantar la
interfaz, y el acceso a red se sustituye por objetos simulados.

### 6.6 Arquitectura cliente–servidor y API REST

El modelo se expone como servicio REST; el cliente móvil envía la imagen por
HTTP y recibe un objeto JSON con la clase, la confianza, las probabilidades y
la ruta del mapa de calor. Esta separación permite actualizar el modelo en el
servidor sin recompilar la aplicación.

### 6.7 Metodología ágil: Scrum

Scrum organiza el trabajo en iteraciones (*sprints*) con un *Product Backlog*
priorizado, eventos definidos (planificación, revisión, retrospectiva) y una
*Definition of Done* común. Es adecuado porque el proyecto contiene
incertidumbre técnica (qué modelo será mejor, si el dataset alcanza) que solo
se resuelve experimentando.

## 7. Metodología de desarrollo

El proyecto se ejecuta con **Scrum** con una cadencia de **una semana por
sprint**. La revisión se realiza en la sesión remota del sábado. El detalle
completo está en `docs/scrum/`.

### 7.1 Roles

| Rol | Responsabilidad |
| --- | --- |
| Product Owner | Prioriza el backlog y acepta los incrementos |
| Scrum Master (rotativo) | Facilita las ceremonias y elimina impedimentos |
| Development Team | Diseña, implementa, entrena y valida |

### 7.2 Ceremonias y artefactos

Ceremonias: *Sprint Planning*, avance diario, *Sprint Review* y retrospectiva.
Artefactos: *Product Backlog*, *Sprint Backlog*, el **incremento** (repositorio)
y la *Definition of Done*.

### 7.3 Fases técnicas

| Fase | Contenido | Objetivo |
| --- | --- | --- |
| F1 | Revisión bibliográfica y alcance | OE1 |
| F2 | Preprocesamiento y exploración de datos | OE1 |
| F3 | Entrenamiento de los cinco modelos | OE1, OE4 |
| F4 | Evaluación, selección e interpretabilidad | OE2, OE4 |
| F5 | Integración móvil | OE3 |

### 7.4 Estrategia de mitigación del riesgo

La Fase 5 depende de la Fase 4 (no hay pesos hasta elegir el modelo). Para no
bloquear el desarrollo del cliente, el backend se desarrolló en paralelo con una
respuesta simulada determinista a partir del contenido de la imagen. Así, ML,
backend y frontend avanzaron en paralelo y la integración real quedó reducida a
cargar los pesos, ya implementada.

## 8. Desarrollo e implementación

### 8.1 Arquitectura general del sistema

```
┌──────────────────────┐        HTTP / JSON        ┌─────────────────────────┐
│  frontend/           │  ───────────────────────► │  backend/               │
│  Flutter (MVVM)      │   POST /api/v1/predict    │  FastAPI                │
│                      │  ◄─────────────────────── │  + SQLite               │
│  Model / ViewModel / │   { label, confidence,    │  + inferencia           │
│  View                │     probabilities,        │  + Grad-CAM             │
└──────────┬───────────┘     gradcam_path }         └───────────┬─────────────┘
           │                                                  │
           │  la imagen se carga,                             │  lee pesos
           │  nunca se envían datos                           ▼
           │  identificables del paciente         ┌─────────────────────────┐
           │                                      │  ml/                    │
           │                                      │  PyTorch + torchvision   │
           └─────────────────────────────────────►└─────────────────────────┘
                                                    SQLite (historial)
```

### 8.2 Capa de machine learning (`ml/`)

- **Dataset:** *Brain Tumor MRI Dataset* de Kaggle (Nickparvar), 5.600
  imágenes de entrenamiento + 1.600 de prueba, con las subcategorías de glioma
  colapsadas a `glioma` según `ml/configs/labels.json`.
- **Partición:** solo `Training/` se divide con una permutación global
  (`randperm`, `seed=42`) en 80 % entrenamiento / 20 % validación; las 1.600
  imágenes de `Testing/` se conservan íntegras como prueba. Manifiesto en
  `ml/data/processed/splits.json`.
- **Preprocesamiento:** redimensionado a 224×224, conversión a RGB y
  normalización de ImageNet compartida por las cinco arquitecturas. Tensor de
  entrada `3×224×224`.
- **Aumento de datos:** `torchvision.transforms` (*flip* horizontal `p=0.5` y
  rotación de 10°); validación y prueba sin aumentos.
- **Entrenamiento:** *transfer learning* con el *backbone* congelado durante
  todo el entrenamiento (solo se entrena la cabeza de 4 clases); optimizador
  **Adam** (`lr=1e-3`), `CrossEntropyLoss`, batch 64, hasta 100 épocas, semilla
  42. La época se selecciona por *accuracy* de validación.
- **Validación:** *holdout* 80/20 sobre `Training/`; `Testing/` permanece
  aislado y no selecciona checkpoints.
- **Evaluación:** exactitud, macro precisión/recall/F1, F1 ponderado, *recall*
  tumoral, ROC-AUC multiclase (uno-contra-resto), matriz de confusión, ms/imagen
  y número de parámetros.
- **Interpretabilidad:** Grad-CAM con capa objetivo por arquitectura
  (`features[-1]`, `conv5`, `features.denseblock4`, `layer4[-1]`).

### 8.3 Capa de backend (`backend/`)

API REST en **FastAPI** con persistencia **SQLite** vía SQLAlchemy.

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/api/v1/predict` | Clasifica una imagen MRI |
| `GET` | `/api/v1/history` | Últimas predicciones |
| `GET` | `/api/v1/health` | Estado del servicio y del modelo |
| `POST` | `/api/v1/auth/register` | Registro de cuenta (JWT real) |
| `POST` | `/api/v1/auth/login` | Inicio de sesión (JWT real) |
| `GET` | `/api/v1/auth/me` | Usuario autenticado (valida el JWT) |

Contrato de `POST /api/v1/predict`:

```json
{
  "label": "meningioma",
  "confidence": 0.97,
  "probabilities": {
    "glioma": 0.01, "meningioma": 0.97, "pituitario": 0.01, "no_tumor": 0.01
  },
  "gradcam_path": "/static/gradcam/9f2a.png",
  "model_version": "mobilenetv3-v1",
  "inference_ms": 82.4
}
```

**Privacidad:** la tabla `prediction_logs` guarda únicamente
`image_hash` (SHA-256), `label`, `confidence`, `model_version`,
`inference_ms` y `created_at`. No se almacenan nombres, metadatos DICOM ni el
nombre original del archivo.

### 8.4 Capa de frontend (`frontend/`)

Aplicación **Flutter** con patrón **MVVM** y una estructura por capas:

```
lib/
├── core/            # configuración (URL de la API) y tema
├── data/
│   ├── models/      # DTOs: PredictionModel, HistoryEntry
│   ├── repositories/# une modelo + servicio
│   └── services/    # ApiService, AuthService y SessionStore (persistencia)
├── viewmodels/      # Prediction, History y Auth (estado + reglas)
├── views/           # Analizar, Historial, Info, Cuenta
└── widgets/         # componentes de presentación
```

Regla de diseño: **ninguna vista hace HTTP, parsea JSON ni lee archivos**; solo
observa el ViewModel y emite intenciones. El acceso a red es inyectable, lo que
permite probar la lógica con un cliente simulado.

**Pantallas consolidadas** (`AppShell`, con `NavigationBar` e `IndexedStack`):

| Pantalla | Propósito | ViewModel |
| --- | --- | --- |
| Analizar | Elegir MRI, clasificar y ver resultado + Grad-CAM | `PredictionViewModel` |
| Historial | Listar las últimas predicciones | `HistoryViewModel` |
| Info | Contenido educativo de las 4 clases | — (estático) |
| Cuenta | Login/registro opcional | `AuthViewModel` |

El flujo de una acción es uniforme:

```
View --intención--> ViewModel --petición--> Repository --► Service --► API
  ^                                                                    |
  └──────────── notifyListeners() <── estado <────────────────────────┘
```

### 8.5 Calidad y pruebas

- **Backend:** 37 pruebas automatizadas (`pytest`) que cubren el contrato de
  `predict`, el historial, la validación de archivos, la salud, la
  autenticación (JWT) y la inferencia real con un checkpoint de prueba.
- **Frontend:** 23 pruebas (`flutter test`) sobre el parseo de DTOs, el
  contrato de `ApiService`, la persistencia de sesión y la lógica de los
  ViewModels; `flutter analyze` sin observaciones.
- **ML:** `smoke_test.py` (7/7) valida el entorno, las etiquetas, la partición,
  el *dataloader* y las capas de Grad-CAM sin necesidad de GPU.

## 9. Resultados

### 9.1 Estado del nivel de madurez

| Componente | Estado | Evidencia |
| --- | --- | --- |
| Pipeline de datos y entrenamiento | **Completo** | `ml/`, `smoke_test.py` 7/7 |
| Pesos de los modelos | **Recibidos** (no versionados por tamaño) | `ml/models/<modelo>/best.pt`, `metadata.json` |
| Inferencia (IA) | **Implementada** (mock por defecto sin pesos) | `backend/app/services/inference.py` + pruebas con checkpoint |
| API REST + persistencia | **Completo** | `backend/`, 37 pruebas |
| Aplicación móvil (MVVM) | **Completo** | `frontend/`, 23 pruebas |
| Autenticación | **JWT real + sesión persistente** | `backend/app/core/security.py`, `session_store.dart` |
| Interpretabilidad Grad-CAM | **Implementada** en `ml/` y en el backend | `ml/evaluation/gradcam.py`, `backend/app/services/gradcam.py` |
| Documentación (Scrum, paper) | **En avance** | `docs/scrum/`, `docs/paper_laccei/` |

### 9.2 Evidencia funcional (verificación de extremo a extremo)

Con el servidor corriendo con inferencia real se comprobó:

```
GET  /api/v1/health          → {"status":"ok", "model_ready":true, "classes":[...]}
POST /api/v1/auth/register   → {"access_token":"<jwt>", "name":"Equipo", ...}
POST /api/v1/auth/login      → {"access_token":"<jwt>", ...}
GET  /api/v1/auth/me         → {"id":1, "name":"Equipo", "email":"..."}
POST /api/v1/predict         → {"label":"glioma", "confidence":0.66, "gradcam_path":"/static/gradcam/..."}
GET  /api/v1/history         → [ {id, label, confidence, model_version, ...} ]
```

### 9.3 Resultados comparativos

Salida de `ml/evaluation/reports/comparison.json` (evaluación de test sobre
1.600 imágenes; figuras y métricas por clase en `ml/evaluation/reports/`):

| Modelo | Params (M) | Tamaño (MB) | Exactitud | Macro F1 | Recall tumor | ROC-AUC OVR | ms/imagen | Apto móvil |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DenseNet121 | 7.98 | 27.12 | **87.56 %** | **87.41 %** | **84.00 %** | 0.9677 | — | Media |
| MobileNetV3 | 5.48 | 16.25 | 87.19 % | 86.97 % | 83.08 % | 0.9710 | — | **Alta** |
| EfficientNetB0 | 5.29 | 15.59 | 87.06 % | 86.73 % | 82.75 % | **0.9711** | — | Alta |
| ResNet18 (ref.) | 11.69 | 42.72 | 85.69 % | 85.37 % | 81.42 % | 0.9644 | — | Baja |
| ShuffleNetV2 | 2.28 | 4.96 | 82.56 % | 82.15 % | 77.08 % | 0.9539 | — | **Alta** |

Modelo recomendado para el despliegue móvil: **MobileNetV3** (mejor equilibrio
exactitud/tamaño). Glioma es la clase más difícil para todos los modelos. Los
`ms/imagen` requieren el hardware de destino y quedan como validación pendiente.

> **Nota de trazabilidad:** estas métricas corresponden a la corrida de los
> notebooks de entrenamiento (la documentada en el ANEXO comparativo). Los
> checkpoints `ml/models/*/best.pt` pueden ser de una corrida posterior con
> mayor exactitud de validación; re-evaluarlos con
> `python ml/training/run_all.py --skip-train` y volver a correr
> `ml/evaluation/fill_table.py` es un paso opcional.

## 10. Discusión

El proyecto demuestra que es posible desacoplar el ciclo de vida del modelo del
ciclo de vida del software: gracias al modo simulado, la API y la aplicación
móvil alcanzaron un estado funcional verificable **sin** depender de que el
entrenamiento hubiera terminado. Este es un resultado de ingeniería
significativo, porque reduce el riesgo de que la incertidumbre del modelo
bloquee la entrega del producto.

Se identificaron, además, decisiones de corrección relevantes que se
documentaron para no incurrir en fallos silenciosos: la capa objetivo de
Grad-CAM cambia por arquitectura, el *backbone* se mantiene congelado y en modo
de evaluación durante el entrenamiento (las capas *BatchNorm* congeladas no
deben actualizar sus estadísticas), y se adoptó torchvision de forma uniforme
para disponer de las cinco arquitecturas con pesos ImageNet equivalentes.
Todas estas desviaciones respecto del manuscrito base están registradas en
`docs/notas-correccion-paper.md`.

En cuanto a la ingeniería de software, la detección de una violación de MVVM en
la pantalla de historial (la vista hacía la petición HTTP directamente) derivó
en la creación de un `HistoryViewModel` y un repositorio, con pruebas
asociadas. Esto ilustra el valor de la *Definition of Done* como control de
calidad transversal.

## 11. Conclusiones

1. Se construyó un **sistema completo de extremo a extremo** —datos, modelos,
   API y aplicación móvil— con una arquitectura limpia y verificable.
2. La aplicación móvil aplica correctamente el patrón **MVVM**: la lógica de
   estado vive en los ViewModels, el acceso a red en los servicios, y las
   vistas solo presentan y capturan intenciones.
3. El backend expone un **contrato REST estable** y consume la inferencia de
   forma intercambiable (mock o real) sin afectar al cliente.
4. Se respeta la privacidad de los pacientes al persistir solo el *hash* de la
   imagen.
5. La metodología **Scrum** permitió avanzar en paralelo capas con distinta
   madurez y mantener el repositorio en verde sprint a sprint.
6. La comparación de arquitecturas y su interpretabilidad con **Grad-CAM**
   quedarán completas al integrar los pesos; el código de inferencia y de
   Grad-CAM ya está implementado y probado, y solo espera los checkpoints.

## 12. Recomendaciones y trabajo futuro

- Los checkpoints `best.pt` ya se integraron (carga real y Grad-CAM en
  `backend/app/services/`); re-evaluarlos sobre el conjunto de prueba para
  alinear las métricas del paper con los pesos desplegados es un control
  opcional de reproducibilidad.
- Generar y publicar los mapas Grad-CAM con el modelo desplegado y completar la
  tabla comparativa con `ml/evaluation/fill_table.py`.
- Completar la conversión a **TFLite** para llevar el modelo al dispositivo
  (`ml/export_tflite.py`).
- Ampliar las pruebas de integración extremo a extremo y la cobertura de las
  pantallas con `flutter_test`.

## 13. Referencias

*(Completar en formato IEEE/LACCEI. Lista base:)*

1. Saeedi, S., et al. *A novel deep learning-based approach for classification
   of brain tumors*, SpringerPlus, 2023.
2. Nickparvar, M. *Brain Tumor MRI Dataset*, Kaggle, 2024.
3. Selvaraju, R. R., et al. *Grad-CAM: Visual Explanations from Deep Networks
   via Gradient-based Localization*, ICCV, 2017.
4. Howard, A., et al. *Searching for MobileNetV3*, ICCV, 2019.
5. Tan, M., Le, Q. *EfficientNet: Rethinking Model Scaling for CNNs*, ICML,
   2019.
6. Ma, N., et al. *ShuffleNet V2: Practical Guidelines for Efficient CNN
   Architecture Design*, ECCV, 2018.
7. Huang, G., et al. *Densely Connected Convolutional Networks*, CVPR, 2017.
8. He, K., et al. *Deep Residual Learning for Image Recognition*, CVPR, 2016.

## 14. Anexos

### Anexo A — Estructura del repositorio

```
brain-tumor-classification/
├── ml/            # dataset, entrenamiento, evaluación: PyTorch + torchvision
├── backend/       # API FastAPI + SQLite + inferencia + Grad-CAM
├── frontend/      # App Flutter con arquitectura MVVM
└── docs/          # scrum, paper, notas, flujograma, tabla comparativa
```

### Anexo B — Comandos principales

```bash
# ML
python ml/smoke_test.py                                   # validación sin GPU
python ml/training/run_all.py --preset ml/configs/experiments/initial.yaml --device cuda
python ml/evaluation/metrics.py --model mobilenetv3 --weights ml/models/mobilenetv3/best.pt

# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

### Anexo C — Documentos del proyecto

| Documento | Contenido |
| --- | --- |
| `docs/scrum/` | Roles, backlog, sprints y Definition of Done |
| `docs/diseno-pantallas.md` | Pantallas consolidadas y su correspondencia MVVM |
| `docs/paper_laccei/avance-paper.md` | Avance del artículo científico |
| `docs/ml-training-handoff.md` | Guía de entrenamiento de los cinco modelos |
| `docs/notas-correccion-paper.md` | Desviaciones respecto al manuscrito |
| `docs/tabla-comparativa.md` | Formato de la tabla de resultados (OE2) |
| `docs/flujograma.md` | Fases y correspondencia con los objetivos |
