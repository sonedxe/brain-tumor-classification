# Clasificación de Tumores Cerebrales en Imágenes de Resonancia Magnética

Aplicativo móvil con Deep Learning para la clasificación multiclase de tumores
cerebrales en imágenes de resonancia magnética (MRI).

Comparación de cuatro arquitecturas CNN ligeras (**MobileNetV3**, **EfficientNetB0**,
**ShuffleNetV2**, **DenseNet121**) contra **ResNet18** como modelo de referencia,
con evaluación de interpretabilidad mediante **Grad-CAM**.

> Aviso: esta herramienta es de apoyo académico y **no constituye un dispositivo
> médico ni sustituye el criterio de un radiólogo**.

## Arquitectura

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
           │  nunca se envía datos                           ▼
           │  del paciente                        ┌─────────────────────────┐
           │                                     │  ml/                    │
           │                                     │  PyTorch + torchvision │
           │                                     │  dataset / training /   │
           │                                     │  evaluation / models    │
           └─────────────────────────────────────►└─────────────────────────┘
                                                   SQLite (historial)
```

El backend guarda únicamente el hash SHA-256 de la imagen. No se almacenan
nombres de pacientes, metadatos DICOM ni ningún dato que permita reidentificar
a un sujeto.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `ml/` | Dataset, entrenamiento (PyTorch + torchvision), evaluación, Grad-CAM y pesos |
| `backend/` | API FastAPI, inferencia, persistencia SQLite |
| `frontend/` | App Flutter con arquitectura MVVM |
| `docs/` | Paper, tesis, notas de corrección y tabla comparativa |
| `docs/scrum/` | Metodología Scrum: backlog, sprints y Definition of Done |
| `docs/paper_laccei/` | Avance del artículo científico (formato LACCEI) |

## Clases

Definidas en un único archivo, `ml/configs/labels.json`, que es la fuente de
verdad compartida entre el entrenamiento y el backend para evitar que se
desincronicen:

`glioma` · `meningioma` · `pituitario` · `no_tumor`

## Contrato de la API

```http
POST /api/v1/predict
Content-Type: multipart/form-data
field: file
```

```json
{
  "label": "meningioma",
  "confidence": 0.97,
  "probabilities": {
    "glioma": 0.01,
    "meningioma": 0.97,
    "pituitario": 0.01,
    "no_tumor": 0.01
  },
  "gradcam_path": "/static/gradcam/9f2a.png",
  "model_version": "mobilenetv3-v1",
  "inference_ms": 82.4
}
```

Otros endpoints: `GET /api/v1/health` (verifica que el modelo esté cargado),
`GET /api/v1/history` (historial de predicciones),
`GET /api/v1/predictions/{id}` (detalle con las cuatro probabilidades),
`POST /api/v1/predictions/{id}/feedback` (revisión humana del resultado),
`GET /api/v1/models` (los cinco modelos registrados, con sus métricas),
`GET /api/v1/classes` (catálogo de clases) y
`GET /api/v1/stats/summary` (conteo por clase y latencia media).

La cuenta es opcional y usa **JWT real con sesiones revocables**:
`POST /api/v1/auth/register`, `POST /api/v1/auth/login` (devuelven
`{ access_token, token_type, name, email, expires_in, refresh_token }`),
`POST /api/v1/auth/refresh` (rota el refresh token), `POST /api/v1/auth/logout`
y `GET /api/v1/auth/me` (valida el token). El `AuthViewModel` persiste la sesión
con `SharedPreferences`. Documentación interactiva en `/docs` cuando el servidor
está corriendo.

## Modelo de datos

Ocho tablas normalizadas (SQLAlchemy sobre SQLite). Los catálogos se siembran al
arrancar: las clases desde `ml/configs/labels.json` y los modelos desde las
métricas de `ml/evaluation/reports/comparison.json`.

| Tabla | Propósito |
| --- | --- |
| `users` | cuentas (rol, borrado lógico) |
| `ml_models` | registro de los cinco modelos (arquitectura, versión, accuracy) |
| `lesion_classes` | catálogo de las clases (`glioma`, `meningioma`, `pituitario`, `no_tumor`) |
| `images` | imagen por SHA-256 (deduplicación), solo metadatos técnicos |
| `predictions` | predicción: imagen + modelo + clase + confianza + Grad-CAM |
| `prediction_scores` | las cuatro probabilidades de cada predicción |
| `prediction_feedback` | revisión humana del resultado (human-in-the-loop) |
| `auth_sessions` | sesiones con refresh token (hash, expiración, revocación) |

El diagrama está en `docs/paper_laccei/figuras/figura-01-modelo-datos.png` y su
fuente versionable en `docs/paper_laccei/figuras/modelo-datos.mmd`.

## Puesta en marcha

### 1. Modelo (Python 3.12)

En Windows, desde la raíz del repositorio, sigue la guía de instalación ML en
[`docs/ml-training-handoff.md`](docs/ml-training-handoff.md). Crea el entorno
`.venv` en la raíz y usa siempre su `python.exe` para instalar dependencias y
ejecutar los scripts. La guía incluye comandos PowerShell para CUDA 13.0 y CPU.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

### 2. Backend

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload
```

