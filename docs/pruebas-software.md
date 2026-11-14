# Plan y documento de pruebas de software

**Proyecto:** Clasificación de tumores cerebrales en imágenes de resonancia magnética (MRI) mediante CNN ligeras, Grad-CAM y una aplicación móvil Flutter con arquitectura MVVM.

**Documento:** Estrategia, casos, ejecución, evidencia y criterios de salida de las pruebas de software.

| Campo | Valor |
| --- | --- |
| Versión | 1.0 |
| Fecha de ejecución | 13 de noviembre de 2026 |
| Estado | Línea base de calidad para la sustentación |
| Autor | *(completar nombre y código)* |
| Curso | Taller de Desarrollo de Proyectos de Software *(ajustar)* |
| Universidad | Universidad Nacional Mayor de San Marcos |
| Repositorio | `sonedxe/brain-tumor-classification` |
| Alcance | Backend, frontend, ML, modo offline, seguridad clínica y despliegue demo |

> **Aviso.** Las pruebas descritas verifican el comportamiento del software,
> **no** la validez clínica del modelo. Un resultado `PASS` no convierte a la
> app en un dispositivo médico ni sustituye la lectura de un radiólogo.

---

## 1. Resumen ejecutivo

El proyecto tiene una línea base de pruebas sólida para su tamaño:

| Suite | Herramienta | Casos | Resultado de la corrida |
| --- | --- | ---: | --- |
| Backend / API | `pytest` + FastAPI `TestClient` | **56** | **56 passed** (exit 0) |
| Frontend / ViewModels / offline | `flutter test` | **42** | **42 passed** |
| Análisis estático Flutter | `flutter analyze` | — | **No issues found** |
| ML / pipeline | `unittest` + `smoke_test.py` | **13** + 8 checks | 13 definidas; smoke 6/7 (cortado por `scikit-learn`; completo = 8/8) |
| E2E automatizado | — | 0 | **No implementado** |
| Carga / seguridad / accesibilidad | — | 0 | **No ejecutado**; planificado en este documento |

**Conclusión:** el sistema es **apto para una demostración académica** y para
un piloto controlado sin pacientes reales. No es apto todavía para uso clínico
ni para producción con SLA, porque faltan pruebas E2E automatizadas, pruebas de
carga/estrés, auditoría de seguridad, validación externa del modelo y
cobertura medida.

Este documento no se limita a reportar lo que ya pasa: define el **plan
completo** (niveles, entornos, casos, datos, criterios de entrada/salida,
trazabilidad, métricas y gestión de defectos) y distingue con claridad entre:

- **PASS:** automatizado y ejecutado en esta corrida.
- **AUTO:** automatizado, pero no ejecutado en este entorno (requiere
  dependencias ML o hardware).
- **PEND:** planificado, todavía no implementado/ejecutado.
- **N/A:** fuera de alcance.

### 1.1 Hallazgos principales

1. **La API está bien cubierta a nivel de contrato.** Las 56 pruebas validan
   `predict`, historial, catálogos, feedback, estadísticas, autenticación,
   validación de imágenes y la capa de seguridad clínica.
2. **El frontend está bien cubierto en lógica.** Las 42 pruebas cubren DTOs,
   `ApiService`, ViewModels, offline, triaje clínico y generación de PDF.
3. **La pirámide se apoya en unitarias/API, no en E2E.** No hay un flujo
   automatizado que abra la app, elija una imagen, llame al backend y valide el
   resultado en pantalla.
4. **No hay cobertura medida.** `pytest-cov` y `flutter test --coverage` no
   están configurados; no se puede afirmar un porcentaje.
5. **El gate de ML no está reproducible en el entorno backend.** `smoke_test`
   falla en `metrics` porque `scikit-learn` no está instalado en
   `backend/.venv`; el entorno ML (`ml/requirements-ml.txt`) sí lo incluye.
6. **Hay documentación desactualizada.** El README y algunos documentos dicen
   37 pruebas backend y 23 frontend; la realidad es 56 y 42. También se habla
   de `smoke_test` 7/7, pero el script actual tiene 8 llamadas a `check()`:
   métricas y Grad-CAM son checks separados. La corrida corta en métricas
   reporta 6/7 porque añade un check de error y no llega a Grad-CAM.
7. **Las pruebas de seguridad clínica están duplicadas con buena intención**
   (backend y frontend), lo que reduce el riesgo de que el triaje se comporte
   distinto online/offline.
8. **Faltan pruebas de refresco/revocación de sesión.** El código implementa
   `refresh` y `logout`, pero `test_auth.py` no los cubre; es el hueco más
   importante de la autenticación.

### 1.2 Recomendación

Antes de la sustentación:

- Ejecutar y adjuntar la salida de `pytest`, `flutter test` y
  `flutter analyze`.
- Instalar `ml/requirements-ml.txt` en un entorno ML y correr
  `python ml/smoke_test.py` hasta 8/8 (7/7 en la nomenclatura previa).
- Añadir pruebas de `refresh` y `logout`.
- Añadir un E2E mínimo (Patrol o integration_test) para el flujo
  subir imagen → resultado → historial.
- Medir cobertura y publicar el número, aunque sea bajo.
- No presentar la app como dispositivo médico; mantener el aviso y el triaje.

---

## 2. Alcance y objetivos

### 2.1 Alcance

**Incluye:**

- API REST: `predict`, `history`, `health`, `models`, `classes`, `stats`,
  `predictions/{id}`, `feedback`, `auth/*`.
- Inferencia real con PyTorch, Grad-CAM y capa de seguridad clínica.
- App Flutter: modelos/DTOs, `ApiService`, ViewModels, historial, detalle,
  autenticación, panel, PDF y modo offline.
- Pipeline ML: etiquetas, partición, dataloader, modelos, métricas, Grad-CAM y
  exportación ONNX.
- Modo offline: almacenamiento local, predicción ONNX, sincronización.
- Despliegue demo: variables de entorno, health check, APK y web.
- Requisitos no funcionales: rendimiento, seguridad, privacidad,
  compatibilidad, accesibilidad, respaldo y recuperación.

**No incluye:**

- Validación clínica con pacientes o radiólogos.
- Certificación regulatoria (SaMD, IEC 62304, ISO 13485, HIPAA/GDPR).
- Pentest externo, auditoría formal de código o análisis de caja blanca.
- Pruebas de alta disponibilidad multirregión.
- Reentrenamiento o ajuste fino del modelo.
- Pruebas de modelos adversarios o *fairness* por subgrupos demográficos.

### 2.2 Objetivos de calidad

| Objetivo | Métrica | Meta | Estado actual |
| --- | --- | --- | --- |
| Corrección funcional | Casos P1/P2 pasados | 100 % | API/FE: 98 casos automatizados en verde; E2E pendiente |
| Cobertura de código | Líneas backend / frontend | ≥ 80 % / ≥ 70 % | **No medida** |
| Cobertura de rutas críticas | predict, auth, offline, triaje | 100 % | Parcial: unitarias/API sí; E2E no |
| Rendimiento warm | p95 de `POST /predict` | < 3 s | No medido en servidor |
| Cold start | Primer request tras *sleep* | < 60 s | Diseñado con timeout 60 s; no medido |
| Concurrencia | 10 usuarios, 5 min | Error < 1 % | No medido |
| Seguridad | Hallazgos críticos/altos | 0 | No auditado |
| Privacidad | PHI en DB/logs | 0 | Verificado por diseño y prueba API |
| Disponibilidad | Uptime mensual | ≥ 99.0 % | No medida |
| Defectos abiertos | S1/S2 al cierre | 0 | 0 conocidos |
| Regresión | Suite completa por release | 100 % | Backend/FE sí; ML condicionado |

### 2.3 Preguntas que responde este plan

1. ¿El contrato HTTP se mantiene y devuelve lo que el cliente espera?
2. ¿La app maneja bien los estados de carga, éxito, error y vacío?
3. ¿El modo offline clasifica y sincroniza sin corromper datos?
4. ¿La capa de triaje clínico se comporta igual online y offline?
5. ¿La autenticación protege las sesiones y no filtra contraseñas?
6. ¿El sistema se comporta bien con imágenes inválidas, grandes o maliciosas?
7. ¿El modelo es reproducible y sus métricas son defendibles?
8. ¿La app soporta los dispositivos y navegadores objetivo?
9. ¿El despliegue resiste un reinicio, un backup y una restauración?
10. ¿Qué falta para considerar el sistema “listo” para un piloto?

---

## 3. Referencias normativas y del proyecto

### 3.1 Normas y guías

- **ISO/IEC 25010** — modelo de calidad de producto de software.
- **ISO/IEC/IEEE 29119** — conceptos y procesos de pruebas de software.
- **ISTQB Foundation Level** — vocabulario y niveles de prueba.
- **OWASP ASVS** — verificación de seguridad de aplicaciones.
- **OWASP Top 10** — riesgos de seguridad web.
- **NIST SP 800-190** — seguridad de contenedores.
- **Google SRE** — SLI/SLO, presupuesto de error y postmortems.
- **Scrum Definition of Done** del proyecto
  (`docs/scrum/definition-of-done.md`).

### 3.2 Documentos del proyecto

- `README.md` — arquitectura, contrato, puesta en marcha, offline y APK.
- `docs/informe-universitario.md` — objetivos, resultados y discusión.
- `docs/mejora-capa-seguridad-clinica.md` — triaje por confianza/margen.
- `docs/diseno-pantallas.md` — pantallas y correspondencia MVVM.
- `docs/scrum/product-backlog.md` — historias US-01 a US-17.
- `docs/scrum/sprints.md` — incrementos y deuda técnica.
- `docs/arquitectura-cloud.md` — arquitectura propuesta y SLOs.
- `ml/evaluation/reports/comparison.json` — métricas de los cinco modelos.
- `backend/tests/`, `frontend/test/`, `ml/tests/` — suites automatizadas.

### 3.3 Convenciones

- **ID de caso:** `API-xx`, `AUTH-xx`, `SAFE-xx`, `FE-xx`, `ML-xx`, `NF-xx`,
  `E2E-xx`.
- **Prioridad:** P1 (crítico), P2 (alto), P3 (medio), P4 (bajo).
- **Estado:** PASS, AUTO, PEND, N/A.
- **Severidad de defecto:** S1–S4 (sección 8.2).
- **Entorno:** local, CI, staging, prod/demo.

---

## 4. Estrategia de pruebas

### 4.1 Enfoque

Se adopta un enfoque **basado en riesgo**, con automatización prioritaria de
las rutas que pueden causar daño o pérdida de datos:

1. **Predict y triaje clínico:** si falla, el usuario recibe una salida
   incorrecta o no concluyente.
2. **Autenticación y sesiones:** si falla, se comprometen cuentas.
3. **Persistencia y sincronización offline:** si falla, se pierden datos.
4. **Validación de archivos:** si falla, se expone el servicio a abuso.
5. **Despliegue y recuperación:** si falla, la demo no está disponible.

La estrategia combina:

- **Shift-left:** pruebas unitarias y de contrato en cada commit.
- **Automatización primero:** todo lo repetible se automatiza.
- **Pruebas exploratorias:** para UX, accesibilidad y casos raros.
- **UAT:** guion de demostración con el PO/docente.
- **Observabilidad:** los fallos en producción se detectan con health checks y
  Sentry, no solo con pruebas.

