# Clasificación de Tumores Cerebrales en Imágenes de Resonancia Magnética

Aplicativo móvil con Deep Learning para la clasificación multiclase de tumores
cerebrales en imágenes de resonancia magnética (MRI).

Comparación de cuatro arquitecturas CNN ligeras (**MobileNetV3**, **EfficientNetB0**,
**ShuffleNetV2**, **DenseNet121**) contra **ResNet18** como modelo de referencia,
con evaluación de interpretabilidad mediante **Grad-CAM**.

> Aviso: esta herramienta es de apoyo académico y **no constitute un dispositivo
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
`GET /api/v1/history` (historial de predicciones). Documentación interactiva
en `/docs` cuando el servidor está corriendo.

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

- `docs/notas-correccion-paper.md` — desviaciones entre el repositorio y el
  manuscripto, y qué línea del paper corresponde a cada una.
- `docs/tabla-comparativa.md` — formato de la tabla de resultados del OE2.
- `docs/flujograma.md` — fases del proyecto y su correspondencia con los
  objetivos específicos.
