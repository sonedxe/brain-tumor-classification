# Figuras del articulo (LACCEI)

Figuras listas para insertar en el articulo. Todas se generaron a partir del
codigo y la aplicacion reales, no son mockups.

| Archivo | Contenido | Tamano |
| --- | --- | --- |
| `figura-01-modelo-datos.png` | Diagrama E-R del modelo de datos real (8 tablas) | 2400 px de ancho, 3x |
| `figura-02-endpoints.png` | Documentacion interactiva de la API (Swagger `/docs`) | 1484 px de ancho |
| `figura-03-pantallas-moviles.png` | Las tres pantallas moviles en marcos de telefono | 4742x3176 |
| `figura-03-pantalla-analizar.png` | Pantalla "Analizar" (MRI cargada + veredicto) | 1254x2700 |
| `figura-03-pantalla-resultado.png` | Resultado: probabilidades por clase + Grad-CAM | 1254x2700 |
| `figura-03-pantalla-historial.png` | Historial de predicciones | 1254x2700 |
| `modelo-datos.mmd` | Fuente Mermaid del diagrama (versionable) | - |

## Pies de figura sugeridos

- **Figura 1.** Modelo de datos del backend (FastAPI + SQLAlchemy + SQLite).
  Ocho tablas normalizadas: catalogo de clases, registro de modelos, imagenes
  deduplicadas por hash, predicciones, distribucion de probabilidades, revision
  humana y sesiones de autenticacion. No se persiste ningun dato identificable
  del paciente.
- **Figura 2.** Documentacion interactiva de la API (OpenAPI/Swagger). Trece
  operaciones agrupadas en seis etiquetas: salud, predicciones, historial,
  catalogos, analitica y autenticacion.
- **Figura 3.** Aplicativo movil (Flutter, MVVM) en ejecucion: seleccion de la
  MRI, resultado de la clasificacion con Grad-CAM y confianza por clase, e
  historial de predicciones. Inferencia real con MobileNetV3.

## Como se regeneraron (reproducible)

```bash
# 1. Diagrama de datos (Mermaid -> PNG)
npx -y @mermaid-js/mermaid-cli@11 -i modelo-datos.mmd -o figura-01-modelo-datos.png \
    -w 2400 -b white -s 3

# 2. Endpoints: con el backend corriendo, capturar http://127.0.0.1:8000/docs

# 3. Pantallas moviles: build web en viewport 390x844 (DPR 3) y captura con Playwright
cd frontend && flutter build web --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Las capturas moviles se tomaron con un viewport de **390x844 px** (dimensiones
de telefono), factor de escala 3 y se enmarcaron con un bisel de telefono.

## Nota sobre las imagenes de MRI

Las capturas usan una imagen de resonancia del conjunto de datos local
(`Training/glioma`, Brain Tumor MRI Dataset). Para la version publica del
articulo, verificar la licencia del dataset y, si corresponde, sustituir la
imagen por una con permiso explicito de reproduccion.

## Convencion de nombres

`figura-NN-descripcion.png`, donde `NN` es el orden de aparicion en el
articulo. Los nombres se pueden renombrar al estilo del template LACCEI.