### 4.2 Pirámide de pruebas

```
                         ┌─────────────────────┐
                         │  E2E / UAT (0 auto) │  ~10 escenarios manuales
                         ├─────────────────────┤
                         │ Integración / API   │  56 pruebas backend
                         │ (TestClient)        │
                         ├─────────────────────┤
                         │ Widget / ViewModel  │  42 pruebas Flutter
                         ├─────────────────────┤
                         │ Unitarias ML        │  13 pruebas unittest
                         │ + smoke (8 checks)  │
                         └─────────────────────┘
```

**Lectura:** la base está bien; la cúspide (E2E) está vacía. Para una demo es
aceptable; para un piloto hay que añadir al menos un E2E y pruebas de carga.

### 4.3 Niveles de prueba

| Nivel | Qué verifica | Herramienta | Responsable | Frecuencia |
| --- | --- | --- | --- | --- |
| Unitario | Funciones, DTOs, reglas de triaje, ViewModels | `pytest`, `flutter test`, `unittest` | Devs | Cada commit |
| Integración/API | Contrato HTTP, DB, autenticación, inferencia | FastAPI `TestClient`, SQLite temporal | Backend | Cada commit |
| Widget/UI | Estados de pantalla, parsing, interacción básica | `flutter_test` | Frontend | Cada commit |
| E2E | Flujo completo app → API → resultado → historial | Patrol / integration_test (propuesto) | QA | Cada release |
| UAT | Guion de usuario y aceptación | Manual | PO + QA | Cada release |
| No funcional | Carga, seguridad, compatibilidad, accesibilidad | k6, ZAP, matrices manuales | QA + Ops | Antes de piloto |
| Regresión | Que lo anterior siga funcionando | Suite completa | CI | Cada release |

### 4.4 Tipos de prueba

| Tipo | Objetivo | Ejemplos |
| --- | --- | --- |
| **Funcional** | Verificar requisitos | Clasificar, historiar, autenticar |
| **Contrato** | Verificar forma y tipos del JSON | `PredictionResponse`, `HistoryEntry` |
| **Regresión** | Evitar roturas | Suite completa en cada PR |
| **Smoke** | Validar lo mínimo tras desplegar | `/health`, `/predict` con imagen |
| **Sanity** | Validar un cambio puntual | Nuevo campo de triaje |
| **Integración** | Verificar capas juntas | API + SQLite + modelo |
| **E2E** | Verificar el viaje del usuario | App → API → resultado |
| **Rendimiento** | Latencia, throughput, memoria | k6, 10–20 VUs |
| **Carga/estrés** | Límites y degradación | Pico de 20 VUs |
| **Seguridad** | AuthN/Z, input, secretos, dependencias | OWASP ASVS, ZAP |
| **Compatibilidad** | Dispositivos, navegadores, versiones | Android 8+, iOS 13+, Chrome |
| **Accesibilidad** | Contraste, semántica, tamaño de texto | Flutter semantics, manual |
| **Usabilidad** | Claridad del resultado y del triaje | Guion UAT |
| **Privacidad** | Sin PHI en DB/logs/archivos | SQL/logs audit |
| **Respaldo/DR** | Restaurar DB y media | Simulacro |
| **ML** | Reproducibilidad, métricas, Grad-CAM | `smoke_test`, `unittest` |
| **Offline** | Predicción y sincronización sin red | Modo avión / fake connectivity |
| **Accesibilidad clínica** | Triaje seguro en baja confianza | Casos SAFE |

### 4.5 Criterios de entrada

Antes de ejecutar una ronda:

- [ ] Build y dependencias instaladas.
- [ ] Variables de entorno de prueba definidas (sin secretos reales).
- [ ] Base de datos de prueba vacía o restaurada.
- [ ] Modelo/checkpoint disponible (`best.pt` real o checkpoint de prueba).
- [ ] Datos de prueba preparados (imágenes sintéticas + test split).
- [ ] Versión de código identificada (commit/tag).
- [ ] Suite de humo en verde.
- [ ] Backup del entorno si se va a migrar/probar datos.

### 4.6 Criterios de salida

Una release se considera lista cuando:

- [ ] 100 % de casos P1 y P2 ejecutados.
- [ ] ≥ 95 % de casos ejecutados en verde; el resto con justificación.
- [ ] 0 defectos S1/S2 abiertos.
- [ ] Cobertura backend ≥ 80 % y frontend ≥ 70 % (o justificación).
- [ ] Cobertura 100 % de rutas críticas (predict, auth, offline, triaje).
- [ ] Rendimiento warm p95 < 3 s y error < 1 % con 10 VUs.
- [ ] Sin hallazgos críticos/altos de seguridad.
- [ ] UAT firmada por PO/docente.
- [ ] Documentación y `CHANGELOG` actualizados.
- [ ] Backup y rollback probados.

### 4.7 Suspensión y reanudación

**Suspender** si:

- El entorno no está disponible o el modelo no carga.
- La base de datos está corrupta.
- Una dependencia externa (Render, GitHub) está caída.
- Un defecto S1 bloquea el flujo principal.

**Reanudar** cuando:

- La causa está corregida y verificada.
- Se restauró el entorno/DB.
- Se documentó el incidente y su impacto en la ronda.

---

## 5. Arquitectura de pruebas y entornos

### 5.1 Flujo de pruebas

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Local      │ →  │  CI         │ →  │  Staging    │ →  │ Prod/demo   │
│  dev/test   │    │  GitHub     │    │  Render/    │    │  Oracle/    │
│             │    │  Actions    │    │  Oracle     │    │  Render     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
   unitarias         suite + build      smoke + E2E        health + UAT
   rápidas           imagen             carga/seguridad    monitoreo
```

### 5.2 Matriz de entornos

| Entorno | SO / runtime | Flutter | DB | Modelo | Propósito |
| --- | --- | --- | --- | --- | --- |
| Local macOS | macOS ARM64 · Python 3.12 | 3.41.6 / Dart 3.11 | SQLite temporal | `best.pt` / checkpoint | Desarrollo y suite |
| Local Windows | Windows 11 · PowerShell · Python 3.12 | 3.41.6 | SQLite | `best.pt` | Entrenamiento ML (guía) |
| CI | Ubuntu latest · Python 3.12 | 3.41.6 | SQLite `test.db` | Checkpoint `shufflenetv2` aleatorio | Automatización |
| Staging | Render Free / Oracle · Python 3.12 | Web/APK | SQLite/Postgres | MobileNetV3 | Validación pre-release |
| Prod/demo | Oracle / Render · Python 3.12 | APK/Web | SQLite/Postgres | MobileNetV3 | Sustentación |
| Android | Emulador/dispositivo | — | Local | ONNX | Compatibilidad/offline |
| iOS | Simulador/dispositivo | — | Local | ONNX | Compatibilidad |
| Web | Chrome/Edge/Firefox/Safari | — | Local | ONNX/API | Compatibilidad |

> **Nota:** la corrida de esta línea base se hizo en macOS ARM64. Los
> resultados pueden variar en Linux (por ejemplo, `ru_maxrss` se mide en KB y
> la versión de `torch` puede tener otro rendimiento).

### 5.3 Datos de prueba

| Tipo | Fuente | Uso | Privacidad |
| --- | --- | --- | --- |
| Imagen sintética PNG/JPEG 256×256 | `tests/conftest.py`, `_png()` | Contrato, validación, determinismo | Sin PHI |
| Imagen aleatoria 224×224 | `test_inference_real.py` | Inferencia y Grad-CAM | Sin PHI |
| Checkpoint aleatorio `shufflenetv2` | `conftest.py` | Evita depender de `best.pt` | Sin datos |
| Test split 1,600 imágenes | Kaggle Brain Tumor MRI | Evaluación de métricas | Público, no PHI |
| Imágenes de demostración | MRI de ejemplo | UAT/manual | Sin nombres |
| Datos offline | `LocalDB` en memoria/temporal | Cola y sincronización | Sin PHI |

**Reglas:**

- No usar imágenes de pacientes reales en el repositorio, CI ni demos.
- No incluir nombres de archivo con datos personales; el backend solo guarda
  el hash, pero el nombre podría filtrarse en logs si se registra.
- Semilla 42 y split fijo para reproducibilidad.
- Los datos de prueba deben ser pequeños y versionables; el dataset completo
  se descarga aparte.

### 5.4 Dobles de prueba

| Doble | Dónde | Qué sustituye |
| --- | --- | --- |
| `FakeApiClient` / `MockClient` | Frontend | HTTP real |
| `SessionStore` falso / `SharedPreferences.setMockInitialValues` | Frontend | Persistencia |
| `LocalDB` temporal | Frontend offline | SQLite local |
| `TestClient` | Backend | Servidor Uvicorn real |
| Checkpoint aleatorio | Backend | Pesos entrenados |
| `tmp_path` / SQLite temporal | Backend | DB de producción |
| `unittest.mock` | ML | Entrenamiento/evaluación reales |

---

## 6. Herramientas

### 6.1 Instaladas y en uso

| Herramienta | Versión | Uso |
| --- | --- | --- |
| `pytest` | 8.3.4 | Suite backend |
| `httpx` | 0.28.1 | Cliente de pruebas |
| FastAPI `TestClient` | 0.115.6 | Integración API |
| Pillow | 11.0.0 | Generación/validación de imágenes |
| PyTorch | 2.14.1 | Inferencia/checkpoint de prueba |
| torchvision | 0.29.1 | Arquitecturas |
| `unittest` | Python 3.12 | Pruebas ML |
| Flutter SDK | 3.41.6 | App y tests |
| `flutter_test` | SDK | Widget/unitarias |
| `flutter_lints` | 6.0.0 | Análisis estático |
| GitHub Actions | — | CI y release APK |
| `smoke_test.py` | — | Gate del pipeline ML |

### 6.2 Recomendadas (pendientes)

| Herramienta | Uso | Prioridad |
| --- | --- | --- |
| `pytest-cov` | Cobertura backend | P1 |
| `flutter test --coverage` + `lcov` | Cobertura frontend | P1 |
| `patrol` o `integration_test` | E2E Flutter | P1 |
| `k6` o `Locust` | Carga/estrés | P2 |
| OWASP ZAP | Seguridad web/API | P2 |
| `pip-audit` | Vulnerabilidades Python | P2 |
| Trivy | Imagen/contenedor | P2 |
| Dependabot | Actualizaciones | P2 |
| Playwright | Web E2E | P3 |
| Firebase Test Lab | Dispositivos reales | P3 |
| BrowserStack | Matriz iOS/Android | P3 |
| `flutter semantics` / Accessibility Scanner | Accesibilidad | P3 |

### 6.3 Comandos de referencia

```bash
# Backend
cd backend
python -m pytest -q
python -m pytest -q --cov=app --cov-report=term-missing   # requiere pytest-cov

# Frontend
cd frontend
flutter analyze
flutter test
flutter test --coverage                                   # genera coverage/lcov.info
flutter test test/clinical_safety_test.dart                # suite específica

