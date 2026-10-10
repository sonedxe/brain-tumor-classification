# Product Backlog

Historias de usuario del aplicativo, priorizadas por el Product Owner. La
prioridad sigue MoSCoW (Must / Should / Could / Won't-for-now) y la estimacion
usa puntos de historia (Fibonacci).

## Epics

| Epic | Descripcion | OE |
| --- | --- | --- |
| E1 | Preparar datos y protocolo de entrenamiento | OE1 |
| E2 | Entrenar y comparar las arquitecturas CNN | OE1, OE2, OE4 |
| E3 | Elegir el mejor modelo e interpretarlo con Grad-CAM | OE2, OE4 |
| E4 | Exponer el modelo como API y persistir el historial | OE3 |
| E5 | Consumir la API desde una app movil con MVVM | OE3 |
| E6 | Documentar el trabajo como articulo cientifico | Transversal |

## Historias de usuario

| ID | Como... | Quiero... | Para... | Epic | Prior. | Pts | Incremento |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US-01 | investigador | descargar y preparar el dataset con un split fijo | entrenar de forma reproducible | E1 | Must | 5 | `ml/dataset/prepare.py`, `splits.json` |
| US-02 | investigador | fijar las 4 clases en un solo archivo | que modelo y API no se desincronicen | E1 | Must | 2 | `ml/configs/labels.json` |
| US-03 | investigador | entrenar los 5 modelos con el mismo protocolo | compararlos de forma justa | E2 | Must | 8 | `ml/training/`, pesos |
| US-04 | investigador | medir metricas, confusion y tiempos | seleccionar el mejor modelo | E2 | Must | 5 | `ml/evaluation/metrics.py` |
| US-05 | investigador | generar Grad-CAM por modelo | sustentar la interpretabilidad | E3 | Should | 3 | `ml/evaluation/gradcam.py` |
| US-06 | usuario | subir una imagen MRI y recibir un diagnostico | apoyar la revision medica | E4 | Must | 8 | `POST /predict` |
| US-07 | usuario | que la API responda sin pesos entrenados | desarrollar la app en paralelo | E4 | Must | 3 | `MOCK_INFERENCE` |
| US-08 | usuario | consultar el historial de predicciones | auditar el uso de la app | E4 | Should | 3 | `GET /history` |
| US-09 | usuario | que no se guarden datos identificables | cuidar la privacidad | E4 | Must | 2 | hash SHA-256 |
| US-10 | usuario movil | seleccionar imagen de galeria o camara | analizarla desde el celular | E5 | Must | 5 | `ImagePickerButton` |
| US-11 | usuario movil | ver etiqueta, confianza y probabilidades | entender el resultado | E5 | Must | 5 | `ResultCard` |
| US-12 | usuario movil | una app con arquitectura MVVM | mantener y testear el codigo | E5 | Must | 8 | `lib/{models,repositories,services,viewmodels,views}` |
| US-13 | usuario movil | navegar entre pantallas consolidadas | usar la app sin friccion | E5 | Must | 5 | `AppShell`, 4 pantallas |
| US-14 | usuario movil | ver el historial dentro de la app | revisar predicciones previas | E5 | Should | 3 | `HistoryViewModel` |
| US-15 | usuario | una cuenta opcional | separar historiales y capturar evidencia | E5 | Could | 3 | `auth/register`, `auth/login` (mock) |
| US-16 | equipo | documentar la metodologia y el avance | cumplir la rubrica | E6 | Must | 5 | `docs/scrum/` |
| US-17 | equipo | redactar el articulo cientifico | entregar el paper | E6 | Must | 8 | `docs/paper_laccei/` |

## Priorizacion del proximo sprint (semana 8)

El examen parcial es la sustentacion del **nivel de madurez**. El PO prioriza
que todo lo "Must" este en verde y que el paper tenga al menos el avance
metodologico:

1. US-16 (Scrum) y US-17 (paper) — evidencia documental del examen.
2. US-12/US-13/US-14 — consolidar MVVM y pantallas.
3. US-06/US-08 completados contra el backend en modo mock.

## Historias aplazadas (Won't for now)

- Reentrenamiento on-device con TFLite (version futura).
- Roles y permisos avanzados; el login sigue en modo mock.
- Persistencia del token entre sesiones (`SharedPreferences`).
