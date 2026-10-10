# Sprint Backlog e historial de sprints

Un sprint por semana. La sesion remota del sabado es el Sprint Review. La
velocidad se expresa en puntos de historia (media movil de los ultimos 3
sprints).

## Resumen

| Sprint | Objetivo | Pts plan | Pts hecho | Estado |
| --- | --- | --- | --- | --- |
| S0 | Repositorio, entorno y convenciones | 3 | 3 | Cerrado |
| S1 | Dataset y clases canonicas | 7 | 7 | Cerrado |
| S2 | Protocolo de entrenamiento comparativo | 8 | 8 | Cerrado |
| S3 | Metricas y evaluacion | 5 | 5 | Cerrado |
| S4 | API FastAPI + modo mock | 11 | 11 | Cerrado |
| S5 | App Flutter: captura y resultado (MVVM) | 10 | 10 | Cerrado |
| S6 | Navegacion, historial e info (pantallas) | 8 | 8 | Cerrado |
| S7 | Cuenta opcional, MVVM del historial, documentos | 11 | 11 | Cerrado |
| S8 | Paper, Scrum y sustentacion (examen parcial) | 13 | - | En curso |

Velocidad (media S4-S6): ~9.7 pts/sprint. S8 se compromete de forma prudente
porque coincide con el examen parcial.

## S0 - Puesta en marcha

- **Incremento:** estructura de carpetas `backend/`, `frontend/`, `ml/`, `docs/`;
  `.gitignore`; README raiz; convenciones de idioma (codigo sin acentos).
- **Definition of Done:** revision del repositorio inicial aceptada.

## S1 - Datos

- **Items:** US-01, US-02.
- **Incremento:** `ml/dataset/download.py`, `prepare.py`, `preprocessing.py`,
  `augmentation.py`; `labels.json` como fuente unica de clases.
- **Nota:** la descarga de Kaggle requiere cuenta; el split es 70/15/15,
  seed=42, estratificado.

## S2 - Entrenamiento

- **Items:** US-03.
- **Incremento:** `ml/training/{train,run_all,kfold,dataloader}.py`, cinco YAML
  en `ml/configs/`, `smoke_test.py` (7/7).
- **Impedimento resuelto:** ShuffleNetV2 no existe en timm 1.x -> se construye
  con torchvision con pesos ImageNet (ver `docs/notas-correccion-paper.md` §5).
- **Riesgo abierto:** GPU destino (RTX 5070) exige `torch>=2.7`. Se documenta
  el handoff en `docs/ml-training-handoff.md`.

## S3 - Evaluacion

- **Items:** US-04, US-05.
- **Incremento:** `ml/evaluation/metrics.py` (accuracy, macro F1, recall
  tumoral, matriz de confusion, ms/imagen, params) y `gradcam.py` con la capa
  objetivo resuelta por arquitectura.

## S4 - API

- **Items:** US-06, US-07, US-08, US-09.
- **Incremento:** API FastAPI con `POST /predict`, `GET /history`,
  `GET /health`, persistencia SQLite (solo hash) y `MOCK_INFERENCE`.
- **Decision:** la inferencia real depende S3/S2; el mock desbloquea S5.
- **Pruebas:** `backend/tests/` en verde.

## S5 - App (captura y resultado)

- **Items:** US-10, US-11, US-12.
- **Incremento:** capas MVVM completas (`models`, `repositories`, `services`,
  `viewmodels`, `views`); `PredictionViewModel`; `ImagePickerButton`;
  `ResultCard`; `ApiService` como unico punto que conoce la URL.
- **Pruebas:** `frontend/test/prediction_viewmodel_test.dart`.

## S6 - Pantallas consolidadas

- **Items:** US-13.
- **Incremento:** `AppShell` con `NavigationBar`; pantallas Analizar,
  Historial, Info, Cuenta; tema unico (`core/theme.dart`).
- **Deuda tecnica detectada:** el historial hacia la llamada HTTP dentro de la
  vista (violacion de MVVM). Se planifica para S7.

## S7 - Cuenta, MVVM del historial y documentos

- **Items:** US-14, US-15, US-16 (parcial).
- **Incremento:**
  - `HistoryViewModel` + `HistoryRepository` + `ApiService.fetchHistory`
    (elimina la deuda tecnica de S6; la vista ya no hace HTTP).
  - `AuthViewModel`/`AuthService` y endpoints mock `POST /auth/register`,
    `POST /auth/login` en el backend.
  - Documentos `docs/scrum/` y este backlog.
- **Impedimento:** el peso del modelo no esta disponible (lo entrega el
  companero de ML). Se mitiga con `MOCK_INFERENCE`.

## S8 - En curso (examen parcial)

- **Sprint Goal:** dejar el proyecto en nivel de madurez sustentable y avanzar
  el articulo cientifico.
- **Items comprometidos:**
  - US-17 (avance del paper en `docs/paper_laccei/`).
  - Consolidar `docs/scrum/` y `docs/diseno-pantallas.md`.
  - Verificar extremo a extremo el consumo de endpoints desde Flutter contra el
    backend en modo mock.
- **Criterio de aceptacion:** `pytest` (backend), `flutter test` y
  `flutter analyze` en verde; demo del flujo subir imagen -> resultado ->
  historial; paper con metodologia redactada.
- **Riesgo:** la sustentacion es sobre madurez, no sobre resultados finales; se
  comunica con transparencia que el modelo esta en modo mock.
