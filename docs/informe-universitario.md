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

El estado actual corresponde a la **semana 7**. El pipeline de entrenamiento,
la API, la aplicación móvil y su documentación están implementados y
verificados; la integración de los pesos reales del modelo permanece en modo
simulado (*mock*) hasta que el equipo de entrenamiento entregue los
checkpoints, de modo que ninguna otra capa del sistema quedara bloqueada.

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
| **OE4** | Validar el rendimiento mediante validación cruzada y compararlo con el estado del arte. |

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
de entrenar desde cero con 3.264 imágenes —insuficientes para converger—, se
congela el *backbone* y se entrena una cabeza nueva, tras lo cual se hace
*fine-tuning*. Esto da una ventaja de convergencia y una comparación más justa
entre arquitecturas.

### 6.3 Arquitecturas ligeras

| Modelo | Idea central | Relevancia para móvil |
| --- | --- | --- |
| **MobileNetV3** | Convoluciones separables en profundidad + *squeeze-and-excitation* | Muy bajo costo |
| **EfficientNetB0** | Escalado compuesto equilibrado de profundidad, ancho y resolución | Buen accuracy/parámetro |
| **ShuffleNetV2** | *Channel shuffle* y convoluciones agrupadas | Muy eficiente en cómputo |
| **DenseNet121** | Conexiones densas entre capas | Reutilización de features |
| **ResNet18** | Conexiones residuales (*skip connections*) | Referencia estándar |

> Se eligió **timm** como biblioteca principal porque provee uniformemente los
> modelos con pesos ImageNet. ShuffleNetV2, ausente en timm 1.x, se construye
> con **torchvision** manteniendo pesos ImageNet equivalentes.

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
bloquear el desarrollo del cliente, el backend opera con
**`MOCK_INFERENCE=true`**: devuelve una predicción ficticia pero determinista a
partir del contenido de la imagen. De este modo, ML, backend y frontend avanzan
en paralelo y la integración real se limita a implementar la carga de pesos.

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
           │                                      │  PyTorch + timm         │
           └─────────────────────────────────────►└─────────────────────────┘
                                                    SQLite (historial)
```

### 8.2 Capa de machine learning (`ml/`)

- **Dataset:** conjunto público de 3.264 imágenes de 4 clases (Saeedi et al.),
  con alternativa de 7.023 imágenes (Nickparvar) cuyas subcategorías de glioma
  se colapsan a `glioma`.
- **Partición única:** 70 % entrenamiento / 15 % validación / 15 % prueba,
  estratificada, `seed=42`, con manifiesto en `ml/dataset/processed/splits.json`.
- **Preprocesamiento:** redimensionado a 256×256, conversión a RGB y
  normalización **por modelo** (rango [-1,1] o estadísticas de ImageNet según
  el caso). Tensor de entrada `3×256×256`.
- **Aumento de datos:** `torchvision.transforms` (rotación, zoom, *flip*).
- **Entrenamiento:** *transfer learning* con *backbone* congelado hasta la
  época 15 y *fine-tuning* posterior; optimizador **AdamW** (`lr=1e-4`,
  `wd=1e-4`), scheduler coseno, *early stopping* con paciencia 7, 30 épocas,
  semilla 42.
- **Validación:** validación cruzada estratificada de 5 folds.
- **Evaluación:** exactitud, macro precisión/recall/F1, F1 ponderado, *recall*
  tumoral, especificidad de `no_tumor`, matriz de confusión, ms/imagen,
  parámetros y tamaño del checkpoint.
- **Interpretabilidad:** Grad-CAM con capa objetivo por arquitectura
  (`conv_head`, `conv5`, `layer4[-1]`, `features.denseblock4`).

### 8.3 Capa de backend (`backend/`)

API REST en **FastAPI** con persistencia **SQLite** vía SQLAlchemy.

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/api/v1/predict` | Clasifica una imagen MRI |
| `GET` | `/api/v1/history` | Últimas predicciones |
| `GET` | `/api/v1/health` | Estado del servicio y del modelo |
| `POST` | `/api/v1/auth/register` | Registro de cuenta (modo mock) |
| `POST` | `/api/v1/auth/login` | Inicio de sesión (modo mock) |

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
│   └── services/    # ApiService y AuthService (único punto HTTP)
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