# ML
python ml/smoke_test.py
python -m unittest discover -s ml/tests -p "test_*.py" -v
python ml/training/run_all.py --skip-train                 # re-evaluar checkpoints

# API manual
cd backend && uvicorn app.main:app --reload
curl -s http://localhost:8000/api/v1/health | jq .
curl -s -F "file=@mri.png" http://localhost:8000/api/v1/predict | jq .

# Carga (ejemplo)
k6 run tests/load/predict.js
```

---

## 7. Organización, roles y responsabilidades

### 7.1 Roles

| Rol | Responsabilidad en pruebas |
| --- | --- |
| **Product Owner** | Define criterios de aceptación; firma UAT; prioriza defectos |
| **QA Lead** | Planifica rondas; mantiene casos; reporta métricas |
| **Backend Dev** | Pruebas de API, DB, auth e inferencia |
| **Frontend Dev** | Pruebas de DTOs, ViewModels, widgets y offline |
| **ML Dev** | Pruebas de pipeline, métricas, Grad-CAM y exportación |
| **Ops/Infra** | Entornos, despliegue, backups, carga y monitoreo |
| **Asesor clínico (opcional)** | Revisa que el triaje y los textos sean seguros |

### 7.2 RACI

| Actividad | PO | QA | Backend | Frontend | ML | Ops |
| --- | --- | --- | --- | --- | --- | --- |
| Plan de pruebas | A | R | C | C | C | C |
| Casos funcionales | A | R | C | C | I | I |
| Automatización API | I | A | R | I | I | I |
| Automatización Flutter | I | A | I | R | I | I |
| Pruebas ML | I | C | I | I | R | I |
| Carga/seguridad | I | A | C | C | I | R |
| UAT | R | C | I | I | I | I |
| Release gate | A | R | C | C | C | C |
| Incidentes | I | C | R | R | C | A |

**R** = responsable, **A** = aprueba, **C** = consultado, **I** = informado.

---

## 8. Gestión de configuración y defectos

### 8.1 Configuración

- Cada ronda se ejecuta sobre un commit/tag identificable.
- Las pruebas usan una DB temporal; nunca la DB de producción.
- Los artefactos (logs, reportes, capturas) se guardan en
  `docs/evidencias/<fecha>/` o como artefacto de GitHub Actions.
- Las variables de entorno de prueba se documentan en `.env.example`.
- Los cambios de contrato actualizan DTOs, pruebas y documentación.
- El APK se versiona con `version: 1.0.0+1` y tag `v*`.

### 8.2 Severidad y prioridad

| Severidad | Definición | Ejemplo | SLA de corrección |
| --- | --- | --- | --- |
| **S1 — Crítico** | Pérdida de datos, brecha de seguridad, resultado clínico peligroso, API caída | `predict` devuelve 500 siempre; JWT acepta tokens falsos; se borra el historial | 24 h |
| **S2 — Alto** | Función principal inutilizable o dato corrupto | No se puede subir imagen; login roto; offline sincroniza mal | 3 días |
| **S3 — Medio** | Función secundaria con *workaround* | Historial no pagina; PDF sin Grad-CAM; error de formato | 1 sprint |
| **S4 — Bajo** | Cosmético o texto | Typo; alineación; color | Backlog |

| Prioridad | Criterio |
| --- | --- |
| P1 | Bloquea la demo o la seguridad; se corrige ya |
| P2 | Afecta el flujo principal; se corrige en el sprint |
| P3 | Afecta una función secundaria; se planifica |
| P4 | Mejora deseable; se prioriza con el PO |

### 8.3 Ciclo de vida de un defecto

```
Nuevo → Triado → En progreso → Corregido → Verificado → Cerrado
                     ↑                         │
                     └──── Reabierto ←─────────┘
```

**Regla:** un defecto se cierra solo cuando la prueba que lo detectó pasa y se
añadió una prueba de regresión cuando aporta valor.

### 8.4 Plantilla de defecto

```markdown
### DEF-<id> — <título corto>

- **Severidad:** S1/S2/S3/S4
- **Prioridad:** P1/P2/P3/P4
- **Entorno:** local / CI / staging / prod
- **Versión/commit:**
- **Precondición:**
- **Pasos:**
  1.
  2.
- **Resultado esperado:**
- **Resultado actual:**
- **Evidencia:** log, captura, response HTTP
- **Impacto:**
- **Causa raíz:**
- **Corrección propuesta:**
- **Prueba de regresión:**
```

### 8.5 Plantilla de caso de prueba

```markdown
### <ID> — <nombre>

- **Objetivo:**
- **Precondición:**
- **Datos de entrada:**
- **Pasos:**
  1.
  2.
