# Mejora implementada: Capa de seguridad clínica

Mejora sustancial y demostrable del aplicativo: convierte la salida del modelo
en una **recomendación de uso clínico con triaje**, en lugar de mostrar una
clase sin contexto. Es el punto que permite sustentar que la app no "adivina":
**sabe cuándo no es concluyente y obliga a derivar a un especialista**.

## 1. Qué se agregó

| Componente | Descripción |
| --- | --- |
| **Triaje por confianza** | Si la confianza es menor al umbral (0.70), el resultado se marca como `no_concluyente` y no se fuerza un diagnóstico. |
| **Margen top-1 / top-2** | Si las dos clases más probables están casi empatadas (margen < 0.10), el resultado también es `no_concluyente`, aunque la confianza absoluta sea alta. |
| **Nivel de riesgo** | `bajo` (sin tumor), `medio` (tumor con confianza moderada), `alto` (tumor con confianza >= 0.90), `no_concluyente`. |
| **Recomendación clínica** | Texto accionable por nivel, siempre remitiendo al especialista. |
| **Ruta de derivación en la app** | Botón "Ver ruta de derivación" que abre un paso a paso: llevar la MRI original, mostrar resultado + Grad-CAM, confirmación por radiólogo/neuroradiólogo y registro del feedback humano. |
| **Paridad backend / offline** | La misma lógica se aplica en el backend (FastAPI) y en el modelo local ONNX, para que el comportamiento no cambie sin conexión. |
| **Compatible hacia atrás** | Los campos nuevos tienen valores por defecto; los clientes antiguos siguen funcionando. |

## 2. Justificación de cada decisión

1. **Umbral de confianza 0.70.** Es una salvaguarda conservadora: por debajo de
   ese valor, el modelo no tiene evidencia suficiente para una clase. Evita el
   error clásico de "forzar" la clase más probable cuando todas son marginales.
2. **Margen top-1 / top-2.** La confianza absoluta puede ser alta y aun así
   haber ambigüedad entre dos clases (p. ej. glioma 0.40 vs. meningioma 0.38).
   El margen detecta esa ambigüedad, que la confianza sola no ve.
3. **Riesgo por clase.** Un hallazgo tumoral no es lo mismo que un estudio sin
   hallazgos: el primero exige derivación, el segundo solo confirmación. El
   nivel de riesgo permite priorizar la acción.
4. **Recomendación explícita.** No basta con un número; el usuario necesita
   saber qué hacer. Cada nivel tiene un texto accionable y el disclaimer se
   mantiene visible.
5. **Ruta de derivación.** Cierra el ciclo clínico: la app no termina en el
   resultado, sino en una acción segura (llevar el estudio a un especialista).
6. **Paridad online/offline.** El modo offline es una fortaleza del proyecto;
   si la seguridad solo existiera en el backend, el usuario sin conexión
   quedaría desprotegido. Por eso la lógica se replica en Dart
   (`frontend/lib/core/clinical_safety.dart`).

## 3. Contrato de la API (solo campos nuevos)

`POST /api/v1/predict` ahora devuelve, además del contrato existente:

```json
{
  "label": "glioma",
  "confidence": 0.95,
  "probabilities": { "glioma": 0.95, "meningioma": 0.02, "pituitario": 0.02, "no_tumor": 0.01 },
  "is_conclusive": true,
  "triage_level": "alto",
  "recommendation": "Hallazgo tumoral con alta confianza. Deriva a un especialista...",
  "confidence_threshold": 0.70,
  "top_two_margin": 0.93
}
```

`GET /api/v1/predictions/{id}` también expone `is_conclusive`, `triage_level`,
`recommendation` y `top_two_margin` (recalculados al vuelo, sin cambiar la base
de datos).

Los umbrales son configurables por entorno:

```env
CLINICAL_CONFIDENCE_THRESHOLD=0.70
CLINICAL_MARGIN_THRESHOLD=0.10
CLINICAL_HIGH_CONFIDENCE_THRESHOLD=0.90
```

## 4. Experiencia de usuario

En la pantalla **Analizar** (y en el detalle del historial) aparece una nueva
tarjeta **"Capa de seguridad clínica"**:

- Insignia con el nivel: **Riesgo bajo / medio / alto / No concluyente**.
- Recomendación clínica en lenguaje claro.
- Métricas auditables: **umbral mínimo** y **margen top-1/top-2**.
- Botón **"Ver ruta de derivación"** cuando el caso lo requiere.

Ejemplo demostrable: al clasificar una imagen con confianza baja (o con dos
clases casi empatadas), la app muestra **"No concluyente"** y la ruta de
derivación, en lugar de un diagnóstico forzado.

## 5. Alineación con los ODS

- **ODS 3 — Salud y bienestar** (principal): la capa de seguridad reduce el
  riesgo de interpretación errónea y promueve la derivación oportuna
  (metas 3.8 y 3.d).
- **ODS 9 — Innovación**: incorpora una salvaguarda de IA explicable y
  auditable en un dispositivo móvil.
- **ODS 10 — Reducción de desigualdades**: funciona offline y en dispositivos
  de gama baja, sin costo por inferencia.
- **ODS 4 — Educación de calidad**: la recomendación y la ruta de derivación
  educan al usuario sobre el uso correcto de la herramienta.
- **ODS 17 — Alianzas**: la ruta de derivación formaliza la colaboración con
  especialistas en salud para el aval clínico.

## 6. Guion de demostración al profesor (5 minutos)

1. **Backend con pesos reales**: `uvicorn app.main:app --reload` y abrir
   `/docs`. Ejecutar `POST /predict` con una MRI.
