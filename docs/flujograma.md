# Flujograma del proyecto

Cinco fases y su correspondencia con los objetivos especificos. Sirve para
explicar la planificacion en sustentacion.

## Fase 1 - Revision bibliografica y definicion del alcance

Comparacion de los trabajos [11] a [24] del manuscripto, verificacion de que
datasets y arquitecturasestan disponibles, y fijacion de las cuatro clases de
salida: `glioma`, `meningioma`, `pituitario`, `no_tumor`.

**Entregable:** `docs/literatura/`
**Objetivo:** OE1

## Fase 2 - Preprocesamiento y exploracion de datos

Preparacion del dataset conservando `Training/` y `Testing/`, redimensionado a
224x224, conversion a RGB y normalizacion ImageNet compartida.

**Entregable:** `ml/dataset/`, `ml/evaluation/reports/`
**Objetivo:** OE1

## Fase 3 - Entrenamiento de los cinco modelos

Transfer learning con pesos ImageNet y backbone congelado. Solo se entrena la
cabeza clasificadora con Adam y CrossEntropyLoss. La epoca se selecciona por
accuracy de validacion; `Testing/` permanece reservado para evaluacion.

**Entregable:** `ml/training/`, pesos en `ml/models/`
**Objetivo:** OE1, OE4

## Fase 4 - Evaluacion, seleccion e interpretabilidad

Metricas de clasificacion, matrices de confusion, tiempos de inferencia y
mapas de calor Grad-CAM. Seleccion del modelo winner.

**Entregable:** `ml/evaluation/`, `docs/tabla-comparativa.md`
**Objetivo:** OE2, OE4

## Fase 5 - Integracion movil

Exposicion del modelo como servicio REST en FastAPI, persistencia del historial
en SQLite, y consumo desde la app Flutter con arquitectura MVVM. Validacion
extrema a extremo del flujo de subida de imagen.

**Entregable:** `backend/`, `frontend/`
**Objetivo:** OE3

## Objetivos especificos

| OE | Formulacion | Fase |
| --- | --- | --- |
| OE1 | Identificar y evaluar arquitecturas CNN ligeras para clasificacion multiclase de tumores cerebrales en MRI | 1, 2, 3 |
| OE2 | Seleccionar el modelo mas adecuado segun exactitud, tiempo de inferencia e interpretabilidad con Grad-CAM | 4 |
| OE3 | Integrar el modelo seleccionado en un aplicativo movil mediante comunicacion cliente-servidor | 5 |
| OE4 | Validar el rendimiento en conjuntos independientes y comparar con el estado del arte | 3, 4 |

## Dependencias entre fases

La fase 5 depende de la 4: la API no puede cargar pesos hasta que haya un
modelo elegido y exportado. La fase 4 depende de la 3. La fase 3 depende de
que la fase 2 confirme que el dataset es utilizable.

Esta dependencia es la razon de que el backend se desarrolle con `MOCK_INFERENCE`:
permite construir y probar toda la capa de comunicacion e interfaz en paralelo
con el entrenamiento, sin esperar a que termine.