- **Resultado esperado:**
- **Tipo:** funcional / integración / E2E / no funcional
- **Prioridad:** P1/P2/P3/P4
- **Automatizado:** sí/no
- **Evidencia:**
```

---

## 9. Casos de prueba

> **Cómo leer las tablas.** `Estado` se refiere a la corrida del 13/11/2026.
> `PASS` = automatizado y ejecutado; `AUTO` = automatizado pero no ejecutado en
> este entorno; `PEND` = planificado; `N/A` = fuera de alcance. Los casos
> manuales incluyen los pasos en la sección 14 (UAT).

### 9.1 API REST

| ID | Caso | Datos / estímulo | Resultado esperado | Prioridad | Estado |
| --- | --- | --- | --- | --- | --- |
| API-01 | Health con modelo cargado | `GET /api/v1/health` | 200; `status=ok`; `model_ready=true`; 4 clases | P1 | PASS |
| API-02 | Contrato de predicción | `POST /predict` con PNG 256×256 | 201; `label` válido; `confidence` 0–1; 4 probabilidades; `gradcam_path`; `model_version`; `inference_ms` | P1 | PASS |
| API-03 | Probabilidades suman 1 | Igual que API-02 | Suma = 1 ± 1e-6; claves = 4 clases | P1 | PASS |
| API-04 | Predicción determinista | Misma imagen dos veces | Misma etiqueta y probabilidades | P1 | PASS |
| API-05 | Historial tras predecir | `GET /history` | 1 registro; hash de 64 hex; etiqueta válida | P1 | PASS |
| API-06 | Sin datos identificables | Archivo llamado `paciente_juan_perez.png` | Respuesta no contiene “paciente” ni “juan”; solo hash | P1 | PASS |
| API-07 | Archivo no imagen | `nota.txt` con texto | 400; mensaje de formato | P1 | PASS |
| API-08 | Archivo vacío | `vacio.png` de 0 bytes | 400 | P1 | PASS |
| API-09 | Imagen demasiado pequeña | PNG 8×8 | 400; dimensiones mínimas | P2 | PASS |
| API-10 | Subida mayor a 10 MB | PNG repetido hasta superar el límite | 413 | P1 | PASS |
| API-11 | Falta el campo `file` | POST sin archivo | 422 | P2 | PASS |
| API-12 | Límite de historial | `limit=0` y `limit=101` | 422 en ambos | P3 | PASS |
| API-13 | Detalle inexistente | `GET /predictions/9999` | 404 | P2 | PASS |
| API-14 | Deduplicación por hash | Dos predicciones de la misma imagen | `total_predictions=2`; `unique_images=1` | P2 | PASS |
| API-15 | Feedback correcto/incorrecto | `POST /predictions/{id}/feedback` con `is_correct=false`, `corrected_label=glioma` | 201; feedback con clase corregida; aparece en el detalle | P1 | PASS |
| API-16 | Feedback con etiqueta inválida | `corrected_label=inventado` | 422 | P2 | PASS |
| API-17 | Resumen de estadísticas | `GET /stats/summary` | Totales, únicos, 5 modelos, media de confianza y distribución | P2 | PASS |
| API-18 | Catálogos | `GET /models`, `GET /classes` | 5 modelos con accuracy; 4 clases en orden canónico; `no_tumor.is_tumor=false` | P2 | PASS |
| API-19 | OpenAPI documenta el contrato | `GET /openapi.json` | Incluye predict, auth, models, classes, detail, feedback, stats | P2 | PASS |

**Cobertura automatizada:** `backend/tests/test_health.py` (4),
`test_predict.py` (13 casos por parametrización), `test_catalog_endpoints.py`
(10), `test_inference_real.py` (10 por parametrización) y `test_auth.py` (12).

### 9.2 Autenticación

| ID | Caso | Datos / estímulo | Resultado esperado | Prioridad | Estado |
| --- | --- | --- | --- | --- | --- |
| AUTH-01 | Registro devuelve tokens | `POST /auth/register` con nombre, email y contraseña válidos | 201; `access_token`, `token_type=bearer`, `name`, `email`, `expires_in`, `refresh_token` | P1 | PASS |
| AUTH-02 | Token es JWT válido | Decodificar `access_token` | Header/payload válidos; `sub` y claims esperados | P1 | PASS |
| AUTH-03 | Contraseña no se guarda en claro | Inspeccionar `users.password_hash` | Hash PBKDF2; no contiene la contraseña | P1 | PASS |
| AUTH-04 | Login correcto | Email/contraseña registrados | 200; tokens nuevos | P1 | PASS |
| AUTH-05 | Email case-insensitive | `User@Example.com` vs `user@example.com` | Login funciona; no duplica | P2 | PASS |
| AUTH-06 | Contraseña incorrecta | Email válido + password errónea | 401; mensaje genérico | P1 | PASS |
| AUTH-07 | Email duplicado | Registrar dos veces el mismo email | 409 | P2 | PASS |
| AUTH-08 | Contraseña corta | Password < mínimo del esquema | 422 | P3 | PASS |
| AUTH-09 | `me` autenticado | `GET /auth/me` con Bearer | 200; id, nombre, email | P1 | PASS |
| AUTH-10 | `me` sin token / token inválido | Sin header / token alterado | 401 en ambos | P1 | PASS |
| AUTH-11 | Refresh rota el token | `POST /auth/refresh` con refresh válido | 200; nuevo access y refresh; el anterior queda revocado | P1 | **PEND** |
| AUTH-12 | Logout revoca la sesión | `POST /auth/logout` y luego refresh | 204; refresh posterior 401 | P1 | **PEND** |

> **Hallazgo:** `AUTH-11` y `AUTH-12` son funcionalidad implementada pero sin
> prueba automatizada en `test_auth.py`. Es el hueco de mayor riesgo de la
> autenticación y debe cerrarse antes de un piloto.

### 9.3 Capa de seguridad clínica (triaje)

| ID | Caso | Datos / estímulo | Resultado esperado | Prioridad | Estado |
| --- | --- | --- | --- | --- | --- |
| SAFE-01 | No tumor concluyente | `no_tumor`, confianza 0.95, margen amplio | `is_conclusive=true`; `triage_level=bajo`; recomienda confirmación | P1 | PASS |
| SAFE-02 | Tumor de alta confianza | `glioma`, 0.95 | `triage_level=alto`; deriva a especialista | P1 | PASS |
| SAFE-03 | Tumor de confianza moderada | `meningioma`, 0.75 | `triage_level=medio`; recomienda revisión | P1 | PASS |
| SAFE-04 | Confianza baja | `glioma`, 0.50 | `is_conclusive=false`; `no_concluyente`; no fuerza diagnóstico | P1 | PASS |
| SAFE-05 | Confianza alta pero margen bajo | 0.80 vs 0.75 | `is_conclusive=false`; `no_concluyente` | P1 | PASS |
| SAFE-06 | Margen expuesto para auditoría | Cualquier caso | `top_two_margin` y `confidence_threshold` presentes | P2 | PASS |
| SAFE-07 | Sin distribución usa confianza | Solo `confidence` | No lanza; margen calculado de forma segura | P3 | PASS |
| SAFE-08 | Paridad backend/offline | Mismos valores en Dart y Python | Mismo `triage_level` y recomendación | P1 | PASS (casos espejo; sin prueba cruzada automática) |

**Cobertura:** `backend/tests/test_clinical_safety.py` (7) y
`frontend/test/clinical_safety_test.dart` (9). La paridad se prueba con los
mismos umbrales en ambos lados.

### 9.4 Frontend Flutter

| ID | Caso | Datos / estímulo | Resultado esperado | Prioridad | Estado |
| --- | --- | --- | --- | --- | --- |
| FE-01 | Parseo de `PredictionModel` | JSON del contrato | Etiqueta, confianza, probabilidades y Grad-CAM correctos | P1 | PASS |
| FE-02 | `no_tumor` y payload incompleto | JSON sin campos opcionales | No lanza; valores por defecto seguros | P2 | PASS |
| FE-03 | `ApiService` resuelve Grad-CAM | `gradcam_path=/static/...` | URL contra la raíz del servidor, no bajo `/api/v1` | P2 | PASS |
| FE-04 | `ApiService` multipart y errores | Archivo en campo `file`; respuesta 422 | Envía `multipart/form-data`; traduce a `ApiException` | P1 | PASS |
| FE-05 | `PredictionViewModel` estados | Inicio, sin imagen, loading, success, error, clear, imagen inválida | `idle` → `loading` → `success`; error sin excepción; `clear` reinicia | P1 | PASS |
| FE-06 | Historial | JSON de `GET /history`, vacío, error | Lista, estado vacío y error con reintento | P1 | PASS |
| FE-07 | Autenticación | Login, restore, logout, 401 | Persiste token/nombre; limpia al salir; 401 no persiste | P1 | PASS |
| FE-08 | Offline: cola local | Predicción sin red | Encola con imagen; lee pendientes; sin duplicados | P1 | PASS |
| FE-09 | Offline: historial y auth | Backend caído | Muestra caché + pendientes; login/registro local; rechaza credenciales malas | P1 | PASS |
| FE-10 | Triaje clínico en Dart | Mismos casos que SAFE | Mismos niveles y recomendaciones | P1 | PASS |
| FE-11 | Reporte PDF | Resultado con y sin Grad-CAM | PDF válido; incluye resultado, triaje, probabilidades y disclaimer | P2 | PASS |
| FE-12 | Panel y detalle | `GET /stats/summary`, `GET /predictions/{id}`, feedback | Carga resumen; detalle; envía feedback | P2 | PASS |
| FE-13 | Estados visuales y widgets | `ResultCard`, `ClinicalSafetyCard`, `AppShell` | Render sin overflow; insignias y botones correctos | P2 | **PEND** |
| FE-14 | Accesibilidad | TalkBack/VoiceOver, texto grande, contraste | Etiquetas semánticas; sin texto truncado; contraste AA | P2 | **PEND** |

**Cobertura:** 42 pruebas en `frontend/test/`:
`prediction_viewmodel_test.dart` (13), `history_viewmodel_test.dart` (4),
`auth_viewmodel_test.dart` (6), `offline_test.dart` (5),
`clinical_safety_test.dart` (9), `report_service_test.dart` (2),
`stats_detail_viewmodel_test.dart` (3).

> **Advertencia observada:** al generar PDF, `flutter test` imprime
> `Helvetica has no Unicode support`. Las pruebas pasan porque validan el PDF,
> pero los acentos podrían no renderizarse en el documento final. Es un
> defecto cosmético S3 que conviene corregir embebiendo una fuente con
> soporte Unicode (p. ej., `Roboto` o `NotoSans`).

### 9.5 Pipeline ML

| ID | Caso | Datos / estímulo | Resultado esperado | Prioridad | Estado |
| --- | --- | --- | --- | --- | --- |
| ML-01 | Etiquetas canónicas | `ml/configs/labels.json` | 4 clases en orden: glioma, meningioma, pituitario, no_tumor | P1 | AUTO |
| ML-02 | Partición reproducible | `prepare.py` sobre dataset sintético | Split 80/20; fingerprint estable; `splits.json` | P1 | AUTO |
| ML-03 | `Testing/` aislado | Ejecutar prepare dos veces | `test` no se usa para seleccionar checkpoint; fingerprint igual | P1 | AUTO |
| ML-04 | Alias de clases | `pituitary` → `pituitario`, `notumor` → `no_tumor` | Mapeo correcto; sin clases desconocidas | P1 | AUTO |
| ML-05 | Dataloader compartido | 5 modelos | Mismos tamaños y orden de clases | P1 | AUTO |
| ML-06 | Backbone congelado y BN en eval | 5 arquitecturas | Solo la cabeza entrena; buffers BN no cambian | P1 | AUTO |
| ML-07 | `run_all` no evalúa checkpoint viejo | Fallo de entrenamiento | No evalúa un `best.pt` previo; falla explícitamente | P1 | AUTO |
| ML-08 | `run_all --skip-eval` no lee reportes viejos | Reportes existentes | No escribe `comparison.json` con datos viejos | P2 | AUTO |
| ML-09 | Reporte de métricas no se sobrescribe sin permiso | `metrics.py` sobre reporte existente | Falla salvo `--overwrite` | P2 | AUTO |
| ML-10 | Métricas | Predicciones ficticias | Accuracy 0.875 en el caso de prueba | P2 | AUTO |
| ML-11 | Capa Grad-CAM por arquitectura | 5 modelos | Resuelve 1 capa válida por modelo | P1 | AUTO |
| ML-12 | Reproducibilidad de entrenamiento | Misma semilla, mismo split | Métricas dentro de tolerancia; `metadata.json` consistente | P1 | **PEND** |
| ML-13 | Paridad ONNX vs PyTorch | Misma imagen en ambos | Etiqueta igual; probabilidades ± tolerancia | P1 | **PEND** |
| ML-14 | Métricas del checkpoint vs reporte | `best.pt` desplegado | `comparison.json` corresponde al checkpoint | P2 | **PEND** |

**Cobertura:** `ml/tests/test_prepare.py` (9),
`test_run_all_safety.py` (3), `test_frozen_batchnorm.py` (1) = **13**.
`smoke_test.py` cubre entorno, etiquetas, prepare, dataloader, forward/backward,
train/val, métricas y Grad-CAM (8 checks; 7 áreas funcionales, porque métricas
y Grad-CAM son dos comprobaciones separadas).

> **Hallazgo:** la corrida de `smoke_test.py` en `backend/.venv` dio **6/7**
> porque `scikit-learn` no está instalado. El fallo en `metrics` añade el check
> `pipeline sintetico` y no llega a ejecutar el check de Grad-CAM; por eso el
> denominador es 7. No es un fallo del pipeline: el entorno ML se instala con
> `ml/requirements-ml.txt`. Para la evidencia final, ejecutar en el entorno
> correcto y adjuntar **8/8**.

### 9.6 Pruebas no funcionales

| ID | Caso | Configuración | Resultado esperado | Prioridad | Estado |
| --- | --- | --- | --- | --- | --- |
| NF-01 | Latencia warm | 1 VU, 60 s, imagen 1.5 MB | p95 < 3 s; 0 errores | P1 | **PEND** |
| NF-02 | Cold start | Reiniciar Render/HF | Primer request < 60 s | P2 | **PEND** |
| NF-03 | Concurrencia | 10 VUs, 5 min | Error < 1 %; sin OOM; p95 < 5 s | P1 | **PEND** |
| NF-04 | Pico | 20 VUs, 1 min | Degradación controlada; sin crash | P2 | **PEND** |
| NF-05 | Imagen límite | 10 MB, 4096×4096 | 201 o 413; sin crash; memoria estable | P2 | **PEND** |
| NF-06 | Fuzzing de archivos | 100 archivos corruptos/aleatorios | 400/422; sin 500; sin excepción no controlada | P1 | **PEND** |
| NF-07 | JWT manipulado | Firma inválida, `alg=none`, expirado | 401; no acepta tokens | P1 | **PEND** |
| NF-08 | Rate limit | 100 requests/min a `/auth/login` y `/predict` | 429 tras el umbral; no afecta a usuarios normales | P2 | **PEND** |
| NF-09 | CORS | Origen permitido y no permitido | Permite solo el dominio configurado | P2 | **PEND** |
| NF-10 | TLS y headers | `curl -I`, SSL Labs | TLS 1.2+; HSTS; `nosniff`; sin `Server` | P2 | **PEND** |
| NF-11 | Accesibilidad | TalkBack/VoiceOver, texto 200 % | Navegación completa; sin truncamiento | P3 | **PEND** |
| NF-12 | Compatibilidad | Android 8+, iOS 13+, 4 navegadores | App funcional; sin crashes | P2 | **PEND** |
| NF-13 | Backup/restore | Simulacro con DB + media | Restaura en < 2 h; `integrity_check=ok`; historial y Grad-CAM OK | P1 | **PEND** |
| NF-14 | Privacidad | SQL/logs/archivos | Sin PHI; solo hash y metadatos | P1 | PASS (API-06) / **PEND** logs |
| NF-15 | Dependencias | `pip-audit`, Trivy, `flutter pub outdated` | Sin críticos/altos; plan de actualización | P2 | **PEND** |
| NF-16 | Carga sostenida | 5 VUs, 30 min | Memoria estable; sin fugas | P2 | **PEND** |

### 9.7 E2E y UAT

| ID | Flujo | Precondición | Resultado esperado | Prioridad | Estado |
| --- | --- | --- | --- | --- | --- |
| E2E-01 | Clasificar en línea | App + API + modelo reales | Imagen → resultado con etiqueta, confianza y Grad-CAM | P1 | **PEND** |
| E2E-02 | Historial y detalle | Al menos una predicción | La entrada aparece; el detalle muestra 4 probabilidades y Grad-CAM | P1 | **PEND** |
| E2E-03 | Caso no concluyente | Imagen ambigua o umbral forzado | Tarjeta “No concluyente” y ruta de derivación | P1 | **PEND** |
| E2E-04 | Offline + sincronización | Modo avión; luego red | Predicción local; historial pendiente; sync al reconectar | P1 | **PEND** |
| E2E-05 | Registro/login | Backend disponible | Cuenta creada; sesión persistida; logout | P1 | **PEND** |
| E2E-06 | Feedback | Predicción existente | Corrección registrada y visible en el detalle | P2 | **PEND** |
| E2E-07 | PDF | Resultado en pantalla | PDF compartido/descargado con resultado y triaje | P2 | **PEND** |
| E2E-08 | Web | Flutter Web + API | Misma funcionalidad que móvil | P2 | **PEND** |
| E2E-09 | Error de red | API caída | Mensaje claro; opción de reintentar; fallback offline | P2 | **PEND** |
| E2E-10 | Reinicio del backend | Predicción + restart | Historial y Grad-CAM persisten (Oracle) o fallan de forma controlada (Render) | P1 | **PEND** |

---

## 10. Matriz de trazabilidad

### 10.1 Objetivos específicos → pruebas

| Objetivo | Evidencia de prueba | Estado |
| --- | --- | --- |
| **OE1** — evaluar arquitecturas CNN | ML-01 a ML-10; `comparison.json`; `smoke_test` | Parcial (13 tests + smoke) |
| **OE2** — seleccionar modelo e interpretabilidad | ML-11, SAFE-01 a SAFE-08, API-02, API-05 | PASS en API/SAFE; ML AUTO |
| **OE3** — integrar en app móvil | API-01 a API-19, AUTH-01 a AUTH-12, FE-01 a FE-14, E2E-01 a E2E-10 | API/FE PASS; E2E PEND |
| **OE4** — validar en test independiente | ML-03, ML-10, ML-14, API-03, API-14, API-17 | Parcial; ML-14 PEND |

### 10.2 Historias de usuario → pruebas

| Historia | Casos | Estado |
| --- | --- | --- |
| US-01 — preparar dataset | ML-02, ML-03, ML-04 | AUTO |
| US-02 — etiquetas únicas | ML-01 | AUTO |
| US-03 — entrenar 5 modelos | ML-05, ML-06, ML-07 | AUTO |
| US-04 — métricas y comparación | ML-08, ML-09, ML-10, ML-14 | AUTO/PEND |
| US-05 — Grad-CAM | ML-11, API-02 | PASS/AUTO |
| US-06 — subir MRI y predecir | API-02 a API-04, E2E-01 | PASS/PEND |
| US-08 — historial | API-05, API-06, FE-06, E2E-02 | PASS/PEND |
| US-09 — privacidad | API-06, NF-14 | PASS/PEND |
| US-10 — elegir imagen | FE-05, FE-13 | PASS/PEND |
| US-11 — ver resultado | FE-01, FE-12, E2E-01 | PASS/PEND |
| US-12 — MVVM | FE-01 a FE-12 | PASS |
| US-13 — navegación | FE-13, E2E-01/02 | PEND |
| US-14 — historial en app | FE-06, E2E-02 | PASS/PEND |
| US-15 — cuenta opcional | AUTH-01 a AUTH-12, FE-07, E2E-05 | PASS/PEND |
| US-16/US-17 — documentación/paper | Revisión documental, no prueba de software | N/A |

### 10.3 Requisitos funcionales → pruebas

| ID | Requisito | Casos |
| --- | --- | --- |
| RF-01 | Clasificar una MRI | API-02, API-03, E2E-01 |
| RF-02 | Devolver 4 probabilidades | API-02, API-03, FE-01 |
| RF-03 | Generar y servir Grad-CAM | API-02, FE-03, E2E-01 |
| RF-04 | Historial persistente | API-05, NF-13, E2E-10 |
| RF-05 | Detalle con probabilidades y feedback | API-13, API-15, FE-12 |
| RF-06 | Feedback humano | API-15, API-16, E2E-06 |
| RF-07 | Catálogos de modelos/clases | API-18 |
| RF-08 | Estadísticas de uso | API-17, FE-12 |
| RF-09 | Registro/login | AUTH-01 a AUTH-09 |
| RF-10 | Refresh/logout | AUTH-11, AUTH-12 |
| RF-11 | Triaje clínico | SAFE-01 a SAFE-08 |
| RF-12 | Offline + sync | FE-08, FE-09, E2E-04 |
| RF-13 | Reporte PDF | FE-11, E2E-07 |
| RF-14 | APK/Web | Workflow Android, E2E-08 |

### 10.4 Requisitos no funcionales → pruebas

| ID | Requisito | Casos |
| --- | --- | --- |
| RNF-01 | Rendimiento warm | NF-01, NF-16 |
| RNF-02 | Cold start | NF-02 |
| RNF-03 | Concurrencia | NF-03, NF-04 |
| RNF-04 | Seguridad | NF-06 a NF-10, NF-15 |
| RNF-05 | Privacidad | API-06, NF-14 |
| RNF-06 | Compatibilidad | NF-12 |
| RNF-07 | Accesibilidad | NF-11 |
| RNF-08 | Respaldo/DR | NF-13 |
| RNF-09 | Observabilidad | Health checks, Sentry, UptimeRobot (operación) |
| RNF-10 | Mantenibilidad | `flutter analyze`, revisión de código |
| RNF-11 | Reproducibilidad | ML-12, ML-13 |
| RNF-12 | Portabilidad | Builds Android/Web; contenedor |

### 10.5 Riesgos → pruebas

| Riesgo | Prueba de mitigación |
| --- | --- |
| Resultado clínico inseguro | SAFE-01 a SAFE-08, E2E-03 |
| Pérdida de historial/Grad-CAM | NF-13, E2E-10 |
| Fuga de credenciales | AUTH-02/03/10, NF-07 |
| Subida maliciosa | API-07 a API-10, NF-06 |
| OOM en Render | NF-03, NF-04, NF-16 |
| Modelo no reproducible | ML-02, ML-03, ML-12 |
| PDF con acentos rotos | FE-11 (mejorar aserción de texto) |
| Cold start percibido como caída | NF-02, E2E-09 |

---

## 11. Ejecución y resultados

### 11.1 Entorno de la corrida

| Elemento | Valor |
| --- | --- |
| Fecha | 13/11/2026 |
| SO | macOS ARM64 |
| Python | 3.12.13 |
| PyTorch | 2.14.1 |
| Flutter | 3.41.6 |
| Dart | ^3.11.4 |
| Backend | FastAPI 0.115.6, SQLAlchemy 2.0.36 |
| DB de pruebas | SQLite temporal (`test.db.sqlite3`) |
| Modelo de pruebas | Checkpoint `shufflenetv2` con pesos aleatorios |
| Modelo real | MobileNetV3 (`ml/models/mobilenetv3/best.pt`) |
| Red | No se ejecutaron pruebas contra Render en esta corrida |

### 11.2 Backend

Comando:

```bash
cd backend
.venv/bin/python -m pytest -q
```

Salida observada:

```text
........................................................                 [100%]
exit=0
```

**Resultado:** **56 pruebas ejecutadas, 56 passed, 0 failed, 0 errors.**
La corrida completa tardó varios minutos porque crea y carga checkpoints de
PyTorch; no es una suite instantánea.

| Archivo | Casos | Resultado |
| --- | ---: | --- |
| `test_auth.py` | 12 | PASS |
| `test_catalog_endpoints.py` | 10 | PASS |
| `test_clinical_safety.py` | 7 | PASS |
| `test_health.py` | 4 | PASS |
| `test_inference_real.py` | 10 (6 funciones + parametrización de 5 arquitecturas) | PASS |
| `test_predict.py` | 13 (12 funciones + 2 límites) | PASS |
| **Total** | **56** | **PASS** |

**Qué cubre:**

- Contrato de `predict` y suma de probabilidades.
- Historial, deduplicación por hash y ausencia de datos identificables.
- Validación de archivos (tipo, vacío, tamaño, dimensiones, campo faltante).
- Autenticación JWT, hash de contraseña, email único y `me`.
- Catálogos, detalle, feedback, estadísticas y OpenAPI.
- Capa de seguridad clínica.
- Inferencia real con checkpoint, Grad-CAM y capas objetivo por arquitectura.

**Qué no cubre:**

- `refresh` y `logout` (AUTH-11/12).
- Rate limiting, CORS real, TLS o cabeceras de seguridad.
- Carga, concurrencia y comportamiento en Render/Oracle.
- Migraciones de esquema (no hay Alembic).
- Recuperación tras reinicio con volumen persistente.

### 11.3 Frontend

Comandos:

```bash
cd frontend
flutter analyze
flutter test
```

Salida observada:

```text
Analyzing frontend...
No issues found! (ran in 39.7s)

