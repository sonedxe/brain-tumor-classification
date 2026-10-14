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

Otros endpoints: `GET /api/v1/health` (verifica que el modelo esté cargado) y
`GET /api/v1/history` (historial de predicciones). La cuenta es opcional y usa
**JWT real**: `POST /api/v1/auth/register`, `POST /api/v1/auth/login` (devuelven
`{ access_token, token_type, name, email, expires_in }`) y `GET /api/v1/auth/me`
(valida el token). El `AuthViewModel` persiste la sesión con `SharedPreferences`.
Documentación interactiva en `/docs` cuando el servidor está corriendo.

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

Con `MOCK_INFERENCE=true` (por defecto) `/predict` responde sin necesidad de
pesos entrenados, lo que permite desarrollar el frontend de inmediato.

Para **inferencia real** instala `backend/requirements-inference.txt` (torch +
torchvision, desde el índice oficial de PyTorch según la variante CPU/CUDA),
coloca el `best.pt` en la ruta de `MODEL_PATH` y pon `MOCK_INFERENCE=false`. En
producción define además un `JWT_SECRET` propio.

### 3. Frontend

```bash
cd frontend
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

`10.0.2.2` es el alias del host desde el emulador de Android. En iOS Simulator
usar `http://localhost:8000/api/v1`; en dispositivo físico, la IP local de la
máquina.

## Documentación

- `docs/informe-universitario.md` — informe universitario completo del proyecto.
- `docs/scrum/` — aplicación de Scrum: roles, ceremonias, product backlog,
  historial de sprints y Definition of Done.
- `docs/diseno-pantallas.md` — las cuatro pantallas consolidadas y su
  correspondencia con MVVM.
- `docs/paper_laccei/avance-paper.md` — avance del artículo científico (LACCEI).
- `docs/ml-training-handoff.md` — guía para entrenar los cinco modelos.
- `docs/notas-correccion-paper.md` — desviaciones entre el repositorio y el
  manuscripto, y qué línea del paper corresponde a cada una.
- `docs/tabla-comparativa.md` — formato de la tabla de resultados del OE2.
- `docs/flujograma.md` — fases del proyecto y su correspondencia con los
  objetivos específicos.

## Estado actual (nivel de madurez)

- **Frontend (MVVM):** capas `models`, `repositories`, `services`, `viewmodels`
  y `views`; cuatro pantallas consolidadas y consumo de `predict`, `history` y
  `auth` desde Flutter. El único punto que conoce la URL es `ApiService`, y la
  sesión se persiste con `SessionStore` (`SharedPreferences`).
- **Backend:** contrato estable (`predict`, `history`, `health`, `auth`) con
  `MOCK_INFERENCE=true` por defecto. La inferencia real (carga de `best.pt` y
  Grad-CAM) y la autenticación JWT ya están implementadas: al dejar los pesos en
  `MODEL_PATH`, el backend pasa a inferencia real sin cambiar el contrato HTTP.
- **ML:** el pipeline comparativo está listo y los cinco modelos están
  entrenados y evaluados (`ml/evaluation/reports/`). Los `best.pt` ya se
  integraron localmente (excluidos de Git por tamaño) y el backend ejecuta la
  inferencia real y el Grad-CAM sin cambiar el contrato HTTP.