- **Backend:** 21 pruebas automatizadas (`pytest`) que cubren el contrato de
  `predict`, el historial, la validación de archivos, la salud y la
  autenticación.
- **Frontend:** 17 pruebas (`flutter test`) sobre el parseo de DTOs, el
  contrato de `ApiService` y la lógica de los ViewModels; `flutter analyze` sin
  observaciones.
- **ML:** `smoke_test.py` (7/7) valida el entorno, las etiquetas, la partición,
  el *dataloader* y las capas de Grad-CAM sin necesidad de GPU.

## 9. Resultados

### 9.1 Estado del nivel de madurez

| Componente | Estado | Evidencia |
| --- | --- | --- |
| Pipeline de datos y entrenamiento | **Completo** | `ml/`, `smoke_test.py` 7/7 |
| Pesos de los modelos | **Pendiente** | a cargo del equipo de entrenamiento |
| Inferencia (IA) | **Simulada (mock)** | `MOCK_INFERENCE=true` |
| API REST + persistencia | **Completo** | `backend/`, 21 pruebas |
| Aplicación móvil (MVVM) | **Completo** | `frontend/`, 17 pruebas |
| Interpretabilidad Grad-CAM | **Implementada**, pendiente de pesos | `ml/evaluation/gradcam.py` |
| Documentación (Scrum, paper) | **En avance** | `docs/scrum/`, `docs/paper_laccei/` |

### 9.2 Evidencia funcional (verificación de extremo a extremo)

Con el servidor corriendo en modo mock se comprobó:

```
GET  /api/v1/health          → {"status":"ok_mock", ..., "classes":[...]}
POST /api/v1/auth/register   → {"access_token":"mock-...", "name":"Equipo", ...}
POST /api/v1/auth/login      → {"access_token":"mock-...", ...}
POST /api/v1/predict         → {"label":"pituitario", "confidence":0.407, ...}
GET  /api/v1/history         → [ {id, label, confidence, model_version, ...} ]
```

### 9.3 Resultados comparativos (pendiente)

La tabla siguiente se completará con la salida de
`ml/evaluation/reports/comparison.json` una vez que existan los pesos:

| Modelo | Params (M) | Tamaño (MB) | Exactitud | Macro F1 | Recall tumor | ms/imagen | Apto móvil |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MobileNetV3 | — | — | — | — | — | — | — |
| EfficientNetB0 | — | — | — | — | — | — | — |
| ShuffleNetV2 | — | — | — | — | — | — | — |
| DenseNet121 | — | — | — | — | — | — | — |
| **ResNet18 (ref.)** | — | — | — | — | — | — | — |

## 10. Discusión

El proyecto demuestra que es posible desacoplar el ciclo de vida del modelo del
ciclo de vida del software: gracias al modo simulado, la API y la aplicación
móvil alcanzaron un estado funcional verificable **sin** depender de que el
entrenamiento hubiera terminado. Este es un resultado de ingeniería
significativo, porque reduce el riesgo de que la incertidumbre del modelo
bloquee la entrega del producto.

Se identificaron, además, decisiones de corrección relevantes que se
documentaron para no incurrir en fallos silenciosos: la normalización depende
del modelo (usar una sola rompe la convergencia de ResNet18), la capa objetivo
de Grad-CAM cambia por arquitectura, y ShuffleNetV2 no existe en timm 1.x, por
lo que se construye con torchvision. Todas estas desviaciones respecto del
manuscrito base están registradas en `docs/notas-correccion-paper.md`.

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
   quedará completa cuando se integren los pesos; hoy el único punto simulado
   del sistema es precisamente la inferencia.

## 12. Recomendaciones y trabajo futuro

- Integrar los checkpoints `best.pt` implementando `load()` y `_predict_real()`
  en `backend/app/services/inference.py`, sin cambiar el contrato HTTP.
- Generar y publicar los mapas Grad-CAM y completar la tabla comparativa.
- Persistir el token de sesión con `SharedPreferences` y sustituir el módulo de
  autenticación mock por uno real (JWT).
- Explorar la conversión a **TFLite** para llevar el modelo al dispositivo.
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
├── ml/            # dataset, entrenamiento, evaluación: PyTorch + timm
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