00:19 +42: All tests passed!
```

**Resultado:** **42 pruebas, 42 passed; análisis estático sin observaciones.**

| Archivo | Casos | Resultado |
| --- | ---: | --- |
| `prediction_viewmodel_test.dart` | 13 | PASS |
| `history_viewmodel_test.dart` | 4 | PASS |
| `auth_viewmodel_test.dart` | 6 | PASS |
| `offline_test.dart` | 5 | PASS |
| `clinical_safety_test.dart` | 9 | PASS |
| `report_service_test.dart` | 2 | PASS |
| `stats_detail_viewmodel_test.dart` | 3 | PASS |
| **Total** | **42** | **PASS** |

**Advertencia no fatal:** los tests de PDF imprimen
`Helvetica has no Unicode support`. El PDF se genera, pero los acentos pueden
perderse. Añadir una fuente Unicode y una aserción sobre el texto extraído.

### 11.4 ML

Comando ejecutado:

```bash
backend/.venv/bin/python ml/smoke_test.py
```

Salida resumida:

```text
[OK] entorno torch torch=2.14.1 cuda=False gpu=sin GPU (CPU)
[OK] labels.json ['glioma', 'meningioma', 'pituitario', 'no_tumor']
[OK] prepare.py splits + class aliases fingerprint=...
[OK] dataloader x5 identico (38, 10, 16)
[OK] forward+backward x5 batch=2, 1 paso
[OK] train+validation sinteticos val_accuracy=0.250
[FALLO] pipeline sintetico ModuleNotFoundError: No module named 'sklearn'
6/7 comprobaciones OK
```

**Interpretación:** el pipeline llegó hasta `train+validation`; el fallo es de
**entorno**, no de lógica: `scikit-learn` está en `ml/requirements-ml.txt`,
pero no en `backend/.venv`. En el entorno ML correcto debe llegar a **8/8**
(7/7 en la nomenclatura previa).

**Pruebas ML definidas:** 13 (`test_prepare.py` 9,
`test_run_all_safety.py` 3, `test_frozen_batchnorm.py` 1). No se ejecutaron en
esta corrida por la misma razón; se ejecutan con:

```bash
python -m unittest discover -s ml/tests -p "test_*.py" -v
```

### 11.5 Resumen de la corrida

| Suite | Casos | PASS | FAIL | BLOCKED | Tasa |
| --- | ---: | ---: | ---: | ---: | ---: |
| Backend | 56 | 56 | 0 | 0 | 100 % |
| Frontend | 42 | 42 | 0 | 0 | 100 % |
| Análisis Flutter | — | OK | 0 | 0 | — |
| ML unittest | 13 | — | — | 13 | No ejecutada |
| ML smoke (cortado) | 7 | 6 | 1 | 0 | 85.7 % (entorno); completo 8/8 |
| E2E | 10 | 0 | 0 | 10 | 0 % (no implementado) |
| No funcionales | 16 | 1 | 0 | 15 | 6.25 % (solo API-06) |
| **Total automatizado ejecutado** | **98** | **98** | **0** | **0** | **100 %** |

> **Nota:** “98” suma 56 backend + 42 frontend. No incluye ML, E2E ni no
> funcionales, que se reportan aparte para no inflar la métrica.

### 11.6 Evidencia y reproducibilidad

- Los logs completos se pueden adjuntar como artefacto de GitHub Actions.
- Para reproducir: instalar `backend/requirements.txt`, `ml/requirements-ml.txt`
  y Flutter 3.41.6; ejecutar los comandos de la sección 6.3.
- La suite backend usa un checkpoint aleatorio; no requiere los `best.pt`
  reales. Eso es bueno para CI, pero no valida la calidad del modelo.
- La suite frontend usa `MockClient` y `SharedPreferences` simuladas; no
  levanta la app real.
- La corrida no se hizo contra Render; por tanto, no hay evidencia de latencia
  real, cold start ni concurrencia.

### 11.7 Desviaciones y hallazgos

| # | Hallazgo | Impacto | Acción |
| --- | --- | --- | --- |
| H1 | README dice 37 pruebas backend; hay 56 | Documentación desactualizada | Actualizar README |
| H2 | README dice 23 pruebas frontend; hay 42 | Documentación desactualizada | Actualizar README |
| H3 | `smoke_test` 6/7 por `scikit-learn` ausente | Gate ML no reproducible en backend venv | Usar entorno ML o instalar dependencias |
| H4 | `refresh`/`logout` sin pruebas | Riesgo de sesiones | Añadir AUTH-11/12 |
| H5 | Sin cobertura medida | No se puede afirmar % | Configurar `pytest-cov` y `lcov` |
| H6 | Sin E2E | No se valida el flujo completo | Añadir Patrol/integration_test |
| H7 | PDF con Helvetica sin Unicode | Acentos posiblemente rotos | Embeber fuente Unicode y probar texto |
| H8 | Métricas del paper vs checkpoint | Trazabilidad | Re-evaluar `best.pt` con `run_all.py --skip-train` |
| H9 | `ms/imagen` nulo en `comparison.json` | No se puede comparar latencia | Medir en hardware objetivo |
| H10 | Sin pruebas de carga/seguridad | Riesgo para piloto | Ejecutar NF-01 a NF-16 |

---

## 12. Pruebas no funcionales detalladas

### 12.1 Rendimiento y carga

**Objetivo:** verificar que la API mantiene una latencia aceptable y no se cae
con la concurrencia esperada.

**Herramienta:** k6 (recomendado) o Locust.

**Perfil:**

| Escenario | VUs | Duración | Carga |
| --- | ---: | ---: | --- |
| Warm-up | 1 | 60 s | 1 imagen cada 2 s |
| Ramp | 0→10 | 2 min | 1 imagen cada 10 s por VU |
| Estable | 10 | 5 min | Igual |
| Pico | 20 | 1 min | Igual |
| Soak | 5 | 30 min | 1 imagen cada 5 s |

**Umbrales:**

- `http_req_failed < 1 %`.
- `http_req_duration{p95} < 3000 ms` en warm.
- `http_req_duration{p95} < 5000 ms` en pico.
- Sin OOM; memoria estable en soak.
- `model_ready=true` al final.

**Script de referencia:**

```javascript
// tests/load/predict.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';