2. Mostrar la respuesta: `triage_level`, `recommendation`, `confidence_threshold`
   y `top_two_margin` además de `label` y `confidence`.
3. **App Flutter**: clasificar una imagen y mostrar la tarjeta
   "Capa de seguridad clínica" con el nivel de riesgo.
4. **Caso de seguridad**: usar una imagen ambigua o de baja confianza; la app
   debe mostrar **"No concluyente"** y habilitar "Ver ruta de derivación".
5. **Historial**: abrir el detalle de una predicción y ver la misma tarjeta
   (consistencia entre resultado y auditoría).
6. **Modo offline**: activar modo avión, clasificar y comprobar que el triaje
   también se calcula en local.
7. Cerrar con la evidencia de pruebas (sección 7).

## 7. Evidencia de pruebas

Backend (`backend/`):

```bash
./.venv/bin/python -m pytest -q
# 56 passed
```

Frontend (`frontend/`):

```bash
flutter analyze   # No issues found!
flutter test      # 40 tests passed
```

Pruebas nuevas específicas:

- `backend/tests/test_clinical_safety.py`: 7 casos de la lógica de triaje.
- `backend/tests/test_predict.py`: el contrato y el detalle exponen la capa de
  seguridad de forma coherente.
- `frontend/test/clinical_safety_test.dart`: 9 casos (lógica, respaldo local y
  parseo de modelos).

## 8. Límites y aval de especialista

Esta mejora **no sustituye la validación clínica**. Para afirmar que la app
está "avalada por un especialista en salud" falta:

1. Validación ciega contra lecturas de un radiólogo/neuroradiólogo certificado.
2. Revisión de que los Grad-CAM corresponden a regiones anatómicas plausibles.
3. Protocolo firmado de uso como **soporte a la decisión** (no diagnóstico).
4. Registro normativo como software médico (SaMD) si se usa con pacientes.

La capa de seguridad es precisamente el puente técnico que hace posible ese
aval: demuestra que el sistema sabe cuándo no es confiable y deriva.

## 9. Reporte PDF y mejoras de interfaz (segunda iteración)

### Exportar reporte PDF
- Botón **"Exportar reporte PDF"** en el resultado (`ResultCard`) y en el
  detalle del historial, más una acción compacta en el AppBar del detalle.
- El PDF incluye: encabezado, resultado con color de triaje, recomendación
  clínica, tabla de probabilidades por clase, mapa Grad-CAM (si está
  disponible), trazabilidad (modelo, latencia, origen, fecha) y disclaimer.
- Se genera con el paquete `pdf` y se comparte/guarda con `printing`
  (`Printing.sharePdf`), que abre la hoja del sistema en Android/iOS y la
  descarga en web/escritorio.
- Si el Grad-CAM no se puede descargar, el reporte se genera igual sin imagen.

### Mejoras visuales / UX
- **Banner de seguridad clínica** visible en la pantalla principal: comunica
  que los resultados no concluyentes se derivan a un especialista.
- **Botón "Nueva clasificación"** después del resultado para reiniciar el flujo
  sin salir de la pantalla.
- **Acción de exportar** integrada en el detalle, además del botón principal.
- Colores de triaje centralizados en `AppTheme` (`triageColors` y
  `triageLabels`), reutilizados por la tarjeta y por el PDF.

### Nota de compatibilidad de dependencias
`pdf 3.12` limita `archive` a `<4.1.0`, pero `image >=4.11` usa
`archive.decodeLazy` (no disponible en `archive 4.0.x`). Por eso `image` se fijó
como `>=4.3.0 <4.11.0` en `pubspec.yaml`.

### Pruebas ejecutadas en esta iteración (mínimas e inteligentes)
```bash
flutter analyze                                      # No issues found!
flutter test test/clinical_safety_test.dart \
             test/report_service_test.dart           # 11 tests passed
```
No se ejecutó la suite completa en esta iteración, según lo solicitado.

## 10. Archivos modificados / agregados

**Backend**

- `backend/app/services/clinical_safety.py` (nuevo): lógica de triaje.
- `backend/app/core/config.py`: umbrales configurables.
- `backend/app/schemas/prediction.py`: campos nuevos en `/predict` y detalle.
- `backend/app/api/v1/endpoints/predict.py`: cálculo y respuesta.
- `backend/tests/test_clinical_safety.py` (nuevo).
- `backend/tests/test_predict.py`: aserciones de la capa de seguridad.

**Frontend**

- `frontend/lib/core/clinical_safety.dart` (nuevo): espejo de la lógica.
- `frontend/lib/data/models/prediction_model.dart`: campos y respaldo local.
- `frontend/lib/data/models/prediction_detail.dart`: campos y respaldo local.
- `frontend/lib/data/services/onnx_predictor_io.dart`: triaje en offline.
- `frontend/lib/core/theme.dart`: colores y etiquetas de triaje.
- `frontend/lib/widgets/clinical_safety_card.dart` (nuevo): tarjeta y ruta.
- `frontend/lib/data/services/report_service.dart` (nuevo): generación del PDF.
- `frontend/lib/widgets/export_report_button.dart` (nuevo): exportar/compartir.
- `frontend/lib/widgets/result_card.dart`: triaje + exportación.
- `frontend/lib/views/prediction_detail_view.dart`: triaje + exportación.
- `frontend/lib/views/home_view.dart`: banner de seguridad + nueva clasificación.
- `frontend/pubspec.yaml`: `pdf`, `printing` y pin de `image`.
- `frontend/test/clinical_safety_test.dart` (nuevo).
- `frontend/test/report_service_test.dart` (nuevo).

**Documentación**

- `docs/mejora-capa-seguridad-clinica.md` (este archivo).
- `README.md`: referencia a esta mejora.