La inferencia es **real**: instala `torch` + `torchvision` (vienen en
`backend/requirements.txt`; usa la variante CPU/CUDA del índice oficial de
PyTorch) y coloca el `best.pt` del modelo elegido en la ruta de `MODEL_PATH`.
En producción define además un `JWT_SECRET` propio.

### 3. Frontend

```bash
cd frontend
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

`10.0.2.2` es el alias del host desde el emulador de Android. En iOS Simulator
usar `http://localhost:8000/api/v1`; en dispositivo físico, la IP local de la
máquina. En **Chrome/Web**:

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000/api/v1
```

El CORS del backend ya permite `http://localhost:*` para el desarrollo web.

## Modo offline

La app funciona sin conexión con **el mismo modelo del backend**. El `best.pt`
activo se exporta a ONNX y se empaqueta como asset:

```bash
# Requiere onnx + onnxscript en el venv del backend
backend/.venv/bin/python ml/export_mobile_onnx.py --model mobilenetv3 --verify
# -> frontend/assets/models/model.onnx (unico archivo, ~16 MB)
```

Comportamiento sin red:

- **Predicción:** inferencia local (ONNX Runtime) con el mismo preprocesamiento
  (224x224, normalización ImageNet) y las mismas 4 clases de
  `ml/configs/labels.json`. El Grad-CAM no se genera offline.
- **Historial:** muestra la caché de `GET /history` más las predicciones
  pendientes, marcadas como «Pendiente de sincronizar».
- **Registro y login:** se resuelven contra el almacén local (contraseña
  cifrada en base64 solo para poder replicar el alta; es una demo académica).
- **Sincronización:** al recuperar la conexión se registran las cuentas
  pendientes, se envían los feedbacks en cola y se reenvían las imágenes
  pendientes a `POST /predict`; el backend vuelve a inferir y guarda el
  registro definitivo.

Prueba manual: activa el modo avión, clasifica una imagen (usa el banner «Sin
conexión · modelo local ONNX»), revisa el historial y desactiva el modo avión
para ver la sincronización.

## Generar el APK

```bash
cd frontend
# Universal (un solo archivo para cualquier dispositivo)
flutter build apk --release

# Variantes por ABI (instalación más liviana)
flutter build apk --release --split-per-abi
```

Salida en `frontend/build/app/outputs/flutter-apk/`:
`app-release.apk` (universal) y `app-arm64-v8a-release.apk` (recomendado para
dispositivos modernos). Para apuntar a un backend desplegado:

```bash
flutter build apk --release \
  --dart-define=API_BASE_URL=https://<tu-backend>.onrender.com/api/v1
```

## Documentación

- `docs/informe-universitario.md` — informe universitario completo del proyecto.
- `docs/scrum/` — aplicación de Scrum: roles, ceremonias, product backlog,
  historial de sprints y Definition of Done.
- `docs/diseno-pantallas.md` — las pantallas consolidadas (Analizar, Historial,
  Panel, Info, Cuenta y el detalle) y su correspondencia con MVVM.
- `docs/paper_laccei/avance-paper.md` — avance del artículo científico (LACCEI).
- `docs/ml-training-handoff.md` — guía para entrenar los cinco modelos.
- `docs/notas-correccion-paper.md` — desviaciones entre el repositorio y el
  manuscripto, y qué línea del paper corresponde a cada una.
- `docs/tabla-comparativa.md` — formato de la tabla de resultados del OE2.
- `docs/flujograma.md` — fases del proyecto y su correspondencia con los
  objetivos específicos.
- `docs/paper_laccei/figuras/` — figuras del artículo (modelo de datos,
  endpoints y pantallas móviles) con su procedencia y cómo regenerarlas.

## Estado actual (nivel de madurez)

- **Frontend (MVVM):** capas `models`, `repositories`, `services`, `viewmodels`
  y `views`; cuatro pantallas consolidadas y consumo de `predict`, `history` y
  `auth` desde Flutter. El único punto que conoce la URL es `ApiService`, y la
  sesión se persiste con `SessionStore` (`SharedPreferences`).
- **Backend:** contrato estable (`predict`, `history`, `health`, `models`,
  `classes`, `stats`, `auth`) con inferencia real (carga de `best.pt` +
  Grad-CAM), autenticación JWT con sesiones revocables y un modelo de datos de
  ocho tablas (ver «Modelo de datos»). Los pesos se colocan en `MODEL_PATH`; sin
  ellos el arranque falla con un mensaje claro.
- **ML:** el pipeline comparativo está listo y los cinco modelos están
  entrenados y evaluados (`ml/evaluation/reports/`). Los `best.pt` ya se
  integraron localmente (excluidos de Git por tamaño) y el backend ejecuta la
  inferencia real y el Grad-CAM sin cambiar el contrato HTTP.