const BASE = __ENV.API_BASE_URL || 'https://api.example.com/api/v1';
const IMAGE = open('./mri-1.jpg', 'b');

export const options = {
  scenarios: {
    warm: { executor: 'constant-vus', vus: 1, duration: '60s' },
    ramp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 10 },
        { duration: '5m', target: 10 },
        { duration: '1m', target: 20 },
        { duration: '1m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<5000'],
  },
};

export default function () {
  const fd = new FormData();
  fd.append('file', http.file(IMAGE, 'mri.jpg', 'image/jpeg'));
  const res = http.post(`${BASE}/predict`, fd.body(), {
    headers: { 'Content-Type': `multipart/form-data; boundary=${fd.boundary}` },
  });
  check(res, {
    'status 201': (r) => r.status === 201,
    'has label': (r) => !!r.json('label'),
  });
  sleep(2);
}
```

**Registro:** guardar `k6 summary --summary-export=summary.json` y adjuntarlo.

### 12.2 Seguridad

Se usa OWASP ASVS como checklist. No se pretende certificar; se busca detectar
fallos evidentes antes de un piloto.

| Control | Verificación | Estado |
| --- | --- | --- |
| Autenticación | JWT firmado, expiración, `alg` permitido | PASS (AUTH-02/10) |
| Contraseñas | PBKDF2 con sal; no texto claro | PASS (AUTH-03) |
| Sesiones | Refresh rotativo y logout | **PEND** (AUTH-11/12) |
| Autorización | `/auth/me` exige token; feedback opcional | PASS (AUTH-09/10) |
| Validación de entrada | Tipo, tamaño, dimensiones, esquema Pydantic | PASS (API-07..11) |
| Inyección SQL | ORM SQLAlchemy; sin SQL concatenado | Revisión de código |
| XSS | Comentarios de feedback se muestran como texto | Revisión Flutter |
| CSRF | API bearer, no cookies de sesión | N/A |
| CORS | Orígenes explícitos | **PEND** (NF-09) |
| Rate limiting | Login/predict | **PEND** (NF-08) |
| TLS/headers | HTTPS, HSTS, `nosniff` | **PEND** (NF-10) |
| Secretos | `.env`, GitHub Secrets, sin claves en Git | Revisión |
| Dependencias | `pip-audit`, Trivy | **PEND** (NF-15) |
| Contenedor | Non-root, read-only, no-new-privileges | Propuesto |
| Logs | Sin PHI, tokens ni imágenes | **PEND** (NF-14) |
| Errores | Sin stack traces al cliente | Revisión |
| Subida maliciosa | Fuzzing, polyglot, zip bomb | **PEND** (NF-06) |
| Fuerza bruta | Rate limit + bloqueo temporal | **PEND** |

**Pruebas manuales de seguridad mínimas:**

```bash
# 1. Token alterado
curl -H "Authorization: Bearer xxx.yyy.zzz" https://api.example.com/api/v1/auth/me
# Esperado: 401

# 2. CORS no permitido
curl -H "Origin: https://evil.example" -I https://api.example.com/api/v1/health
# Esperado: sin Access-Control-Allow-Origin

# 3. Archivo disfrazado
printf 'no soy una imagen' > fake.png
curl -F "file=@fake.png" https://api.example.com/api/v1/predict
# Esperado: 400

# 4. Rate limit
for i in $(seq 1 120); do curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST https://api.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"x@example.com","password":"bad"}'; done | sort | uniq -c
# Esperado: mayoría 401; aparición de 429 tras el umbral
```

### 12.3 Compatibilidad

| Plataforma | Versión mínima | Verificación | Estado |
| --- | --- | --- | --- |
| Android | 8.0 (API 26) | APK en dispositivo/emulador | PEND |
| iOS | 13.0 | Simulador/dispositivo | PEND |
| Chrome | Última estable | Flutter Web | PEND |
| Edge | Última estable | Flutter Web | PEND |
| Firefox | Última estable | Flutter Web | PEND |
| Safari | Última estable | Flutter Web | PEND |
| Pantallas | 360×640 a tablet | Sin overflow | PEND |
| Orientación | Vertical (principal) | Layout estable | PEND |
| Red | 3G/4G/Wi-Fi/offline | Timeout 60 s; fallback | PEND |

**Prueba mínima:** instalar el APK en un dispositivo físico limpio, sin la app
previa, y ejecutar E2E-01, E2E-04 y E2E-05.

### 12.4 Accesibilidad

| Criterio | Verificación | Estado |
| --- | --- | --- |
| Contraste | Texto normal ≥ 4.5:1; grande ≥ 3:1 | PEND |
| Semántica | `Semantics`/labels en botones e imágenes | PEND |
| Tamaño de texto | Escalado 200 % sin truncar | PEND |
| Navegación | TalkBack/VoiceOver recorre todo | PEND |
| Colores de triaje | No depender solo del color; incluir texto | PASS por diseño |
| Disclaimer | Visible y legible | PASS |
| Errores | Mensajes claros, no solo códigos | PASS |

### 12.5 Confiabilidad y offline

| Escenario | Acción | Resultado esperado |
| --- | --- | --- |
| Sin red al predecir | Modo avión | Predicción ONNX + banner “Sin conexión” |
| Vuelve la red | Desactivar modo avión | Sync de pendientes; sin duplicados |
| API 500 | Forzar error | Mensaje claro; reintento; no crash |
| API lenta | Latencia > 60 s | Timeout controlado; ofrecer offline |
| Doble tap en “Clasificar” | Taps rápidos | Una sola petición/estado loading |
| Cerrar app en loading | Matar proceso | No corrupción; estado consistente |
| DB local llena | Muchos pendientes | Error controlado; no crash |
| Imagen borrada | Archivo temporal eliminado | Mensaje; no crash |

### 12.6 Privacidad

**Consultas de verificación:**

```sql
-- No debe haber columnas con nombres de pacientes
SELECT name FROM sqlite_master WHERE type='table';
SELECT * FROM images LIMIT 5;
SELECT * FROM predictions LIMIT 5;
SELECT * FROM prediction_feedback LIMIT 5;

-- El hash debe ser SHA-256 (64 hex)
SELECT length(image_hash), COUNT(*) FROM images GROUP BY length(image_hash);
```

**Logs:**

```bash
docker compose logs api | grep -Ei "paciente|nombre|dicom|token|authorization" || echo "OK"
```

**Criterio:** no debe aparecer ningún nombre, DICOM, token ni ruta con datos
personales. El único identificador es el hash.

### 12.7 Respaldo y recuperación

**Simulacro:**

1. Crear una predicción y un feedback.
2. Ejecutar el backup.
3. Borrar la DB y `media/` en un entorno de prueba.
4. Restaurar.
5. Verificar `PRAGMA integrity_check`, historial, detalle y Grad-CAM.
6. Medir tiempo total.

**Criterios:** RPO ≤ 24 h; RTO ≤ 2 h; sin pérdida de filas; Grad-CAM
recuperado. Documentar el resultado y las diferencias.

### 12.8 Puertas de calidad en CI

| Etapa | Comando | Bloquea |
| --- | --- | --- |
| Backend tests | `pytest -q` | Sí |
| Cobertura | `pytest --cov=app --cov-fail-under=80` | Sí (cuando se configure) |
| Frontend analyze | `flutter analyze` | Sí |
| Frontend tests | `flutter test` | Sí |
| ML smoke | `python ml/smoke_test.py` | Sí (en job ML) |
| Build ARM64 | `docker buildx build --platform linux/arm64` | Sí |
| Seguridad | `pip-audit`, Trivy | No al inicio; reportar |
| Deploy smoke | `curl /health` | Sí |

---

## 13. Pruebas de modelo y validación ML

### 13.1 Protocolo

- Dataset: Brain Tumor MRI Dataset (Kaggle, Nickparvar), 5.600 imágenes de
  entrenamiento + 1.600 de test.
- Solo `Training/` se divide 80/20 con semilla 42; `Testing/` se conserva
  intacto.
- Preprocesamiento: 224×224, RGB, normalización ImageNet.
- Transfer learning con backbone congelado; solo la cabeza de 4 clases.
- Optimizador Adam, `lr=1e-3`, batch 64, hasta 100 épocas.
- Selección por accuracy de validación; test no participa.
- Métricas: accuracy, macro F1, recall tumoral, ROC-AUC OVR, matriz de
  confusión, parámetros y ms/imagen.

### 13.2 Resultados de referencia

| Modelo | Params (M) | Tamaño (MB) | Accuracy | Macro F1 | Recall tumoral | ROC-AUC | Apto móvil |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| DenseNet121 | 7.98 | 27.12 | **87.56 %** | **87.41 %** | **84.00 %** | 0.9677 | Media |
| MobileNetV3 | 5.48 | 16.25 | 87.19 % | 86.97 % | 83.08 % | 0.9710 | **Alta** |
| EfficientNetB0 | 5.29 | 15.59 | 87.06 % | 86.73 % | 82.75 % | **0.9711** | Alta |
| ResNet18 | 11.69 | 42.72 | 85.69 % | 85.37 % | 81.42 % | 0.9644 | Baja |
| ShuffleNetV2 | 2.28 | 4.96 | 82.56 % | 82.15 % | 77.08 % | 0.9539 | **Alta** |

**Modelo desplegado:** MobileNetV3 por equilibrio exactitud/tamaño. DenseNet121
tiene la mejor accuracy, pero pesa 27 MB y es menos apto para móvil; ShuffleNetV2
es el más liviano, pero pierde ~4.6 puntos de accuracy.

### 13.3 Criterios de aceptación del modelo

| Criterio | Umbral | Estado |
| --- | --- | --- |
| Accuracy en test | ≥ 85 % | PASS (87.19 % MobileNetV3) |
| Macro F1 | ≥ 85 % | PASS (86.97 %) |
| Recall tumoral | ≥ 80 % | PASS (83.08 %) |
| ROC-AUC OVR | ≥ 0.95 | PASS (0.9710) |
| Sin fuga train/test | 0 imágenes compartidas | PASS por diseño (fingerprint) |
| Partición reproducible | Mismo fingerprint | PASS (seed 42) |
| Grad-CAM en 5 modelos | 1 capa válida por modelo | PASS |
| Inferencia determinista | Misma imagen → misma salida | PASS |
| Paridad ONNX/PyTorch | Etiqueta igual | **PEND** |
| Validación externa | Otro hospital/dataset | **PEND** (fuera de alcance) |

### 13.4 Pruebas de calibración y triaje

- **Calibración:** el triaje usa confianza y margen, no probabilidades
  calibradas. Medir ECE (Expected Calibration Error) y reliability diagram es
  trabajo futuro; hoy no se afirma que la confianza esté calibrada.
- **Umbrales:** 0.70 de confianza, 0.10 de margen, 0.90 para riesgo alto. Se
  probaron en backend y frontend (SAFE-01..08).
- **Sesgo por clase:** glioma es la clase más difícil (recall 84 % en
  DenseNet121, 83.08 % en MobileNetV3). Un falso negativo de glioma es el error
  más costoso; el triaje no lo detecta si la confianza es alta pero la
  predicción es incorrecta.
- **Limitación:** no hay estudio con radiólogos ni validación externa; no se
  puede afirmar sensibilidad clínica.

### 13.5 Grad-CAM: qué verificar

1. El mapa se genera en la capa correcta por arquitectura.
2. El tamaño es 224×224 y el archivo es PNG válido.
3. El mapa se superpone a la imagen original.
4. La clase objetivo corresponde a la predicción.
5. No hay mapas en blanco o ruido constante para todas las imágenes.
6. Un radiólogo (si participa) revisa que las regiones sean anatómicamente
   plausibles; esto es validación cualitativa, no una prueba automática.
7. Si Grad-CAM falla, la predicción no falla (degradación elegante).

### 13.6 Model card mínima

| Campo | Contenido |
| --- | --- |
| Nombre | MobileNetV3 brain tumor classifier |
| Versión | `mobilenetv3-v1` |
| Entrada | MRI 224×224 RGB |
| Clases | glioma, meningioma, pituitario, no_tumor |
| Entrenamiento | 5.600 imágenes; split 80/20; semilla 42 |
| Test | 1.600 imágenes |
| Métricas | Accuracy 87.19 %, macro F1 86.97 %, recall tumoral 83.08 %, ROC-AUC 0.9710 |
| Uso previsto | Apoyo académico, no diagnóstico |
| Limitaciones | Dataset único, sin validación externa, sin calibración, sin lectura de radiólogo |
| Privacidad | Solo hash de imagen; sin PHI |
| Riesgo | Falsos negativos/positivos; triaje mitiga ambigüedad, no elimina error |

---

## 14. Pruebas de aceptación de usuario (UAT)

### 14.1 UAT-01 — Clasificación en línea

**Precondición:** app instalada, backend con modelo real, red disponible.

1. Abrir la app.
2. Tocar “Elegir de la galería” y seleccionar una MRI.
3. Verificar la vista previa.
4. Tocar “Clasificar”.
5. Esperar el resultado.

**Esperado:** indicador de carga; resultado con etiqueta, confianza,
probabilidades, Grad-CAM y aviso médico; sin error. Si la confianza es baja,
aparece “No concluyente” y la ruta de derivación.

### 14.2 UAT-02 — Caso no concluyente

**Precondición:** imagen ambigua o umbral forzado en un entorno de prueba.

1. Clasificar la imagen.
2. Revisar la tarjeta de seguridad clínica.

**Esperado:** insignia “No concluyente”; recomendación de repetir/consultar;
botón “Ver ruta de derivación”; no se muestra un diagnóstico forzado.

### 14.3 UAT-03 — Offline y sincronización

1. Activar modo avión.
2. Clasificar una imagen.
3. Verificar el banner “Sin conexión · modelo local ONNX”.
4. Abrir el historial: la predicción aparece como “Pendiente de sincronizar”.
5. Desactivar modo avión.
6. Esperar la sincronización.

**Esperado:** inferencia local con el mismo triaje; historial local; al
reconectar, el pendiente se envía y se convierte en registro del backend.

### 14.4 UAT-04 — Historial y detalle

1. Abrir “Historial”.
2. Verificar la lista (etiqueta, confianza, modelo, fecha).
3. Tocar una entrada.
4. Revisar el detalle: 4 probabilidades, Grad-CAM y feedback.

**Esperado:** datos consistentes con la predicción; sin 404; pull-to-refresh
funciona; estado vacío y error son claros.

### 14.5 UAT-05 — Registro, login y logout

1. Ir a “Cuenta”.
2. Registrarse con nombre, email y contraseña.
3. Cerrar sesión.
4. Iniciar sesión con las mismas credenciales.
5. Cerrar y reabrir la app.

**Esperado:** sesión persistida; logout limpia; error claro con credenciales
incorrectas; no se muestran tokens.

### 14.6 UAT-06 — Feedback humano

1. Abrir el detalle de una predicción.
2. Marcar “Correcto” o corregir la clase.
3. Enviar.

**Esperado:** confirmación; el feedback aparece en el detalle; la clase
corregida se refleja; no se permite una etiqueta inválida.

### 14.7 UAT-07 — Reporte PDF

1. Clasificar una imagen.
2. Tocar “Exportar reporte PDF”.
3. Guardar/compartir.

**Esperado:** PDF con encabezado, resultado, triaje, recomendación, tabla de
probabilidades, Grad-CAM (si está), trazabilidad y disclaimer. Revisar que los
acentos se vean bien.

### 14.8 UAT-08 — Manejo de errores

1. Detener el backend o activar modo avión sin ONNX.
2. Intentar clasificar.
3. Revisar el mensaje.

**Esperado:** mensaje en español, no un stack trace; opción de reintentar o
usar offline; la app no se cierra.

### 14.9 UAT-09 — Accesibilidad

1. Activar TalkBack/VoiceOver.
2. Recorrer Analizar, Historial, Panel, Info y Cuenta.
3. Aumentar el tamaño de texto al 200 %.

**Esperado:** todos los controles tienen etiqueta; no hay texto truncado;
el flujo principal se completa.

### 14.10 UAT-10 — Web

1. Abrir Flutter Web en Chrome.
2. Elegir una imagen y clasificar.
3. Revisar historial y PDF.

**Esperado:** misma funcionalidad que móvil; CORS configurado; sin errores de
consola; descarga de PDF funciona.

### 14.11 Firma de aceptación

| UAT | Ejecutado por | Fecha | Resultado | Observaciones |
| --- | --- | --- | --- | --- |
| UAT-01 | | | | |
| UAT-02 | | | | |
| UAT-03 | | | | |
| UAT-04 | | | | |
| UAT-05 | | | | |
| UAT-06 | | | | |
| UAT-07 | | | | |
| UAT-08 | | | | |
| UAT-09 | | | | |
| UAT-10 | | | | |

**Aprobación:** ____________________ (PO/docente) — Fecha: __________

---

## 15. Criterios de salida y release gate

### 15.1 Release gate

Una versión se publica solo si:

- [ ] `pytest` 56/56 (o más) en verde.
- [ ] `flutter analyze` sin issues.
- [ ] `flutter test` 42/42 (o más) en verde.
- [ ] `smoke_test` 8/8 en el entorno ML (7/7 en la nomenclatura previa).
- [ ] 0 defectos S1/S2 abiertos.
- [ ] Cobertura backend ≥ 80 % y frontend ≥ 70 % (o excepción aprobada).
- [ ] E2E-01, E2E-02, E2E-04 y E2E-05 ejecutados.
- [ ] NF-01, NF-03, NF-06, NF-07, NF-13 y NF-14 ejecutados.
- [ ] Sin hallazgos críticos/altos de seguridad.
- [ ] Backup y restore probados en staging.
- [ ] APK instalado en dispositivo limpio.
- [ ] `API_BASE_URL` correcta y `/health` en verde.
- [ ] Documentación y changelog actualizados.
- [ ] UAT firmada.

### 15.2 Mapeo con la Definition of Done

| DoD | Evidencia |
| --- | --- |
| Implementado y mergeado | PR + CI |
| Sin TODO funcional | Revisión |
| Documentado | `docs/` actualizado |
| Backend `pytest` | 56/56 |
| Frontend `analyze` + `test` | 0 issues + 42/42 |
| ML `smoke_test` | 8/8 en entorno ML (7/7 previo) |
| Prueba automatizada cuando aporta | 98 pruebas |
| Clases desde `labels.json` | ML-01, API-18 |
| Sin datos identificables | API-06, NF-14 |
| URL solo en `ApiService`/`AppConfig` | Revisión FE |
| Vista sin HTTP/JSON/archivos | Revisión MVVM |
| Estado en ViewModel | FE-05..FE-12 |
| Red sustituible por fake | FE-03/04 |
| Experimento reproducible | ML-02, ML-12 |
| Resultados en `reports/` | `comparison.json` |
| Desviaciones documentadas | `notas-correccion-paper.md` |

### 15.3 Excepciones

Si no se cumple un criterio, el PO debe aprobar una excepción documentada con:

- Criterio no cumplido.
- Riesgo aceptado.
- Mitigación temporal.
- Fecha de corrección.
- Responsable.

No se aceptan excepciones para S1/S2 de seguridad o pérdida de datos.

---

## 16. Métricas y reportes

### 16.1 Fórmulas

| Métrica | Fórmula | Meta |
| --- | --- | --- |
| Tasa de éxito | `passed / (passed + failed)` | ≥ 95 % |
| Progreso de ejecución | `executed / total` | 100 % P1/P2 |
| Densidad de defectos | `defects / 100 casos` | ≤ 5 |
| Eficiencia de eliminación | `defectos pre-release / total` | ≥ 90 % |
| Defectos escapados | `defectos post-release / total` | ≤ 5 % |
| Cobertura de líneas | `líneas cubiertas / total` | ≥ 80 % BE / 70 % FE |
| Cobertura de rutas críticas | `rutas cubiertas / rutas críticas` | 100 % |
| Flakiness | `reruns / total ejecuciones` | ≤ 2 % |
| MTTR | `tiempo medio de reparación` | < 1 día (S1/S2) |
| Cumplimiento SLO | `minutos disponibles / minutos totales` | ≥ 99.0 % |

### 16.2 Línea base actual

| Métrica | Valor |
| --- | --- |
| Casos automatizados ejecutados | 98 (56 BE + 42 FE) |
| Tasa de éxito | 100 % |
| Defectos S1/S2 abiertos | 0 |
| Cobertura | No medida |
| E2E | 0 |
| No funcionales | 1 de 16 (privacidad API) |
| Flakiness observada | 0 en esta corrida |
| Tiempo backend | Varios minutos (checkpoints) |
| Tiempo frontend | ~19 s |

### 16.3 Reporte semanal (plantilla)

```markdown
## Reporte de calidad — semana <n>

- **Commit/tag:**
- **Rondas ejecutadas:**
- **Casos:** <passed>/<total> (<%>)
- **Defectos nuevos:** S1: __ S2: __ S3: __ S4: __
- **Defectos cerrados:**
- **Bloqueos:**
- **Cobertura:** BE __ % / FE __ %
- **Riesgos:**
- **Próxima acción:**
```

### 16.4 Dashboard mínimo

- Estado del CI (verde/rojo).
- Última ejecución de la suite y duración.
- Defectos abiertos por severidad.
- Cobertura por capa.
- Uptime y latencia p95.
- Errores nuevos en Sentry.

---

## 17. Riesgos de las pruebas

| # | Riesgo | P | I | Mitigación |
| --- | --- | --- | --- | --- |
| R1 | Entorno distinto a producción (macOS vs Linux/Render) | A | M | Ejecutar smoke en staging; contenedor |
| R2 | Suite backend lenta por PyTorch | M | M | Checkpoint pequeño; marcar tests lentos; CI paralelo |
| R3 | Falsos positivos por checkpoint aleatorio | M | B | No evalúa calidad; solo contrato |
| R4 | Datos de test no representativos | M | A | Usar test split real para métricas; UAT con MRI variadas |
| R5 | Sin E2E | A | A | Añadir Patrol/integration_test |
| R6 | Sin cobertura | A | M | `pytest-cov` + `lcov` |
| R7 | Dependencia de Render | M | M | Plan B Oracle; smoke local |
| R8 | Modelo no determinista en GPU | B | M | CPU para pruebas; semilla; tolerancia |
| R9 | Falta de tiempo antes de la entrega | A | A | Priorizar P1/P2; automatizar lo crítico |
| R10 | Sesgo clínico no detectado | M | C | Validación externa; no uso clínico |
| R11 | Pruebas de seguridad incompletas | A | A | ZAP + ASVS + revisión |
| R12 | Documentación desactualizada | A | M | Actualizar README y este doc |

> **P** = probabilidad; **I** = impacto. **A** = alta, **M** = media, **B** = baja, **C** = crítica.

---

## 18. Conclusiones y recomendaciones

1. **La calidad del software es buena para una demo académica.** 98 pruebas
   automatizadas en verde, análisis estático limpio y una separación MVVM
   verificable.
2. **La API tiene cobertura de contrato y de seguridad clínica.** Las 56
   pruebas backend cubren el flujo principal, validación, auth y triaje.
3. **El frontend tiene buena cobertura de lógica.** Las 42 pruebas cubren DTOs,
   servicios, ViewModels, offline, PDF y triaje.
4. **El eslabón más débil es E2E.** No hay una prueba automatizada que abra la
   app y recorra el flujo completo; la UAT manual es indispensable.
5. **La cobertura no se mide.** Sin `pytest-cov`/`lcov`, no se puede afirmar un
   porcentaje ni comparar releases.
6. **El gate de ML debe ejecutarse en su entorno.** `smoke_test` 6/7 en
   `backend/.venv` es un problema de dependencias, no del pipeline; en el
   entorno ML completo se espera 8/8. Hay que usar `ml/requirements-ml.txt`.
7. **Hay un hueco en auth:** `refresh` y `logout` están implementados pero no
   probados. Es prioritario antes de un piloto.
8. **El PDF tiene un defecto cosmético:** Helvetica no soporta Unicode; los
   acentos pueden perderse. Embeber una fuente y probar el texto.
9. **Las pruebas no funcionales están pendientes.** Sin carga, seguridad,
   accesibilidad y restore, no se puede afirmar que el sistema soporte un
   piloto real.
10. **La validación clínica sigue siendo el límite.** Ninguna prueba de
    software sustituye un estudio con radiólogos y una validación externa.

### 18.1 Plan de mejora (30/60/90 días)

**30 días:**

- Añadir AUTH-11/12.
- Configurar cobertura y publicar el número.
- Corregir el PDF Unicode.
- Añadir un E2E mínimo.
- Actualizar README (56/42, no 37/23).

**60 días:**

- Ejecutar NF-01, NF-03, NF-06, NF-07, NF-13, NF-14.
- Añadir k6 y ZAP al pipeline.
- Probar APK en dispositivo limpio y Web en 4 navegadores.
- Hacer un simulacro de restore.

**90 días:**

- Validación externa del modelo (otro dataset/hospital).
- Estudio de calibración y revisión de Grad-CAM con radiólogo.
- Comité de ética si se usará con pacientes.
- Plan de migración a Oracle y monitoreo continuo.

---

## 19. Referencias

### 19.1 Normas y guías

1. ISO/IEC 25010:2011. *Systems and software engineering — Systems and
   software Quality Requirements and Evaluation (SQuaRE) — System and software
   quality models.*
2. ISO/IEC/IEEE 29119-1:2022. *Software and systems engineering — Software
   testing — Part 1: General concepts.*
3. ISTQB. *Foundation Level Syllabus.*
4. OWASP. *Application Security Verification Standard (ASVS).*
   https://owasp.org/www-project-application-security-verification-standard/
5. OWASP. *Top 10.* https://owasp.org/www-project-top-ten/
6. NIST. *SP 800-190: Application Container Security Guide.* 2017.
7. Google. *Site Reliability Engineering.* O'Reilly, 2016.
8. IEEE 829-2008. *Standard for Software and System Test Documentation*
   (referencia histórica).

### 19.2 Documentación del proyecto

9. `README.md`.
10. `docs/informe-universitario.md`.
11. `docs/mejora-capa-seguridad-clinica.md`.
12. `docs/diseno-pantallas.md`.
13. `docs/scrum/definition-of-done.md`.
14. `docs/scrum/product-backlog.md`.
15. `docs/scrum/sprints.md`.
16. `docs/arquitectura-cloud.md`.
17. `ml/evaluation/reports/comparison.json`.
18. `backend/tests/`, `frontend/test/`, `ml/tests/`.

### 19.3 Herramientas

19. pytest. https://docs.pytest.org/
20. Flutter testing. https://docs.flutter.dev/testing
21. k6. https://k6.io/docs/
22. OWASP ZAP. https://www.zaproxy.org/
23. Trivy. https://trivy.dev/
24. pip-audit. https://pypi.org/project/pip-audit/
25. Patrol. https://patrol.leancode.co/

---

## 20. Anexos

### Anexo A — Comandos de ejecución

```bash
# 1. Backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q

# 2. Frontend
cd frontend
flutter pub get
flutter analyze
flutter test

# 3. ML
python3.12 -m venv .venv-ml && source .venv-ml/bin/activate
pip install -r ml/requirements-ml.txt
# Instalar torch/torchvision según la variante CPU/CUDA (ver docs/ml-training-handoff.md)
python ml/smoke_test.py
python -m unittest discover -s ml/tests -p "test_*.py" -v

# 4. API manual
cd backend
uvicorn app.main:app --reload
curl -s http://localhost:8000/api/v1/health | jq .
curl -s -F "file=@mri.png" http://localhost:8000/api/v1/predict | jq .

# 5. Carga
k6 run tests/load/predict.js

# 6. Cobertura
cd backend && pytest --cov=app --cov-report=term-missing
cd frontend && flutter test --coverage && genhtml coverage/lcov.info -o coverage/html
```

### Anexo B — Plantilla de evidencia

```markdown
## Evidencia — <suite> — <fecha>

- **Commit/tag:**
- **Entorno:**
- **Comando:**
- **Resultado:** <passed>/<total>
- **Duración:**
- **Fallos:**
- **Log:** <ruta o artifact>
- **Observaciones:**
```

### Anexo C — Checklist de seguridad rápida

- [ ] `JWT_SECRET` fuerte y distinto de dev.
- [ ] HTTPS y HSTS.
- [ ] CORS explícito.
- [ ] Rate limit en auth/predict.
- [ ] Validación de archivo y límite 10 MB.
- [ ] Contenedor no-root/read-only.
- [ ] Firewall 80/443; SSH restringido.
- [ ] Backups cifrados y restore probado.
- [ ] `pip-audit`/Trivy sin críticos.
- [ ] Logs sin PHI/tokens.
- [ ] Alertas de salud/errores/disco.
- [ ] Plan de incidentes.

### Anexo D — Consultas de privacidad

```sql
-- Conteo de tablas
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Verificar que solo hay hash y metadatos técnicos
PRAGMA table_info(images);
PRAGMA table_info(predictions);
PRAGMA table_info(prediction_feedback);

-- Verificar longitud del hash
SELECT length(image_hash) AS len, COUNT(*) FROM images GROUP BY len;

-- Buscar posibles fugas de nombres en campos de texto
SELECT id, source FROM predictions WHERE source LIKE '%paciente%';
SELECT id, comment FROM prediction_feedback WHERE comment LIKE '%paciente%';
```

### Anexo E — Glosario

| Término | Definición |
| --- | --- |
| **API** | Interfaz de programación de aplicaciones |
| **Contrato** | Forma y tipos de request/response |
| **E2E** | Prueba de extremo a extremo |
| **Fixture** | Datos/objeto preparado para una prueba |
| **Flaky test** | Prueba que pasa y falla sin cambios |
| **Grad-CAM** | Mapa de calor de la región que influye en la predicción |
| **JWT** | Token JSON firmado |
| **MVVM** | Model–View–ViewModel |
| **PHI** | Información de salud protegida/identificable |
| **Pirámide** | Proporción de pruebas unitarias/integración/E2E |
| **SLO/SLI** | Objetivo/indicador de nivel de servicio |
| **Smoke test** | Prueba mínima de humo |
| **UAT** | Prueba de aceptación de usuario |
| **ViewModel** | Estado y reglas que observa la vista |

---

**Fin del documento.**


