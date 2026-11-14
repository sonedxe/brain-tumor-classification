# Arquitectura cloud propuesta y evaluación de SaaS con capa gratuita

**Proyecto:** Clasificación de tumores cerebrales en imágenes de resonancia magnética (MRI) mediante CNN ligeras, Grad-CAM y una aplicación móvil Flutter con arquitectura MVVM.

**Documento:** Propuesta de arquitectura cloud, dimensionamiento, seguridad, operación y plan de migración.

| Campo | Valor |
| --- | --- |
| Versión | 1.0 |
| Fecha | 13 de noviembre de 2026 |
| Estado | Propuesta para revisión académica |
| Autor | *(completar nombre y código)* |
| Curso | Taller de Desarrollo de Proyectos de Software *(ajustar)* |
| Universidad | Universidad Nacional Mayor de San Marcos |
| Repositorio | `sonedxe/brain-tumor-classification` |
| Vigencia de precios y capas gratuitas | Verificada el 13/11/2026. Los planes cambian; revisar las fuentes de la sección 16 antes de contratar. |

> **Aviso de uso responsable.** Esta arquitectura corresponde a una herramienta
> académica de apoyo. **No constituye un dispositivo médico ni sustituye el
> criterio de un radiólogo.** El sistema no debe usarse con pacientes reales sin
> validación clínica, comité de ética y el registro regulatorio que corresponda.

---

## 1. Resumen ejecutivo

El proyecto ya funciona de extremo a extremo: una app Flutter (MVVM) consume una
API FastAPI que ejecuta inferencia real con PyTorch, genera Grad-CAM, persiste
un historial en SQLite y expone autenticación JWT, feedback humano y
estadísticas. El despliegue actual usa el plan gratuito de **Render** y publica
el APK mediante **GitHub Releases**. Esa combinación es suficiente para una
demostración, pero tiene dos problemas estructurales:

1. **El disco de Render Free es efímero.** SQLite y las imágenes Grad-CAM se
   pierden en cada reinicio, redeploy o *spin-down* por inactividad. El
   historial y los enlaces `/static/gradcam/...` dejan de ser confiables.
2. **512 MB de RAM y 0.1 CPU están al límite.** La medición local de este
   proyecto, con MobileNetV3 y Grad-CAM, dio un pico aproximado de **342 MB**
   de RSS antes de sumar el proceso FastAPI completo y el sistema operativo.
   Con concurrencia o un modelo más grande, el riesgo de OOM es real.

La arquitectura recomendada para mantener **costo $0** y calidad suficiente es:

> **Una VM Ampere A1 de Oracle Cloud Always Free** (2 OCPU, 3–4 GB de RAM,
> volumen de bloque persistente) con Docker Compose, Caddy como reverse proxy
> con TLS, SQLite en el volumen persistente, respaldos cifrados hacia Oracle
> Object Storage o Cloudflare R2, CI/CD con GitHub Actions, APK en GitHub
> Releases y Flutter Web en Cloudflare Pages. Cloudflare aporta DNS, caché y
> una primera capa de protección; UptimeRobot, Sentry y Grafana Cloud cubren la
> observabilidad dentro de sus capas gratuitas.

Esta opción conserva **persistencia real**, permite ejecutar PyTorch con
holgura, no tiene *cold starts* de 20–60 segundos y sigue costando $0 dentro de
los límites de Always Free. El costo principal es operativo: hay que
aprovisionar, parchear, respaldar y monitorear una VM. Para un equipo académico
es un costo manejable si se automatiza con Docker Compose y un *runbook*.

La segunda opción, de **mínimo esfuerzo**, es mantener Render Free y mover la
persistencia a **Neon Postgres** y **Cloudflare R2**. Es válida para una demo,
pero no elimina el límite de 512 MB ni el *spin-down*; además obliga a adaptar
SQLite a Postgres y a añadir almacenamiento de objetos. La tercera opción,
**Modal Starter** ($30 USD/mes de crédito gratuito), es atractiva si se acepta
un proveedor serverless y se externaliza el estado. **Hugging Face Spaces ya no
es una capa gratuita para Docker Spaces nuevos**: desde 2026, crear un Space
con cómputo requiere plan PRO o superior.

### 1.1 Decisión recomendada

| Decisión | Elección | Motivo |
| --- | --- | --- |
| Cómputo del backend | Oracle Cloud Always Free, VM A1 (ARM64) | 2 OCPU / 12 GB disponibles; persistencia y costo $0 |
| Tamaño propuesto | 2 OCPU / 3–4 GB / 150 GB de disco | Holgura para PyTorch, Grad-CAM y sistema; evita la recuperación por inactividad |
| Contenedores | Docker Compose: `api` + `caddy` | Simple, reproducible, sin orquestador |
| Base de datos | SQLite en volumen persistente (WAL) | Suficiente para 1 instancia y el volumen actual |
| Imágenes Grad-CAM | Volumen persistente + respaldo a objeto | Evita 404 en el historial |
| Backend de respaldo | Render Free + Neon + R2 | Continuidad inmediata mientras se migra |
| Frontend móvil | GitHub Releases (APK) | Ya implementado y probado |
| Frontend web | Cloudflare Pages | CDN gratuita, 500 builds/mes, requests ilimitados |
| CI/CD | GitHub Actions → GHCR → SSH a la VM | Automatiza pruebas, imagen y despliegue |
| Observabilidad | UptimeRobot + Sentry + Grafana Cloud | Capas gratuitas suficientes para un piloto |
| Costo mensual | **$0** dentro de límites | Con disparadores claros de upgrade |

### 1.2 Advertencia sobre las capas gratuitas

Las capas gratuitas de 2026 no son las de 2024. Durante la investigación se
confirmaron cambios relevantes:

- **Koyeb**, según anuncios de febrero de 2026, dejó de ofrecer el plan Starter
  gratuito a cuentas nuevas; las organizaciones existentes conservan su
  instancia de 512 MB/0.1 vCPU. Conviene verificar el estado al crear la cuenta.
- **Hugging Face Spaces** mantiene CPU Basic sin costo por hora, pero crear
  Gradio o Docker Spaces requiere plan de pago (PRO para cuentas personales).
  Los Spaces gratuitos existentes siguen funcionando y se duermen a las 48 h.
- **Render Postgres Free** expira a los 30 días y no tiene respaldos.
- **Oracle Cloud** redujo la cuota Always Free de A1 a 1.500 OCPU-horas y 9.000
  GB-horas al mes, equivalentes a 2 OCPU y 12 GB; además puede reclamar
  instancias ociosas.
- **Railway** ya no ofrece una capa gratuita amplia: su plan Free da $1 USD/mes
  de crédito y 0.5 GB por servicio; el plan Hobby cuesta $5 USD/mes.
- **GitHub Actions** sigue siendo gratuito para repositorios públicos; en
  privados, GitHub Free incluye $12 USD/mes de cómputo.

Por eso este documento no se limita a listar proveedores: evalúa cuáles son
viables **hoy** para una carga de PyTorch y explica qué se pierde con cada uno.

---

## 2. Contexto y alcance

### 2.1 El sistema existente

El repositorio contiene tres capas:

| Capa | Tecnología | Función |
| --- | --- | --- |
| `ml/` | PyTorch + torchvision | Dataset, entrenamiento comparativo de cinco CNN, evaluación, Grad-CAM y exportación ONNX |
| `backend/` | FastAPI + SQLAlchemy + SQLite | API REST, inferencia real, Grad-CAM, historial, autenticación JWT, feedback y estadísticas |
| `frontend/` | Flutter + MVVM + ONNX Runtime | App Android/iOS/Web, captura de imagen, resultado, historial, panel, cuenta y modo offline |

El modelo activo es **MobileNetV3** (`mobilenetv3-v1`), con 5,483 M parámetros,
un checkpoint de 16.245 MB y métricas de test de 87.19 % de exactitud, 86.97 %
de macro F1, 83.08 % de *recall* tumoral y 0.9710 de ROC-AUC multiclase. El
backend carga `ml/models/mobilenetv3/best.pt` y genera Grad-CAM con *hooks* de
PyTorch, sin depender de OpenCV ni de `pytorch-grad-cam`.

### 2.2 Alcance de esta propuesta

**Incluye:**

- Arquitectura de despliegue para el backend de inferencia y su persistencia.
- Evaluación de proveedores cloud y SaaS con capa gratuita vigente.
- Dimensionamiento, disponibilidad, respaldo, seguridad y observabilidad.
- CI/CD, entornos y plan de migración desde Render.
- Costos, riesgos y criterios de escalamiento.

**No incluye:**

- Reentrenamiento de modelos ni cambios al pipeline de ML.
- Validación clínica, estudio con radiólogos o certificación como dispositivo
  médico.
- Una plataforma multirregión o de alta disponibilidad; el alcance es un
  piloto académico con una sola región.
- Compra de dominio, firma de APK para Google Play o publicación en App Store.

### 2.3 Supuestos de carga

| Variable | Supuesto base | Escenario de pico |
| --- | --- | --- |
| Usuarios activos | 20–50 por día | 200 en una demostración |
| Predicciones | 100/día (~3.000/mes) | 1.000/día (~30.000/mes) |
| Tamaño de imagen | 1–3 MB (máx. 10 MB) | 5 MB promedio |
| Respuesta JSON | < 5 KB | < 5 KB |
| Grad-CAM | 100–200 KB por predicción | 200 KB |
| Retención de historial | 12 meses | 12 meses |
| Retención de Grad-CAM | 90 días | 90 días |
| Latencia objetivo (warm) | p95 < 3 s | p95 < 5 s |
| Cold start aceptable | < 60 s | < 60 s |
| Presupuesto | $0/mes | $0–9/mes |

Con 3.000 predicciones/mes, el almacenamiento de Grad-CAM es de ~450 MB/mes;
con retención de 90 días, ~1.4 GB. La base de datos crece ~5 MB/mes. Son cifras
que caben holgadamente en un volumen de 100 GB y en la capa gratuita de R2
(10 GB) si se aplica una política de retención.

---

## 3. Línea base actual (as-is)

### 3.1 Diagrama actual

```
┌──────────────────────┐        HTTPS / JSON        ┌─────────────────────────┐
│  Flutter (MVVM)      │  ───────────────────────►  │  Render Free            │
│  Android / iOS / Web │   POST /api/v1/predict     │  FastAPI + Uvicorn      │
│                      │  ◄───────────────────────  │  PyTorch + Grad-CAM     │
│  ONNX local (offline)│   label, confidence,       │  SQLite (efímero)       │
└──────────────────────┘   probabilities, gradcam    │  media/ (efímero)       │
                                                      └───────────┬─────────────┘
                                                                  │
                                                      ┌───────────▼─────────────┐
                                                      │  GitHub Releases (APK)  │
                                                      │  GitHub Actions (build) │
                                                      └─────────────────────────┘
```

### 3.2 Componentes y configuración actual

| Componente | Implementación | Observación |
| --- | --- | --- |
| API | FastAPI 0.115.6, Uvicorn 0.34.0 | Contrato estable en `/api/v1` |
| Inferencia | PyTorch 2.14.1 + torchvision 0.29.1 | `best.pt` de MobileNetV3 |
| Persistencia | SQLite + SQLAlchemy 2.0.36 | 8 tablas; sin Alembic |
| Archivos | `backend/media/gradcam/` | Servidos en `/static` |
| Autenticación | JWT HS256 + refresh token opaco | PBKDF2-HMAC-SHA256; sesiones revocables |
| App | Flutter 3.41.6, Dart ^3.11.4 | MVVM; Android/iOS/Web |
| Offline | ONNX Runtime + `model.onnx` (~16 MB) | Misma clase y triaje que el backend |
| APK | GitHub Actions + GitHub Releases | Firma de desarrollo, no Google Play |
| Hosting | Render Free | URL por defecto en el workflow |
| Modelo de datos | 8 tablas normalizadas | `users`, `ml_models`, `lesion_classes`, `images`, `predictions`, `prediction_scores`, `prediction_feedback`, `auth_sessions` |

### 3.3 Hechos medidos o verificados

| Hecho | Evidencia |
| --- | --- |
| Pico de RSS con MobileNetV3 + Grad-CAM | **342.4 MB** en macOS ARM64, antes de FastAPI completo |
| Checkpoint MobileNetV3 | 16.245 MB; 5.483 M parámetros |
| Pruebas backend | **56 pruebas** (`pytest`), exit 0 |
| Pruebas frontend | **42 pruebas** (`flutter test`), todas pasan |
| Análisis estático Flutter | `flutter analyze`: **No issues found** |
| Pruebas ML | 13 pruebas `unittest` + `smoke_test.py` |
| Timeout del cliente | 60 s, pensado para el *cold start* de Render |
| Límite de subida | 10 MB; formatos JPEG, PNG, BMP, WEBP, TIFF; lado mínimo 32, máximo 4096 |
| Modelo de datos | Solo hash SHA-256 de la imagen; sin nombres, DICOM ni metadatos identificables |

### 3.4 Limitaciones de la línea base

| # | Limitación | Impacto | Severidad |
| --- | --- | --- | --- |
| L1 | Disco efímero en Render Free | SQLite y Grad-CAM se pierden al reiniciar, redeploy o *spin-down* | Alta |
| L2 | 512 MB / 0.1 CPU | OOM o latencia alta con concurrencia; modelos grandes no caben | Alta |
| L3 | *Spin-down* a los 15 min | Primer request tras inactividad tarda ~20–60 s | Media |
| L4 | Postgres Free expira a 30 días | No sirve para persistencia permanente | Alta |
| L5 | Sin respaldos | Un error de datos o de deploy no se puede revertir | Alta |
| L6 | Sin rate limiting | Abuso de CPU, colas y costo (si se escala) | Media |
| L7 | CORS limitado a localhost | Flutter Web en producción requiere configurar orígenes | Media |
| L8 | `JWT_SECRET` por defecto | Si no se define, cualquiera puede firmar tokens | Crítica |
| L9 | Sin CI de backend | Las 56 pruebas no se ejecutan en cada push | Media |
| L10 | Sin *staging* | Los cambios se prueban contra producción/demo | Media |
| L11 | Sin métricas ni trazas | Los fallos se detectan por el usuario | Media |
| L12 | SQLite sin migraciones | Cambios de esquema manuales y riesgosos | Media |
| L13 | Una sola instancia | No hay alta disponibilidad; el *deploy* corta el servicio | Media |
| L14 | Ruta `/static` pública | Grad-CAM accesible sin autenticación (sin PHI, pero es dato clínico derivado) | Baja/Media |
| L15 | Modelo en Git | Repositorio más pesado; no escala a varios checkpoints | Baja |
| L16 | Sin pruebas E2E, de carga ni de seguridad | La calidad se apoya en unitarias/API, no en el flujo completo | Media |

### 3.5 Lo que ya está bien y conviene conservar

- Separación limpia por capas y **MVVM** en Flutter; la vista no hace HTTP.
- **Inferencia real** con un contrato HTTP estable y pruebas con checkpoint.
- **Privacidad por diseño**: solo hash SHA-256, sin datos identificables.
- **Capa de seguridad clínica** con triaje por confianza y margen top-1/top-2.
- **Modo offline** con ONNX y sincronización al recuperar conexión.
- **Autenticación JWT** con refresh token rotativo y sesiones revocables.
- **Reproducibilidad** del pipeline ML (split fijo, semilla 42, manifiestos).
- **APK** publicado automáticamente con checksums.
- **Documentación** académica y Scrum ya existente.

La propuesta no reescribe estas decisiones; las conserva y las lleva a un
entorno con persistencia y operación real.

---

## 4. Requerimientos y restricciones

### 4.1 Requerimientos funcionales del despliegue

| ID | Requerimiento | Criterio de aceptación |
| --- | --- | --- |
| RF-C01 | Exponer la API por HTTPS | `GET /api/v1/health` responde 200 con `model_ready=true` |
| RF-C02 | Clasificar una MRI | `POST /api/v1/predict` responde 201 con etiqueta, confianza, probabilidades y Grad-CAM |
| RF-C03 | Persistir historial | `GET /api/v1/history` conserva los registros tras reiniciar el servicio |
| RF-C04 | Servir Grad-CAM | `GET /static/gradcam/<archivo>.png` responde 200 después de un reinicio |
| RF-C05 | Autenticación opcional | Registro, login, refresh, logout y `me` funcionan con JWT |
| RF-C06 | Feedback humano | `POST /api/v1/predictions/{id}/feedback` registra revisión y corrección |
| RF-C07 | Catálogos y estadísticas | `/models`, `/classes` y `/stats/summary` responden con datos sembrados |
| RF-C08 | Modo offline | La app clasifica sin red con ONNX y sincroniza al reconectar |
| RF-C09 | Exportar reporte PDF | El PDF se genera con y sin Grad-CAM |
| RF-C10 | Publicar APK | El tag `v*` genera un GitHub Release con APK y `SHA256SUMS.txt` |
| RF-C11 | Web | Flutter Web se sirve por HTTPS con la API configurada |
| RF-C12 | Administración | El equipo puede desplegar, revertir y respaldar sin acceso manual al servidor |

### 4.2 Requerimientos no funcionales

| ID | Requerimiento | Objetivo | Verificación |
| --- | --- | --- | --- |
| RNF-C01 | Costo | $0/mes dentro de límites | Facturación y alertas |
| RNF-C02 | Disponibilidad | ≥ 99.0 % mensual (piloto) | UptimeRobot |
| RNF-C03 | Latencia warm | p95 < 3 s para una imagen de 1–3 MB | k6 / logs |
| RNF-C04 | Cold start | < 60 s (solo en opciones con *sleep*) | Medición manual |
| RNF-C05 | Capacidad | 10 usuarios concurrentes sin errores 5xx | Prueba de carga |
| RNF-C06 | Persistencia | RPO ≤ 24 h; RTO ≤ 2 h | Simulacro de restore |
| RNF-C07 | Seguridad | Sin vulnerabilidades críticas/altas abiertas | `pip-audit`, Trivy, ZAP |
| RNF-C08 | Privacidad | Sin PHI en DB, logs ni archivos | Revisión SQL/logs |
| RNF-C09 | Observabilidad | Health check cada 5 min; errores en Sentry | Panel y alertas |
| RNF-C10 | Portabilidad | Contenedor OCI multi-arquitectura | Build arm64/amd64 |
| RNF-C11 | Mantenibilidad | Deploy reproducible en < 15 min | Pipeline |
| RNF-C12 | Reproducibilidad | Imagen y modelo con versiones fijas | `requirements.txt`, digest, SHA-256 |
| RNF-C13 | Escalabilidad | Camino a 30.000 predicciones/mes | Prueba de carga y plan |
| RNF-C14 | Usabilidad | App usable en Android 8+, iOS 13+ y Web | Matriz de compatibilidad |

### 4.3 Restricciones

- **Presupuesto:** el proyecto no puede asumir una factura mensual; cualquier
  gasto debe ser opt-in y con alerta.
- **Equipo:** 3–5 estudiantes, sin un SRE dedicado; la operación debe caber en
  pocas horas al mes.
- **Datos:** no se almacenan datos identificables; no hay DICOM ni historias
  clínicas. Si se usaran pacientes reales, cambia todo el marco regulatorio.
- **Red:** usuarios en Perú/LatAm; la latencia a EE. UU. es aceptable para un
  piloto, pero no para tiempo real estricto.
- **Hardware:** no hay GPU en el servidor; la inferencia es CPU.
- **Modelo:** MobileNetV3 es el único modelo con pesos versionados para el
  despliegue; los otros cuatro están en `ml/models/` localmente.

---

## 5. Principios de arquitectura

1. **Estado fuera del contenedor.** La API debe ser reemplazable; SQLite y los
   archivos viven en un volumen persistente, no en la capa efímera.
2. **Una sola instancia mientras el estado sea SQLite.** SQLite no es un buen
   motor para múltiples réplicas; si se escala horizontalmente, se migra a
   Postgres.
3. **Privacidad por diseño.** Solo hash SHA-256, metadatos técnicos y Grad-CAM;
   nunca nombres, DICOM ni identificadores.
4. **Mínimo privilegio.** Contenedor no-root, firewall de 80/443, SSH solo por
   Bastion/VPN, secretos fuera del repositorio.
5. **Infraestructura reproducible.** Dockerfile, Compose, variables de entorno
   documentadas y versiones fijas; nada de cambios manuales no registrados.
6. **Observabilidad antes que optimización.** Health check, logs estructurados,
   errores con contexto y alertas simples; no se optimiza lo que no se mide.
7. **Costo con guardarraíles.** Recursos Always Free, alertas de facturación,
   presupuesto $0 y revisión mensual.
8. **Degradación elegante.** Si la API no responde, la app sigue funcionando
   offline con ONNX; si Grad-CAM falla, la predicción se devuelve igual.
9. **Documentación como código.** El *runbook*, los umbrales y el contrato se
   versionan en `docs/`.
10. **Evaluar antes de adoptar.** Toda capa gratuita se verifica contra su
    documentación oficial y se prueba con la carga real del proyecto.

---

## 6. Arquitectura propuesta

### 6.1 Vista de alto nivel

```
                         ┌──────────────────────────────┐
                         │  Usuarios                   │
                         │  Android / iOS / Web        │
                         └──────────────┬───────────────┘
                                        │ HTTPS
                         ┌──────────────▼───────────────┐
                         │  Cloudflare (DNS + proxy)    │
                         │  TLS, caché, WAF básico      │
                         └──────────────┬───────────────┘
                                        │ 443
                         ┌──────────────▼───────────────┐
                         │  Oracle Cloud Always Free    │
                         │  VM A1 (ARM64)               │
                         │  ┌────────────────────────┐  │
                         │  │ Caddy (TLS, headers)   │  │
                         │  └───────────┬────────────┘  │
                         │              │ 8000          │
                         │  ┌───────────▼────────────┐  │
                         │  │ FastAPI + Uvicorn      │  │
                         │  │ PyTorch + Grad-CAM     │  │
                         │  └───────┬────────┬───────┘  │
                         │          │        │          │
                         │  ┌───────▼───┐ ┌──▼────────┐ │
                         │  │ SQLite    │ │ media/    │ │
                         │  │ (WAL)     │ │ gradcam/  │ │
                         │  └───────┬───┘ └──┬────────┘ │
                         │          │        │          │
                         │  ┌───────▼────────▼───────┐  │
                         │  │ Volumen de bloque      │  │
                         │  │ 100 GB persistente     │  │
                         │  └───────────┬────────────┘  │
                         └──────────────┼───────────────┘
                                        │ respaldo cifrado
                         ┌──────────────▼───────────────┐
                         │  Oracle Object Storage / R2  │
                         │  DB + Grad-CAM + config      │
                         └──────────────────────────────┘

  CI/CD: GitHub Actions → GHCR (imagen arm64) → SSH → docker compose pull/up
  APK:   GitHub Releases        Web: Cloudflare Pages
  Obs.:  UptimeRobot + Sentry + Grafana Cloud (opcional)
```

### 6.2 Componentes

| Capa | Componente | Tecnología / plan | Función |
| --- | --- | --- | --- |
| Edge | DNS y proxy | Cloudflare Free | DNS, TLS, caché, protección básica |
| Edge | Reverse proxy | Caddy 2 | TLS automático, headers, compresión, rate limit |
| Cómputo | VM | Oracle A1.Flex, 2 OCPU / 3–4 GB | Ejecuta contenedores |
| API | FastAPI + Uvicorn | 1 worker, 2 threads | Contrato REST |
| ML | PyTorch + torchvision | CPU, MobileNetV3 | Inferencia y Grad-CAM |
| Datos | SQLite | WAL, volumen persistente | Historial, usuarios, feedback |
| Archivos | `media/gradcam` | Volumen persistente | Mapas de calor |
| Respaldos | Object Storage | Oracle 20 GB o R2 10 GB | Copias cifradas |
| CI/CD | GitHub Actions | Repo público | Tests, build, deploy |
| Registro | GHCR | Imagen pública/privada | Artefacto inmutable |
| Móvil | GitHub Releases | APK + SHA256 | Distribución |
| Web | Cloudflare Pages | Flutter Web | Distribución estática |
| Observabilidad | UptimeRobot | 50 monitores, 5 min | Disponibilidad |
| Observabilidad | Sentry | 5k errores/mes | Errores backend/frontend |
| Observabilidad | Grafana Cloud | 10k series, 50 GB logs | Métricas/logs opcionales |
| Secretos | Oracle Vault / GitHub Secrets | 150 secretos gratis | `JWT_SECRET`, claves SSH |

### 6.3 Topología de despliegue

| Recurso | Especificación | Justificación |
| --- | --- | --- |
| Región | La más cercana a Perú disponible en Oracle (p. ej., Santiago o São Paulo; verificar latencia) | Menor RTT; Always Free solo en *home region* |
| Shape | `VM.Standard.A1.Flex` | ARM64; 2 OCPU / 12 GB disponibles |
| OCPU / RAM | 2 OCPU / 3 GB (ampliable a 4–6 GB) | 2 OCPU siempre encendidos consumen ~1.460 de 1.500 OCPU-h/mes; 3 GB deja margen y evita la recuperación por inactividad |
| Disco de arranque | 50 GB | Mínimo de Oracle; Ubuntu 24.04 ARM64 |
| Volumen de datos | 100 GB | SQLite, media, backups locales |
| Total de bloque | 150 GB de 200 GB Always Free | Deja 50 GB para backups/snapshots |
| Red | VCN pública; security list 80/443; SSH solo desde Bastion o Tailscale | Mínimo privilegio |
| SO | Ubuntu 24.04 LTS ARM64 | Soporte y paquetes actualizados |
| Docker | Engine + Compose v2 | Simplicidad operativa |
| Usuario | `deploy` no-root, grupo `docker` | Evita operar como root |

> **Cálculo de cuota.** 2 OCPU × 730 h = 1.460 OCPU-h/mes, el 97,3 % de las
> 1.500 h gratuitas. No se debe crear una segunda instancia A1 ni dejar otra
> instancia encendida. 3 GB × 730 h = 2.190 GB-h/mes, el 24,3 % de las 9.000
> GB-h. Si se necesitan 4 GB, el consumo sube a 2.920 GB-h (32,4 %), todavía
> dentro del límite. Usar los 12 GB completos consumiría 8.760 GB-h (97,3 %) y
> dejaría poco margen; no se recomienda.

### 6.4 Flujos principales

#### 6.4.1 Predicción en línea

```
App → HTTPS → Cloudflare → Caddy → FastAPI
  → valida archivo (tipo, tamaño, dimensiones)
  → InferenceService.predict(imagen)
      → preprocesa 224×224 + normalización ImageNet
      → forward MobileNetV3 → softmax(4)
      → Grad-CAM (hook en la capa objetivo)
  → assess(label, confidence, probabilities)  [triaje clínico]
  → persiste image(hash), prediction, scores, gradcam_path
  → responde 201 JSON
```

#### 6.4.2 Predicción offline y sincronización

```
App sin red → ONNX Runtime local (mismo preprocesamiento)
  → clasifica + triaje local
  → guarda pendiente en LocalDB (SQLite local)
  → al recuperar conexión: SyncService
      → registra cuentas pendientes
      → envía feedback en cola
      → reenvía imágenes a POST /predict
      → el backend re-infere y guarda el registro definitivo
```

#### 6.4.3 Autenticación

```
POST /auth/register → valida email único → PBKDF2 → usuario
  → emite JWT (HS256, 7 días) + refresh token opaco (30 días)
  → guarda hash del refresh en auth_sessions
POST /auth/refresh → valida hash, no revocado, no expirado
  → revoca la sesión anterior y emite una nueva (rotación)
POST /auth/logout → marca revoked_at
GET /auth/me → valida JWT y devuelve usuario
```

#### 6.4.4 Respaldo

```
Cron diario 03:00 UTC:
  sqlite3 db.sqlite3 ".backup '/backups/db-YYYYMMDD.sqlite3'"
  tar -czf media-YYYYMMDD.tar.gz media/gradcam
  sha256sum > SHA256SUMS
  age -r <clave-pública> → archivo .age
  rclone copy /backups remote:bucket/backups
  retención: 7 diarios + 4 semanales + 3 mensuales
  verificación semanal: restaurar en un directorio temporal
```

### 6.5 Entornos

| Entorno | Propósito | Datos | Modelo | URL |
| --- | --- | --- | --- | --- |
| Local | Desarrollo y pruebas | Sintéticos / test split | `best.pt` local | `http://localhost:8000` |
| CI | Tests automatizados | Fixtures y checkpoint aleatorio | `shufflenetv2` de prueba | Sin URL pública |
| Staging | Validación previa | Copia anonimizada del demo | Mismo `best.pt` | `https://staging.api...` |
| Producción/demo | Sustentación y piloto | Datos reales del demo (sin PHI) | `best.pt` versionado | `https://api...` |

Para un equipo académico, *staging* puede ser un contenedor en la misma VM con
otra base y otro puerto, o un Render Free separado. Lo importante es no probar
migraciones ni cambios de contrato directamente contra el entorno que se
muestra al jurado.

### 6.6 Configuración y secretos

| Variable | Ejemplo / valor | Secreto | Nota |
| --- | --- | --- | --- |
| `APP_NAME` | `Brain Tumor Classification API` | No | — |
| `API_V1_PREFIX` | `/api/v1` | No | — |
| `MODEL_PATH` | `/data/models/mobilenetv3/best.pt` | No | Ruta en el volumen |
| `MODEL_VERSION` | `mobilenetv3-v1` | No | Debe coincidir con el catálogo |
| `IMAGE_SIZE` | `224` | No | — |
| `DATABASE_URL` | `sqlite:////data/db.sqlite3` | No | Cuatro barras = ruta absoluta |
| `MEDIA_ROOT` | `/data/media` | No | Grad-CAM |
| `MAX_UPLOAD_BYTES` | `10485760` | No | 10 MB |
| `JWT_SECRET` | 32+ bytes aleatorios | **Sí** | Nunca en Git; rotar si se filtra |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | No | 7 días |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `30` | No | — |
| `CORS_ORIGINS` | `["https://app.example.com"]` | No | Solo orígenes reales |
| `CORS_ORIGIN_REGEX` | `""` en producción | No | Evitar localhost en prod |
| `CLINICAL_CONFIDENCE_THRESHOLD` | `0.70` | No | Capa de seguridad |
| `CLINICAL_MARGIN_THRESHOLD` | `0.10` | No | Capa de seguridad |
| `CLINICAL_HIGH_CONFIDENCE_THRESHOLD` | `0.90` | No | Capa de seguridad |
| `SENTRY_DSN` | `<dsn>` | **Sí** | Opcional |
| `TZ` | `UTC` | No | Logs y backups consistentes |

**Regla:** los secretos se configuran en GitHub Actions Secrets, en el archivo
`/etc/app/.env` con permisos `600`, o en Oracle Vault. Nunca se commitean. El
`.env.example` solo contiene valores de desarrollo.

### 6.7 Contenedores y Compose

La API se construye con un Dockerfile multi-stage y una imagen base fijada por
digest. El contenedor corre como usuario no-root, con `HEALTHCHECK` y sin
dependencias de compilación en la imagen final.

```yaml
# docker-compose.yml (extracto conceptual)
services:
  api:
    image: ghcr.io/sonedxe/brain-tumor-classification-api:${TAG:-latest}
    build:
      context: .
      dockerfile: backend/Dockerfile
      platforms: [linux/arm64]
    env_file: /etc/btc/api.env
    environment:
      HOME: /tmp
      TORCH_HOME: /tmp/torch
    volumes:
      - /srv/btc/data:/data:rw
      - /srv/btc/models:/data/models:ro
    expose:
      - "8000"
    mem_limit: 2g
    cpus: 1.8
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp:size=256m
    security_opt:
      - no-new-privileges:true
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 90s

  caddy:
    image: caddy:2.8-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    depends_on:
      - api

volumes:
  caddy_data:
  caddy_config:
```

**Notas de implementación:**

- `read_only: true` obliga a montar `/tmp` y `/data`; evita escrituras
  accidentales en la imagen.
- `mem_limit: 2g` deja ~1 GB para el sistema y Caddy en una VM de 3 GB.
- `cpus: 1.8` reserva capacidad para el sistema y evita que una inferencia
  sature los 2 OCPU.
- `start_period: 90s` cubre la carga de PyTorch y del checkpoint.
- No se incluye un contenedor de base de datos: SQLite es un archivo.
- Si se migra a Postgres, se añade un servicio `db` o se usa Neon; en ese caso
  el API deja de montar `/data/db.sqlite3`.

### 6.8 Dockerfile propuesto

El Dockerfile actual copia `backend/` y `ml/configs`, pero no los pesos. Para
la VM se propone:

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TORCH_NUM_THREADS=2 \
    OMP_NUM_THREADS=2 \
    MALLOC_ARENA_MAX=2
RUN groupadd -g 10001 app && useradd -u 10001 -g app -d /app -s /sbin/nologin app
WORKDIR /app
COPY --from=builder /install /usr/local
COPY backend /app/backend
COPY ml/configs /app/ml/configs
COPY .env.example /app/.env.example
RUN mkdir -p /data/media/gradcam /data/models && chown -R app:app /data /app
USER app
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--limit-concurrency", "4", "--timeout-keep-alive", "30"]
```

> El modelo no se hornea en la imagen: se monta desde `/data/models` o se
> descarga al arrancar con verificación SHA-256. Así se puede cambiar el modelo
> sin reconstruir la imagen y se mantiene la imagen por debajo de ~1.2 GB.
>
> Para CPU, instalar `torch`/`torchvision` desde el índice oficial
> `https://download.pytorch.org/whl/cpu` (o fijar la variante en un constraints
> file). No usar el wheel CUDA por defecto: infla la imagen y consume memoria.
> Verificar que exista wheel `linux/aarch64` para la versión fijada; si no,
> usar ONNX Runtime en el backend o una VM x86.

> El volumen `/srv/btc/data` debe pertenecer al UID/GID 10001 del usuario
> `app` del contenedor. Si se cambia el UID, ajustar el `chown` del host.

**`.dockerignore` mínimo** (sin esto, el contexto puede incluir `.venv`,
`frontend/build` y `ml/models`, y el build se vuelve lentísimo):

```text
.git
**/.venv
**/__pycache__
**/*.pyc
frontend/build
frontend/.dart_tool
ml/data
ml/models
docs
```

Si se decide descargar el modelo durante el build, quitar `ml/models` del
`.dockerignore` y usar un `RUN` con verificación SHA-256.

### 6.9 CI/CD

```
push / pull request
  ├─ backend: ruff? + pytest (56) + pip-audit
  ├─ frontend: flutter analyze + flutter test (42)
  ├─ ml: smoke_test (entorno ML)
  └─ docker: buildx linux/arm64 (sin push en PR)

tag v* o merge a main
  ├─ build y push a GHCR con tag = SHA corto
  ├─ SSH a la VM: docker compose pull && up -d
  ├─ smoke: GET /api/v1/health (model_ready=true)
  ├─ si falla: rollback al tag anterior
  └─ GitHub Release: APK + SHA256SUMS
```

**Recomendaciones:**

- Fijar acciones por SHA, no por tag flotante.
- Usar `concurrency` para cancelar despliegues viejos.
- Guardar el tag anterior en `/srv/btc/.last_good` para rollback.
- No desplegar si las pruebas o el análisis estático fallan.
- El workflow actual solo compila el APK; hay que añadir el job de backend.

### 6.10 Observabilidad y SLO

| SLI | SLO (piloto) | Medición |
| --- | --- | --- |
| Disponibilidad | ≥ 99.0 % mensual | UptimeRobot `/api/v1/health` cada 5 min |
| Latencia warm | p95 < 3 s | Logs de `inference_ms` + prueba k6 |
| Tasa de error | < 2 % de requests 5xx | Sentry / logs |
| Éxito de inferencia | > 99.5 % | Contador de predicciones vs. errores |
| Cold start | < 60 s (si aplica) | Medición manual |
| Respaldo | 100 % de ejecuciones diarias | Verificación del cron |
| Restore | RTO < 2 h, RPO < 24 h | Simulacro trimestral |

**Alertas mínimas:**

- Health check falla 2 veces consecutivas (10 min) → email/Telegram.
- 5xx > 5 % durante 10 min → email.
- Disco > 80 % → email.
- Memoria > 85 % durante 10 min → email.
- Respaldo fallido → email.
- Certificado TLS por vencer (< 14 días) → email.

**Herramientas:** UptimeRobot Free (50 monitores, 5 min), Sentry Developer
(5.000 errores/mes, 1 usuario), Grafana Cloud Free (10.000 series, 50 GB logs,
14 días de retención, 3 usuarios) y `journald` con rotación. No se necesita una
plataforma de observabilidad completa para un piloto; sí se necesita saber si
el servicio está vivo y por qué falló.

### 6.11 Seguridad

#### Modelo de amenazas resumido (STRIDE)

| Amenaza | Escenario | Control |
| --- | --- | --- |
| Spoofing | Robo de JWT o refresh token | HTTPS, expiración corta, rotación, revocación, almacenamiento seguro |
| Tampering | Modificación de imagen o payload | Validación de tipo/tamaño/dimensiones, checksum, esquema Pydantic |
| Repudiation | Usuario niega una predicción | Historial con `created_at`, `source`, feedback y logs de auditoría |
| Information disclosure | Fuga de Grad-CAM o DB | Sin PHI, `/static` con hash no adivinable, backups cifrados, logs sin imágenes |
| Denial of service | Subida masiva o imágenes gigantes | Límite 10 MB, 4096 px, rate limit, timeout, concurrencia limitada |
| Elevation of privilege | Contenedor root o SSH abierto | Non-root, `no-new-privileges`, firewall, SSH por Bastion/Tailscale |
| Supply chain | Dependencia o imagen comprometida | Versiones fijas, `pip-audit`, Trivy, GHCR, acciones pinneadas |

#### Controles mínimos de puesta en producción

- [ ] `JWT_SECRET` aleatorio de 32+ bytes, distinto de desarrollo.
- [ ] `CORS_ORIGINS` con el dominio real de Flutter Web; sin `*`.
- [ ] HTTPS obligatorio; HSTS; TLS 1.2+.
- [ ] Rate limit por IP en login, registro y predict.
- [ ] Límite de subida y validación de imagen ya existentes.
- [ ] Contenedor no-root, `read_only`, `no-new-privileges`.
- [ ] Firewall: solo 80/443 públicos; SSH restringido.
- [ ] Backups cifrados y probados.
- [ ] Dependencias auditadas; imagen escaneada.
- [ ] Logs sin PHI, sin tokens y sin imágenes.
- [ ] Alertas de salud, errores y disco.
- [ ] Documento de respuesta a incidentes y contacto.

#### Privacidad

El backend persiste únicamente:

- Hash SHA-256 de la imagen.
- Dimensiones, formato y tamaño.
- Etiqueta, confianza, probabilidades, modelo y latencia.
- Ruta del Grad-CAM.
- `source` (flutter/web/api) y feedback humano.

No persiste nombres de archivo originales, DICOM, edad, sexo, institución ni
ningún identificador. El historial es, por tanto, seudónimo. Aun así, un
Grad-CAM deriva de una MRI y podría considerarse dato clínico; por eso se
recomienda autenticar `/static` en un entorno con pacientes reales y aplicar
retención (90 días para Grad-CAM, 12 meses para historial).

#### Marco regulatorio

Para una demo académica, basta el aviso de no-dispositivo-médico. Para uso
clínico real se necesitaría, como mínimo:

- Validación clínica con radiólogos y un conjunto externo.
- Comité de ética y consentimiento informado.
- Gestión de riesgos (ISO 14971), ciclo de vida de software médico
  (IEC 62304) y sistema de calidad (ISO 13485).
- Clasificación regulatoria (SaMD) y evaluación de conformidad.
- Acuerdo de tratamiento de datos (HIPAA BAA, GDPR o ley local) y cifrado en
  reposo/tránsito.
- Trazabilidad de versiones de modelo, datos y decisiones.

Nada de esto se resuelve con una capa gratuita; es un proyecto aparte.

### 6.12 Respaldo y recuperación

| Aspecto | Definición |
| --- | --- |
| RPO | ≤ 24 h (respaldo diario) |
| RTO | ≤ 2 h (restaurar DB + media + contenedor) |
| Frecuencia | Diaria 03:00 UTC; semanal completa |
| Retención | 7 diarios, 4 semanales, 3 mensuales |
| Cifrado | `age` o `gpg` con clave pública; bucket privado |
| Verificación | Restore automático semanal en directorio temporal + `PRAGMA integrity_check` |
| Ubicación | Oracle Object Storage (20 GB) o Cloudflare R2 (10 GB) |
| Prueba | Simulacro trimestral documentado |

**Runbook de restore:**

```bash
# 1. Detener la API
cd /srv/btc && docker compose stop api

# 2. Descargar el respaldo más reciente
rclone copy remote:bucket/backups/2026-11-13/ /srv/btc/restore/

# 3. Descifrar y verificar
age -d -i /etc/app/age.key -o db.sqlite3.age \
  /srv/btc/restore/db-20261113.sqlite3.age
sha256sum -c SHA256SUMS
sqlite3 db.sqlite3 "PRAGMA integrity_check;"

# 4. Restaurar datos y media
install -o 10001 -g 10001 -m 600 db.sqlite3 /srv/btc/data/db.sqlite3
tar -xzf media-20261113.tar.gz -C /srv/btc/data/

# 5. Arrancar y verificar
docker compose up -d api
curl -fsS https://api.example.com/api/v1/health | jq .
curl -fsS https://api.example.com/api/v1/history?limit=1 | jq .
```

### 6.13 Escalabilidad

| Etapa | Carga | Arquitectura | Acción |
| --- | --- | --- | --- |
| Demo | < 3.000 pred/mes | 1 VM, SQLite, 1 worker | Actual |
| Piloto | 3.000–30.000 | 1 VM más grande; 2 workers; retención 90 días | Vertical scaling |
| Crecimiento | 30.000–100.000 | Postgres gestionado (Neon/Supabase), R2, 2 réplicas | Migrar estado |
| Producción | > 100.000 o SLA | Load balancer, 2+ VM, Postgres HA, object storage, CDN | Contrato paid |

**Cuándo migrar de SQLite a Postgres:**

- Más de una instancia de API.
- Escrituras concurrentes sostenidas.
- Necesidad de backups point-in-time.
- Crecimiento de la DB > 1 GB o consultas lentas.
- Requisito de alta disponibilidad.

La migración es directa porque el acceso a datos ya está en repositorios
SQLAlchemy; requiere añadir `psycopg`, cambiar `DATABASE_URL` y adoptar Alembic
para migraciones.

---

## 7. Evaluación de proveedores y capas gratuitas

### 7.1 Método

Se evaluaron cuatro dimensiones:

1. **Viabilidad técnica para PyTorch en CPU.** RAM, CPU, arquitectura, disco y
   capacidad de ejecutar un contenedor Docker con `torch` + `torchvision`.
2. **Persistencia.** ¿El disco sobrevive a reinicios y redeploys? ¿Hay base de
   datos gestionada? ¿Se pueden guardar Grad-CAM?
3. **Costo real.** No solo el precio de lista: límites de horas, *sleep*,
   vencimiento de bases gratuitas, egreso, almacenamiento y cargos ocultos.
4. **Carga operativa.** ¿Cuánto trabajo exige aprovisionar, desplegar,
   actualizar, respaldar y monitorear?

La verificación se hizo contra la documentación oficial el **13/11/2026**. Los
valores son referenciales y pueden cambiar; la columna “Veredicto” es la lectura
del equipo para este proyecto, no una recomendación general.

### 7.2 Tabla comparativa

| Proveedor / servicio | Rol | Capa gratuita vigente (13/11/2026) | Límites que importan | Veredicto |
| --- | --- | --- | --- | --- |
| **Oracle Cloud Always Free** | VM para API | 2 OCPU Ampere A1 + 12 GB RAM; 200 GB de bloque; 20 GB Object Storage; 10 TB egreso/mes | 1.500 OCPU-h y 9.000 GB-h/mes; solo *home region*; puede reclamar instancias ociosas; capacidad A1 no siempre disponible | **Recomendado** para el backend si se acepta operar una VM |
| **Render Free** | PaaS para API | Web service 512 MB / 0.1 CPU; 750 h/mes; Postgres 1 GB | *Sleep* a los 15 min; disco efímero; Postgres expira a los 30 días; sin shell; sin disco persistente | **Viable solo para demo**; no para persistencia |
| **Google Cloud Free Tier** | VM x86 | 1 `e2-micro` (1 GB), 30 GB disco, 1 GB egreso/mes | Solo regiones de EE. UU.; requiere cuenta de facturación; 1 GB de RAM es justo para PyTorch | **Alternativa** si se usa ONNX Runtime o un modelo muy pequeño |
| **Modal Starter** | Serverless | $30 USD/mes de crédito; 1 TiB egreso; 100 contenedores | Los créditos se agotan; el estado debe externalizarse; *cold starts*; requiere tarjeta | **Buena opción** si se quiere serverless y se acepta el crédito recurrente |
| **Railway Free** | PaaS | $1 USD/mes de crédito; 1 vCPU / 0.5 GB | El crédito no alcanza para una API con PyTorch 24/7; Hobby $5/mes | **No viable** para este backend; sí para un frontend estático |
| **Hugging Face Spaces** | Demo ML | CPU Basic 2 vCPU / 16 GB / 50 GB sin costo por hora | Crear Docker/Gradio Spaces requiere plan de pago (PRO $9/mes); *sleep* a las 48 h; disco no persistente | **No es gratis para Spaces nuevos**; PRO es opción de bajo costo |
| **Koyeb** | PaaS | Free 512 MB / 0.1 vCPU / 2 GB (organizaciones existentes) | Según anuncios de feb-2026, nuevas cuentas pasan a Pro ($29/mes); sin volúmenes en free; *scale-to-zero* 1 h | **Descartado** para un proyecto nuevo; verificar al registrar |
| **Neon** | Postgres | 100 proyectos; 100 CU-h/proyecto; 1 GB; 5 GB egreso | *Scale-to-zero* a los 5 min; sin SLA; storage compartido por proyecto | **Recomendado** como DB si se externaliza el estado |
| **Supabase** | Postgres + Auth + Storage | 500 MB DB; 1 GB storage; 5 GB egreso; 50k MAU | Pausa tras 7 días de inactividad; sin backups automáticos | **Viable** para un piloto; la pausa es un riesgo |
| **Cloudflare R2** | Object storage | 10 GB; 1 M Class A; 10 M Class B; egreso gratis | Requiere método de pago para activar; solo Standard; operaciones se redondean | **Recomendado** para Grad-CAM y backups |
| **Cloudflare Pages** | Flutter Web | 500 builds/mes; 20.000 archivos; 25 MiB/archivo; requests estáticos ilimitados | 1 build concurrente; 20 min por build | **Recomendado** para la web |
| **GitHub Actions** | CI/CD | Repos públicos gratis; GitHub Free privado: $12 USD/mes de cómputo | Minutos de macOS más caros; artefactos 500 MB; cache 10 GB | **Recomendado**; el repo es público |
| **GitHub Releases** | APK | Gratis para repos públicos | 2 GB por archivo; ancho de banda razonable | **Recomendado**; ya implementado |
| **UptimeRobot** | Monitoreo | 50 monitores; intervalo 5 min; 1 status page | Sin SMS/voz gratis; 3 meses de retención | **Suficiente** para disponibilidad |
| **Sentry Developer** | Errores | 1 usuario; 5.000 errores/mes; 5 GB logs; 5 M spans; 50 replays | 30 días de retención; 1 monitor de uptime | **Suficiente** para backend y app |
| **Grafana Cloud Free** | Métricas/logs | 10.000 series; 50 GB logs; 50 GB traces; 14 días; 3 usuarios | Sin SLA; no export de métricas en free | **Opcional**; útil si se instrumenta Prometheus/OTel |

### 7.3 Cambios relevantes respecto a guías antiguas

| Creencia común | Realidad en noviembre de 2026 | Implicación |
| --- | --- | --- |
| “Hugging Face Spaces es gratis para Docker” | CPU Basic no cuesta por hora, pero **crear** un Docker/Gradio Space requiere plan de pago | No se puede usar como backend gratuito nuevo; PRO $9/mes |
| “Koyeb tiene free tier” | La instancia gratuita queda para organizaciones antiguas; nuevas cuentas pasan a Pro | No recomendable para un proyecto que empieza |
| “Render free sirve para producción” | 512 MB, 0.1 CPU, *sleep* 15 min, disco efímero, Postgres 30 días | Solo demo; no persistencia |
| “Oracle da 4 OCPU y 24 GB” | La cuota actual es 1.500 OCPU-h/9.000 GB-h ≈ 2 OCPU/12 GB | Ajustar el dimensionamiento y no crear dos instancias |
| “Railway es gratis” | Free = $1/mes de crédito; Hobby $5/mes | No alcanza para PyTorch |
| “GitHub Actions es gratis para todo” | Repos públicos sí; privados tienen $12/mes en GitHub Free | Mantener el repo público o vigilar el consumo |
| “Cloudflare R2 es gratis sin tarjeta” | La capa es gratis, pero activar R2 requiere método de pago | Considerar Oracle Object Storage si no se quiere tarjeta |

### 7.4 Combinaciones viables

| Combo | Cómputo | Base de datos | Archivos | Costo | Comentario |
| --- | --- | --- | --- | --- | --- |
| **A. Oracle full** | Oracle A1 2 OCPU/3–4 GB | SQLite en volumen | Volumen + Object Storage | $0 | Recomendado; más operación |
| **B. Render + Neon + R2** | Render Free 512 MB | Neon Free | R2 Free | $0 | Mínimo cambio; 512 MB y *sleep* siguen siendo el límite |
| **C. Modal + Neon + R2** | Modal Starter | Neon Free | R2 Free | $0 dentro de $30 crédito | Serverless; estado externalizado; buen camino si se agota la VM |
| **D. HF PRO + Neon + R2** | HF Space CPU Basic (PRO) | Neon Free | R2 Free | $9/mes | La opción más simple para una demo ML; no es $0 |
| **E. GCP e2-micro + SQLite** | GCP e2-micro 1 GB | SQLite | Disco 30 GB | $0 | Solo si se usa ONNX Runtime; 1 GB es muy justo para PyTorch |
| **F. Render Free solo** | Render Free | SQLite efímero | Disco efímero | $0 | Solo demo; pérdida de datos en cada *spin-down* |

### 7.5 Estimación de costos por escenario

Supuestos: imagen promedio 1.5 MB, Grad-CAM 150 KB, retención de 90 días,
3.000 predicciones/mes en el escenario base. Los precios son de lista y no
incluyen impuestos.

| Concepto | Demo (3k pred/mes) | Piloto (30k pred/mes) | Crecimiento (100k pred/mes) |
| --- | --- | --- | --- |
| Subida de imágenes (ingreso) | ~4.5 GB | ~45 GB | ~150 GB |
| Egreso JSON + Grad-CAM | ~0.5 GB | ~5 GB | ~16 GB |
| Grad-CAM almacenado (90 días) | ~1.4 GB | ~13.5 GB | ~45 GB |
| DB SQLite | ~50 MB | ~500 MB | ~1.5 GB |
| Oracle VM | $0 | $0 | $0 (hasta 2 OCPU/12 GB) |
| Oracle Object Storage | $0 (20 GB) | $0 (20 GB) | $0 (20 GB; usar R2 si se supera) |
| R2 (si se usa) | $0 (10 GB) | ~$0.05/mes por 13.5 GB | ~$0.53/mes por 45 GB |
| Render Free | $0 | No viable por RAM/bandwidth | No viable |
| Render Starter (si se escala) | $7/mes | $7/mes + DB | $25+/mes |
| Neon Free | $0 | $0 (1 GB) | $0–$19/mes (Launch) |
| Cloudflare Pages | $0 | $0 | $0 |
| GitHub Actions | $0 (público) | $0 (público) | $0 (público) |
| Sentry / UptimeRobot / Grafana | $0 | $0 | $0–$19/mes |
| **Total estimado** | **$0** | **$0–$9/mes** | **$0–$40/mes** |

**Lectura:** el costo no es el problema en el rango académico; el problema es
la operación y los límites de memoria. Oracle permite llegar a 30.000
predicciones/mes sin pagar, siempre que se respete la cuota de 2 OCPU y se
use un volumen de 100 GB. A partir de ~100.000 predicciones/mes, el egreso y el
almacenamiento de Grad-CAM obligan a una política de retención más agresiva o a
un plan pagado.

### 7.6 Costos ocultos y letra pequeña

- **Tarjeta de crédito:** Oracle, GCP, Modal, R2 y Railway pueden pedir una
  tarjeta para verificar identidad. Oracle no cobra si no se actualiza a pago
  por uso, pero puede hacer una retención temporal.
- **Tiempo de operación:** una VM no es gratis en esfuerzo. Se estiman 16–24 h
  de puesta en marcha y 2–4 h/mes de mantenimiento (parches, backups,
  incidentes).
- **Egreso:** Oracle incluye 10 TB/mes; Render incluye 5 GB/mes en Hobby;
  Cloudflare R2 no cobra egreso. El egreso de imágenes es bajo, pero un video o
  un log mal configurado puede dispararlo.
- **Almacenamiento:** Supabase Free tiene 1 GB; no sirve para Grad-CAM a largo
  plazo. R2 tiene 10 GB; con 30.000 predicciones/mes y 90 días se acerca al
  límite.
- **Cold starts:** Render y HF duermen; el tiempo de espera no cuesta dinero,
  pero sí experiencia de usuario y tiempo de demo.
- **Vendor lock-in:** un PaaS facilita el despliegue, pero migrar de Render a
  Oracle exige contenedor, proxy y backups. La opción A usa estándares
  (Docker, SQLite, Caddy) y reduce el lock-in.
- **Cambios de plan:** una capa gratuita puede desaparecer o reducirse (Koyeb,
  HF). Tener backups y una imagen Docker permite migrar en horas, no en semanas.

---

## 8. Alternativas y decisión

### 8.1 Opciones evaluadas

#### Opción A — Oracle Cloud Always Free + Docker Compose (recomendada)

**Ventajas:**

- 2 OCPU / 12 GB disponibles; se pueden asignar 3–4 GB y 2 OCPU.
- 200 GB de bloque y 20 GB de Object Storage; persistencia real.
- Sin *sleep* ni *cold start*; la API está siempre disponible.
- Egreso de 10 TB/mes; sobra para el proyecto.
- Estándares abiertos: Docker, SQLite, Caddy; migrar es sencillo.
- Costo $0 dentro de la cuota.

**Desventajas:**

- Hay que aprovisionar y operar una VM (parches, firewall, backups).
- Oracle puede reclamar instancias ociosas; hay que dimensionar memoria y
  monitorear.
- Capacidad A1 no siempre disponible en la región; puede fallar el alta.
- La cuota de 2 OCPU siempre encendidos consume casi toda la bolsa mensual.
- No hay SLA ni soporte en Always Free.

**Mitigaciones:** Docker Compose, backups automáticos, UptimeRobot, runbook,
dimensionar 3 GB para superar el 20 % de memoria y mantener la instancia
“activa” con uso real; si se agota la capacidad, usar Render+Neon+R2 como
respaldo.

#### Opción B — Render Free + Neon + R2 (mínimo cambio)

**Ventajas:**

- Ya está desplegado; el equipo conoce Render.
- Cero operación de servidor.
- Neon y R2 resuelven persistencia y backups.
- Costo $0.

**Desventajas:**

- 512 MB / 0.1 CPU: el pico medido de 342 MB deja poco margen; con FastAPI,
  sistema y concurrencia puede fallar.
- *Sleep* a los 15 min; primer request lento.
- Requiere adaptar SQLite a Postgres (psycopg, migraciones, pruebas).
- Render Free no tiene shell ni disco persistente.
- El egreso incluido es limitado.

**Veredicto:** buena **continuidad inmediata** mientras se migra; no es la
arquitectura objetivo.

#### Opción C — Modal Starter + Neon + R2 (serverless)

**Ventajas:**

- $30 USD/mes de crédito; escala a cero; 1 TiB de egreso.
- Ideal para cargas intermitentes y demostraciones.
- No se administra servidor; se despliega una imagen/ función.
- Excelente para picos o para separar la inferencia del API.

**Desventajas:**

- Los créditos se agotan; si no se pone un límite, puede generar factura.
- El estado debe estar en Neon/R2; no hay SQLite local.
- *Cold starts* y latencia variable.
- Requiere adaptar el despliegue a la plataforma (contenedor/ASGI).

**Veredicto:** plan B técnico si Oracle no es viable; también sirve para
pruebas de carga puntuales.

#### Opción D — Hugging Face Spaces PRO + Neon + R2

**Ventajas:**

- 2 vCPU / 16 GB / 50 GB; muy buen encaje para PyTorch.
- Interfaz pensada para demos de ML; fácil de compartir.
- PRO cuesta $9/mes, mucho menos que un servidor equivalente.

**Desventajas:**

- Ya no es gratuito para Docker Spaces nuevos.
- Disco no persistente; *sleep* a las 48 h (configurable en paid).
- Requiere Neon/R2 para historial.
- La imagen debe exponer el puerto correcto y cumplir las reglas de HF.

**Veredicto:** mejor relación simplicidad/precio si se aceptan $9/mes; no es
$0.

#### Opción E — Google Cloud e2-micro

**Ventajas:**

- Always Free real (1 GB, 30 GB, 1 GB egreso) en regiones de EE. UU.
- x86, sin sorpresas de ARM64.
- Integración con Cloud Monitoring/Logging.

**Desventajas:**

- 1 GB de RAM es insuficiente para PyTorch + Grad-CAM con holgura; habría que
  usar ONNX Runtime o un modelo más pequeño.
- 1 GB de egreso/mes es justo si se sirven muchos Grad-CAM.
- Requiere cuenta de facturación y tarjeta.
- Latencia desde Perú a EE. UU. acceptable, pero no óptima.

**Veredicto:** interesante si se migra la inferencia a ONNX Runtime; no para
el estado actual con PyTorch.

### 8.2 Matriz de decisión ponderada

Escala 1–5 (5 = mejor). Los pesos suman 100 %.

| Criterio | Peso | A Oracle | B Render+Neon | C Modal | D HF PRO | E GCP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Costo | 25 % | 5 | 5 | 4 | 3 | 4 |
| Encaje con PyTorch | 20 % | 5 | 3 | 5 | 5 | 2 |
| Persistencia | 15 % | 5 | 4 | 3 | 3 | 4 |
| Carga operativa (5 = poca) | 15 % | 2 | 5 | 4 | 5 | 2 |
| Rendimiento | 10 % | 5 | 2 | 4 | 4 | 2 |
| Escalabilidad | 10 % | 3 | 2 | 5 | 3 | 2 |
| Lock-in (5 = bajo) | 5 % | 3 | 3 | 2 | 2 | 3 |
| **Total ponderado** | **100 %** | **4.25** | **3.75** | **4.05** | **3.75** | **2.85** |

**Resultado:** A (Oracle) gana por persistencia, rendimiento y encaje con
PyTorch; C (Modal) queda cerca por su excelente encaje y menor operación, pero
pierde en persistencia y lock-in. B y D empatan; B es la continuidad inmediata
y D la opción de bajo costo si se prefiere no operar una VM.

### 8.3 Análisis de sensibilidad

- Si el equipo **no puede dedicar tiempo a operar una VM**, C o D son mejores;
  A solo tiene sentido con un responsable de infraestructura.
- Si el requisito es **$0 estricto y sin tarjeta**, B es la única opción
  inmediata, pero con pérdida de datos; hay que asumir que es una demo.
- Si se necesita **persistencia y disponibilidad sostenida**, A es la única
  opción gratuita con esas propiedades.
- Si se espera **> 30.000 predicciones/mes**, A sigue siendo viable; C puede
  ser más caro que $30 de crédito; B no aguanta.
- Si se necesita **SLA o soporte**, ninguna capa gratuita sirve; hay que pagar.

### 8.4 Decisión

Se adopta **A (Oracle Cloud Always Free + Docker Compose)** como arquitectura
objetivo, con **B (Render + Neon + R2)** como plan de continuidad y **C
(Modal)** como plan de escalamiento puntual. La decisión se registra como ADR:

> **ADR-001:** usar una VM Always Free de Oracle con Docker Compose para el
> backend, SQLite en volumen persistente, Caddy para TLS y backups a Object
> Storage/R2. Mantener Render Free solo como demo de respaldo. La decisión se
> revisa si Oracle no entrega capacidad, si la cuota de 2 OCPU se vuelve
> insuficiente o si el equipo no puede sostener la operación.

---

## 9. Diseño detallado de la opción recomendada

### 9.1 Dimensionamiento

| Recurso | Cálculo | Resultado |
| --- | --- | --- |
| OCPU | 2 OCPU × 730 h | 1.460 OCPU-h/mes (97,3 % de 1.500) |
| RAM | 3 GB × 730 h | 2.190 GB-h/mes (24,3 % de 9.000) |
| Disco | 50 GB boot + 100 GB datos | 150 GB de 200 GB |
| Object Storage | DB + media + config | < 20 GB (o R2 < 10 GB con retención) |
| Egreso | 3.000 × (5 KB + 150 KB) + 4.5 GB subida | < 5 GB/mes (de 10 TB) |
| Inferencia | 3.000 × 0,5 s | ~25 min de CPU/mes |
| Pico de RAM medido | MobileNetV3 + Grad-CAM | 342 MB (app) + FastAPI/SO |
| Margen de RAM | 3 GB − ~0,9 GB base | ~2,1 GB para concurrencia/Grad-CAM |

**Recomendación:** 2 OCPU / 3 GB. Si se observa swapping o picos de Grad-CAM,
subir a 4 GB (2.920 GB-h, aún dentro de la cuota). No usar 12 GB salvo que se
necesite y se acepte consumir el 97 % de la bolsa de memoria.

### 9.2 Aprovisionamiento de la VM

Pasos generales (adaptar a la consola/CLI de Oracle):

```bash
# 1. Crear VCN, subred pública y security list 80/443 (SSH solo desde Bastion).
# 2. Crear instancia A1.Flex:
#    shape: VM.Standard.A1.Flex
#    ocpus: 2, memory: 3 GB
#    image: Ubuntu 24.04 (ARM64)
#    boot volume: 50 GB
# 3. Crear y adjuntar volumen de bloque de 100 GB.
# 4. Formatear y montar en /srv/btc:
sudo mkfs.ext4 /dev/oracleoci/oraclevdb
sudo mkdir -p /srv/btc
echo '/dev/oracleoci/oraclevdb /srv/btc ext4 defaults,noatime 0 2' | sudo tee -a /etc/fstab
sudo mount -a

# 5. Usuario de despliegue y Docker
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG docker deploy
sudo apt update && sudo apt install -y git curl docker.io docker-compose-v2 sqlite3 rclone age
sudo systemctl enable --now docker

# 6. Directorios y repositorio
sudo mkdir -p /srv/btc/{app,data,models,backups,restore}
sudo chown -R deploy:deploy /srv/btc
git clone https://github.com/sonedxe/brain-tumor-classification.git /srv/btc/app
# El contenedor corre con UID/GID 10001; el volumen debe pertenecerle.
sudo chown -R 10001:10001 /srv/btc/data
sudo chmod 750 /srv/btc/data

# Pesos del modelo (no se hornean en la imagen)
sudo mkdir -p /srv/btc/models/mobilenetv3
sudo cp /srv/btc/app/ml/models/mobilenetv3/best.pt /srv/btc/models/mobilenetv3/
sudo cp /srv/btc/app/ml/models/mobilenetv3/metadata.json /srv/btc/models/mobilenetv3/ 2>/dev/null || true
sudo chown -R 10001:10001 /srv/btc/models
sudo chmod 550 /srv/btc/models /srv/btc/models/mobilenetv3
sudo chmod 440 /srv/btc/models/mobilenetv3/*
# Verificar el SHA-256 contra metadata.json antes de arrancar.

# 7. Variables de entorno (nunca en Git)
sudo mkdir -p /etc/btc
sudo install -m 600 -o deploy -g deploy /srv/btc/app/.env.example /etc/btc/api.env
# Editar /etc/btc/api.env con los valores reales.
```

**Firewall de Oracle (security list / NSG):**

| Puerto | Origen | Uso |
| --- | --- | --- |
| 80/tcp | 0.0.0.0/0 (o Cloudflare) | Redirección a HTTPS / ACME |
| 443/tcp | 0.0.0.0/0 (o Cloudflare) | API y web |
| 22/tcp | Solo IP de administración / Bastion | SSH |
| 8000/tcp | No exponer | Solo red interna de Docker |

### 9.3 Caddy

```
# /srv/btc/app/Caddyfile
{
    email admin@example.com
    admin off
}

api.example.com {
    encode zstd gzip

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        Permissions-Policy "camera=(), microphone=(), geolocation=()"
        -Server
    }

    # Rate limit (requiere el módulo caddy-ratelimit). Descomentar solo
    # después de instalar el módulo; si no, Caddy no arranca.
    # rate_limit {
    #     zone dynamic {
    #         key {remote_host}
    #         events 60
    #         window 1m
    #     }
    # }

    # Grad-CAM: lo sirve FastAPI (StaticFiles) y Caddy solo lo cachea.
    reverse_proxy /static/* api:8000
    header /static/* Cache-Control "public, max-age=86400, immutable"

    # API
    reverse_proxy /api/* api:8000 {
        health_uri /api/v1/health
        health_interval 30s
        health_timeout 5s
    }

    # Documentación interactiva (opcional en producción)
    reverse_proxy /docs* api:8000
    reverse_proxy /openapi.json api:8000

    log {
        output stdout
        format json
    }
}
```

> Si no se quiere instalar el módulo de rate limit en Caddy, usar `slowapi` en
> FastAPI con límites por IP y por ruta. En ambos casos, confiar en
> `CF-Connecting-IP` solo si el origen está restringido a los rangos de
> Cloudflare; de lo contrario, un cliente puede falsificar la cabecera.
>
> **TLS con Cloudflare:** si el registro está en modo *Proxied*, usar SSL/TLS
> **Full (strict)** y un Origin Certificate instalado en Caddy; si está en
> *DNS only*, Caddy puede emitir y renovar Let's Encrypt por HTTP-01/TLS-ALPN.
> No usar Flexible: rompe el flujo y deja el origen sin cifrar.

### 9.4 Runtime de la API

| Ajuste | Valor | Motivo |
| --- | --- | --- |
| Workers de Uvicorn | 1 | Evita duplicar el modelo en RAM (~342 MB por worker) |
| `--limit-concurrency` | 4 | Encola en lugar de agotar memoria |
| `TORCH_NUM_THREADS` | 2 | Usa los 2 OCPU sin sobre-suscribir |
| `OMP_NUM_THREADS` | 2 | Consistente con torch |
| `MALLOC_ARENA_MAX` | 2 | Reduce fragmentación de memoria |
| `--timeout-keep-alive` | 30 | Suficiente para el cliente Flutter |
| `--proxy-headers` | Sí (detrás de Caddy) | Logs con IP real |
| Límite de subida | 10 MB | Ya implementado |
| Timeout de inferencia | 30 s (interno) | Evita requests colgados |
| Lock de Grad-CAM | 1 a la vez | Los hooks de PyTorch no son thread-safe |

**Mejora recomendada:** el endpoint `predict` es `async def` pero llama a
`service.predict()` de forma síncrona; eso bloquea el *event loop*. Para
permitir concurrencia real, ejecutar la inferencia en un *threadpool*
(`anyio.to_thread.run_sync`) y proteger Grad-CAM con un `threading.Lock`. Con
un solo worker y 4 solicitudes concurrentes, el tiempo de cola es aceptable
para un piloto; con 10 usuarios habría que añadir otro worker o una cola.

### 9.5 SQLite en producción

Configuración recomendada al abrir la conexión:

```python
# Ejemplo con SQLAlchemy (evento de conexión)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

**Buenas prácticas:**

- Un solo proceso escribe; las lecturas pueden ser concurrentes con WAL.
- No usar SQLite sobre NFS ni sobre un volumen de red.
- Incluir `db.sqlite3`, `db.sqlite3-wal` y `db.sqlite3-shm` en el respaldo; o
  usar `sqlite3 .backup`, que genera una copia consistente.
- Ejecutar `PRAGMA integrity_check` después de restaurar.
- Si se necesita alta disponibilidad, migrar a Postgres; SQLite no es el
  camino.

### 9.6 Almacenamiento de Grad-CAM

- Directorio: `/srv/btc/data/media/gradcam`.
- Nombre: primeros 16 hex del SHA-256 de la imagen (`<hash16>.png`), lo que
  evita colisiones prácticas y no revela el nombre original.
- Tamaño: ~100–200 KB por imagen a 224×224.
- Retención: 90 días; un cron elimina archivos sin referencia o antiguos.
- Respaldo: semanal; no es necesario respaldar todos los días si se acepta
  perder mapas recientes.
- Acceso: público con hash no adivinable en la demo; para pacientes reales,
  exigir JWT y servir con URL firmada.

### 9.7 CI/CD detallado

```yaml
name: CI/CD
on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -r backend/requirements.txt
      - run: pip install pip-audit
      - run: cd backend && python -m pytest -q
      - run: pip-audit -r backend/requirements.txt || true

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with: { flutter-version: "3.41.6", channel: stable, cache: true }
      - run: cd frontend && flutter pub get
      - run: cd frontend && flutter analyze --no-pub
      - run: cd frontend && flutter test

  image:
    if: github.event_name == 'push'
    needs: [backend, frontend]
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-qemu-action@v3
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: .
          file: backend/Dockerfile
          platforms: linux/arm64
          push: true
          tags: ghcr.io/${{ github.repository }}-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [image]
    runs-on: ubuntu-latest
    steps:
      - uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.ORACLE_HOST }}
          username: deploy
          key: ${{ secrets.ORACLE_SSH_KEY }}
          script: |
            set -euo pipefail
            cd /srv/btc/app
            PREV="$(cat .last_good 2>/dev/null || echo latest)"
            echo "${{ github.sha }}" > .last_good
            export TAG="${{ github.sha }}"
            docker compose pull
            docker compose up -d
            sleep 10
            if ! curl -fsS https://api.example.com/api/v1/health; then
              echo "Health check falló; rollback a ${PREV}"
              export TAG="${PREV}"
              docker compose up -d
              exit 1
            fi
```

**Notas:**

- El `curl` final debe fallar el job si el health check no responde; en ese
  caso, hacer rollback con el tag anterior.
- `pip-audit` no debe bloquear el pipeline al principio; primero reportar,
  luego endurecer.
- El build ARM64 con QEMU es lento; si tarda demasiado, construir en la VM o
  usar un runner ARM64.
- El paquete de GHCR debe ser **público** o la VM debe autenticarse con un PAT
  con `read:packages`. Si es privado y no hay login, `docker compose pull`
  falla. Alternativa: construir la imagen en la propia VM con
  `docker compose up -d --build`.
- Las acciones deben fijarse por SHA en la versión final.

### 9.8 Monitoreo

**UptimeRobot:**

- Monitor HTTPS `GET https://api.example.com/api/v1/health` cada 5 min.
- Keyword: `"model_ready":true`.
- Alerta por email/Telegram al equipo.
- Status page pública opcional para la sustentación.

**Sentry:**

- Backend: `sentry-sdk[fastapi]`, `traces_sample_rate=0.1`, `send_default_pii=False`.
- Flutter: `sentry_flutter`, con `beforeSend` para no enviar imágenes ni tokens.
- Alertas: nuevo issue, regresión, tasa de errores.

**Grafana Cloud (opcional):**

- Exportar métricas con `prometheus-fastapi-instrumentator` o
  `opentelemetry-instrumentation-fastapi`.
- Paneles: requests/min, p95, 5xx, memoria, CPU, disco, duración de
  inferencia, tasa de triaje no concluyente.
- No es necesario para el piloto; sí ayuda a justificar el OE3 con evidencia.

### 9.9 Capacidad y pruebas de carga

| Prueba | Configuración | Umbral |
| --- | --- | --- |
| Warm single | 1 VU, 60 s, imagen 1.5 MB | p95 < 3 s; 0 errores |
| Ramp | 0→10 VU en 2 min, 5 min estable | error < 1 %; p95 < 5 s |
| Pico | 20 VU durante 1 min | sin OOM; cola < 30 s |
| Cold start | Reiniciar el servicio y medir | < 60 s (solo Render/HF) |
| Soak | 5 VU durante 30 min | memoria estable; sin fugas |
| Subida grande | 10 MB, 4096×4096 | 201 o 413 controlado; sin crash |
| Archivo inválido | 100 requests con texto | 400; sin excepción no controlada |

La prueba de carga se ejecuta contra *staging*, no contra la demo del jurado.
Se usa k6 o Locust; el resultado se adjunta al informe de pruebas.

### 9.10 Checklist de aceptación de la arquitectura

- [ ] La API responde por HTTPS con un certificado válido.
- [ ] `/health` devuelve `model_ready=true` después de reiniciar la VM.
- [ ] Una predicción sobrevive a un reinicio y aparece en `/history`.
- [ ] El Grad-CAM sigue accesible después de un reinicio.
- [ ] El login/refresh/logout funciona con `JWT_SECRET` de producción.
- [ ] El APK apunta a la nueva URL y clasifica en línea.
- [ ] El modo offline sigue funcionando y sincroniza al reconectar.
- [ ] El respaldo diario se ejecuta y se verificó un restore.
- [ ] UptimeRobot alerta si se detiene la API.
- [ ] No hay secretos en el repositorio ni en logs.
- [ ] El firewall no expone 8000 ni SSH al mundo.
- [ ] La factura de Oracle permanece en $0.

---

## 10. Plan de migración desde Render

### 10.1 Fases

| Fase | Duración | Actividades | Criterio de salida |
| --- | --- | --- | --- |
| F0. Preparación | 2–3 días | Inventario de variables, endpoints, datos y URLs; backup lógico del historial; congelar cambios de esquema | Inventario aprobado; backup descargado |
| F1. Infraestructura | 3–5 días | Crear VM, volumen, firewall, Docker, Caddy; desplegar API con DB vacía; probar health y predict | API responde en staging con modelo real |
| F2. Datos | 1–2 días | Importar historial/feedback; copiar media si existe; verificar conteos y hashes | Historial y detalle consistentes |
| F3. Corte | 1 día | Bajar TTL del DNS; cambiar `API_BASE_URL`; desplegar APK/web; smoke tests | App móvil y web usan la nueva API |
| F4. Estabilización | 1 semana | Monitoreo, backups, carga, corrección de incidencias | 7 días sin incidentes S1/S2 |
| F5. Retiro | 1 día | Apagar Render; archivar configuración; actualizar docs | Render desactivado; runbook actualizado |

### 10.2 Migración de datos

Render Free no ofrece shell ni acceso directo al archivo SQLite. Opciones:

1. **Exportar vía API (recomendado para el historial):**
   - `GET /api/v1/history?limit=100&offset=...` para las filas planas.
   - `GET /api/v1/predictions/{id}` para probabilidades, imagen, modelo y
     feedback.
   - Generar un JSON/CSV y un script de importación idempotente.
   - Limitación: las imágenes originales no se guardan (solo hash), así que
     los Grad-CAM antiguos no se pueden regenerar; si los archivos ya se
     perdieron por un *spin-down*, no hay nada que migrar.
2. **Endpoint temporal de exportación:**
   - Añadir `GET /api/v1/admin/export` protegido por un token temporal y
     limitado a la IP del equipo.
   - Devolver un ZIP con `db.sqlite3` (copia `.backup`) y `media/`.
   - Desplegar, descargar, eliminar el endpoint y rotar el token.
   - Es la única forma de conservar Grad-CAM si aún existen en el disco.
3. **Aceptar la pérdida del historial de demo:** es válido si se documenta y
   se comunica; el historial no es un requisito clínico y los datos son de
   prueba.

**Script de importación (esquema):**

```python
# tools/import_history.py (pseudo-código)
import json, sqlite3, hashlib
from pathlib import Path

data = json.loads(Path("export.json").read_text())
con = sqlite3.connect("/srv/btc/data/db.sqlite3")
for row in data["predictions"]:
    # insertar/actualizar imagen por hash, modelo, clase, predicción y scores
    # usar INSERT ... ON CONFLICT para que sea idempotente
    ...
con.commit()
```

### 10.3 Corte de DNS y frontend

1. Bajar el TTL del registro `api.example.com` a 300 s al menos 24 h antes.
2. Crear el registro A hacia la IP pública de Oracle (o CNAME a Cloudflare).
3. Verificar TLS y health desde fuera de la red del equipo.
4. Actualizar la variable `API_BASE_URL` en GitHub Actions a
   `https://api.example.com/api/v1`.
5. Recompilar el APK y publicar un tag `v1.1.0`; verificar la instalación en un
   dispositivo limpio.
6. Rebuild de Flutter Web en Cloudflare Pages con la nueva URL.
7. Mantener Render activo en paralelo 48–72 h; comparar respuestas.

### 10.4 Rollback

| Escenario | Acción | Tiempo |
| --- | --- | --- |
| La API nueva no responde | DNS de vuelta a Render; el APK anterior sigue funcionando | < 15 min |
| Datos inconsistentes | Restaurar backup previo; reimportar | < 2 h |
| Modelo no carga | Revisar `MODEL_PATH`, permisos y SHA-256; volver al tag anterior | < 30 min |
| TLS falla | Cambiar Cloudflare a “DNS only”; renovar certificado con Caddy | < 30 min |
| Costo inesperado | Apagar recursos pagados; volver a Render Free | < 1 h |

**Regla:** no borrar Render hasta que la nueva API haya pasado 7 días de
monitoreo y un simulacro de restore.

### 10.5 Actualización de documentación y APK

- `README.md`: nueva URL, comandos de despliegue, variables.
- `docs/arquitectura-cloud.md`: este documento.
- `docs/pruebas-software.md`: evidence de smoke tests post-migración.
- `.github/workflows/android-release.yml`: variable `API_BASE_URL` y timeout.
- `frontend/lib/core/config.dart`: mantener el default de desarrollo, no la URL
  de producción.
- `docs/scrum/sprints.md`: registrar la migración como deuda técnica saldada.

---

## 11. Costos y sostenibilidad

### 11.1 Costo mensual de la opción A

| Recurso | Capa gratuita | Uso estimado | Costo |
| --- | --- | --- | --- |
| Oracle A1 2 OCPU / 3 GB | 1.500 OCPU-h / 9.000 GB-h | 1.460 / 2.190 | $0 |
| Block Volume 150 GB | 200 GB | 150 GB | $0 |
| Object Storage | 20 GB | < 5 GB | $0 |
| Egreso | 10 TB | < 5 GB | $0 |
| Cloudflare DNS/Pages | Free | — | $0 |
| GitHub Actions/Releases | Repo público | ~200 min/mes | $0 |
| UptimeRobot | Free | 2 monitores | $0 |
| Sentry | Developer | < 5k errores | $0 |
| Dominio (opcional) | — | ~$10–15/año | ~$1/mes |
| **Total** | | | **$0–$1/mes** |

### 11.2 Comparación a 12 meses

| Opción | Costo 12 meses | Operación | Persistencia | Riesgo principal |
| --- | ---: | --- | --- | --- |
| A. Oracle Always Free | $0 (+ dominio) | Media | Sí | Capacidad/reclamación |
| B. Render + Neon + R2 | $0 | Baja | Sí (externa) | RAM 512 MB / *sleep* |
| C. Modal + Neon + R2 | $0–$360 | Baja | Sí (externa) | Créditos/cold start |
| D. HF PRO + Neon + R2 | $108 | Muy baja | Sí (externa) | $9/mes; *sleep* 48 h |
| E. GCP e2-micro | $0 | Media | Sí | 1 GB RAM; 1 GB egreso |
| Render Starter + Postgres | ~$156+ | Baja | Sí | Costo mensual |

### 11.3 Cuándo pagar

| Disparador | Umbral | Acción |
| --- | --- | --- |
| Predicciones | > 30.000/mes | Evaluar Modal/Neon Launch o Render Standard |
| Base de datos | > 1 GB | Migrar a Postgres gestionado |
| Grad-CAM | > 10 GB | R2 + lifecycle o retención 30 días |
| Concurrencia | > 10 usuarios simultáneos | 2 workers + 4 GB o segunda VM |
| Disponibilidad | SLA > 99.5 % | Load balancer + 2 instancias + Postgres HA |
| Clínico | Cualquier paciente real | Presupuesto de compliance y validación |

### 11.4 Guardarraíles de costo

- Crear un presupuesto de $0 en Oracle/GCP y alertas al 50/80/100 %.
- Etiquetar todos los recursos (`project=brain-tumor`, `env=demo`).
- Revisar la factura el primer día de cada mes.
- No dejar instancias A1 adicionales encendidas.
- No usar GPUs ni servicios managed sin aprobación.
- Apagar recursos de prueba al terminar.
- Documentar cualquier gasto aprobado por el PO.

---

## 12. Operación, SLOs y runbooks

### 12.1 Rutina operativa

| Frecuencia | Tarea | Responsable |
| --- | --- | --- |
| Diaria (automática) | Backup DB + media; health check | Cron / UptimeRobot |
| Semanal | Revisar errores en Sentry; verificar disco; revisar backups | Ops |
| Semanal | Revisar issues de dependencias (Dependabot/pip-audit) | Dev |
| Mensual | Revisar factura; aplicar parches; probar restore | Ops |
| Trimestral | Simulacro de recuperación; revisión de accesos | Ops + PO |
| Por release | Tests, build, deploy, smoke, rollback plan | Dev + QA |

### 12.2 Runbooks

#### API caída

1. `curl -v https://api.example.com/api/v1/health`.
2. `ssh deploy@vm` (por Bastion/VPN) y `docker compose ps`.
3. `docker compose logs --tail=200 api`.
4. Si el contenedor reinicia: revisar OOM (`dmesg | tail`), `MODEL_PATH`,
   permisos del volumen y espacio en disco.
5. Si el modelo no carga: verificar SHA-256 y `metadata.json`.
6. Si el fallo es de red/TLS: revisar Caddy (`journalctl -u caddy`), DNS y
   firewall.
7. Si no se resuelve en 30 min: restaurar el tag anterior y, si es crítico,
   conmutar DNS a Render.

#### Disco lleno

1. `df -h /srv/btc`; `du -sh /srv/btc/*`.
2. Limpiar Grad-CAM antiguos según retención.
3. Rotar logs de Caddy/Docker.
4. Ampliar el volumen si es recurrente (hasta 200 GB Always Free).
5. Verificar que la DB no haya crecido por un bucle de feedback.

#### Base de datos bloqueada

1. `sqlite3 /srv/btc/data/db.sqlite3 "PRAGMA busy_timeout;"`.
2. Verificar procesos que escriben y requests concurrentes.
3. Comprobar que WAL está activo (`PRAGMA journal_mode;`).
4. Si persiste, reiniciar la API y, si es necesario, restaurar el backup.
5. Plan de migración a Postgres si ocurre más de una vez al mes.

#### Latencia alta

1. Revisar `inference_ms` en logs y CPU/memoria.
2. Verificar que no haya dos workers duplicando el modelo.
3. Reducir concurrencia (`--limit-concurrency`) o aumentar RAM/OCPU.
4. Evaluar ONNX Runtime para el backend (menor huella, sin gradientes).
5. Si el pico es por Grad-CAM, hacerlo opcional o asíncrono.

#### Incidente de seguridad

1. Rotar `JWT_SECRET` (invalida todas las sesiones).
2. Revocar refresh tokens en `auth_sessions`.
3. Revisar logs de acceso y Sentry.
4. Aislar la VM (security list sin 80/443) si hay compromiso.
5. Restaurar desde un backup anterior al incidente.
6. Documentar causa, impacto y acciones; notificar al PO.

### 12.3 Gestión de cambios

- Todo cambio de infraestructura va en un PR con `docker-compose.yml`,
  `Caddyfile` o workflow actualizado.
- Los cambios de esquema requieren migración (Alembic) y backup previo.
- Los cambios de modelo requieren `metadata.json`, SHA-256 y una prueba de
  inferencia con una imagen de referencia.
- Los cambios de contrato requieren actualizar `docs/` y las pruebas.
- No se hacen cambios manuales en la VM sin registrarlos en el PR o runbook.

---

## 13. Riesgos y mitigaciones

| # | Riesgo | P | I | Mitigación |
| --- | --- | --- | --- | --- |
| R1 | Oracle no entrega capacidad A1 en la región | M | A | Reintentar en otra AD; usar Render+Neon+R2 como plan B |
| R2 | Oracle reclama la instancia por inactividad | M | A | Dimensionar 3 GB para superar el 20 % de memoria; uso real; backups; monitoreo |
| R3 | PyTorch ARM64 no tiene wheel para alguna dependencia | B | A | Probar el build arm64 temprano; fallback a ONNX Runtime o GCP x86 |
| R4 | OOM por concurrencia o Grad-CAM | M | A | 3–4 GB; 1 worker; límite de concurrencia; lock de Grad-CAM; monitoreo |
| R5 | Corrupción de SQLite | B | A | WAL, backups diarios, `integrity_check`, migrar a Postgres si escala |
| R6 | Pérdida de Grad-CAM por backup incompleto | M | M | Incluir `media/` en el backup; verificar restore |
| R7 | Cambio de plan gratuito | M | M | Backups, imagen Docker, runbook de migración |
| R8 | Fuga de secreto JWT | B | C | Secretos fuera de Git; rotación; escaneo; mínimo privilegio |
| R9 | Subida maliciosa/DoS | M | M | Límite 10 MB, validación, rate limit, timeout, Cloudflare |
| R10 | Deriva del modelo o métricas desactualizadas | M | M | Re-evaluar `best.pt` con `run_all.py --skip-train`; versionar |
| R11 | Baja disponibilidad por una sola VM | M | A | SLO 99 %; backups; plan de conmutación; no prometer 99.9 % |
| R12 | Costo inesperado | B | M | Presupuesto $0, alertas, etiquetas, revisión mensual |
| R13 | Rotación del equipo | M | M | Documentación, runbook, infraestructura como código |
| R14 | Uso clínico sin validación | B | C | Aviso, disclaimers, bloqueo de uso real, comité de ética |

> **P** = probabilidad; **I** = impacto. **A** = alta, **M** = media, **B** = baja, **C** = crítica.

---

## 14. Conclusiones

1. **La arquitectura actual es una demo, no un servicio persistente.** Render
   Free pierde SQLite y Grad-CAM en cada *spin-down*; eso es incompatible con
   un historial confiable.
2. **El límite de 512 MB es el factor decisivo.** La medición de 342 MB con
   MobileNetV3 deja poco margen; cualquier concurrencia o modelo mayor agrava
   el riesgo.
3. **Oracle Cloud Always Free es la mejor opción $0 para este proyecto.**
   Ofrece 2 OCPU, 12 GB y 200 GB, suficiente para PyTorch, Grad-CAM y
   persistencia, a cambio de operar una VM.
4. **La cuota de Oracle es finita y hay que respetarla.** 2 OCPU siempre
   encendidos consumen el 97,3 % de la bolsa mensual; 3 GB de RAM consumen el
   24,3 %. No se debe crear una segunda instancia A1.
5. **La recuperación por inactividad es un riesgo real.** Dimensionar 3 GB
   mantiene el uso de memoria por encima del 20 % y reduce la probabilidad de
   reclamación; aun así, se necesitan backups y un plan B.
6. **Render + Neon + R2 sigue siendo un buen plan de continuidad.** Es la
   opción de mínimo esfuerzo si Oracle falla o si el equipo no puede operar una
   VM, pero no resuelve el límite de RAM.
7. **Hugging Face Spaces ya no es gratis para Docker.** Es una buena opción de
   $9/mes si se prioriza simplicidad y no se quiere administrar servidor.
8. **El costo no es la barrera en el rango académico.** Con 3.000–30.000
   predicciones/mes, la opción A cuesta $0; el costo real es el tiempo de
   operación y la disciplina de backups.
9. **La seguridad y la privacidad se mantienen.** Solo hash, sin PHI, JWT con
   refresh rotativo, HTTPS, rate limit y backups cifrados; el uso clínico real
   exige un proyecto regulatorio aparte.
10. **La migración es viable en 2–3 semanas.** Fases claras, rollback a Render
    y criterios de aceptación medibles; el riesgo principal es la capacidad de
    Oracle, no el código.

---

## 15. Criterios de aceptación y trabajo futuro

### 15.1 Criterios de aceptación de la propuesta

- [ ] La arquitectura cabe en la capa gratuita y está justificada con números.
- [ ] Cada componente tiene un proveedor, un límite y un plan B.
- [ ] La persistencia de SQLite y Grad-CAM está resuelta.
- [ ] El costo mensual estimado es $0 (o $9 si se elige HF PRO).
- [ ] Hay un plan de migración con rollback.
- [ ] Hay controles de seguridad y privacidad mínimos.
- [ ] Hay SLOs, alertas y runbooks.
- [ ] La decisión está registrada como ADR y es revisable.

### 15.2 Trabajo futuro

1. Implementar el `docker-compose.yml` y el `Caddyfile` en un branch de
   infraestructura.
2. Añadir el job de backend y el build ARM64 al workflow de GitHub Actions.
3. Medir la latencia real en Oracle con k6 y ajustar workers/RAM.
4. Migrar SQLite a Postgres si se superan 10 usuarios concurrentes o 30.000
   predicciones/mes.
5. Añadir autenticación a `/static` si se manejan datos clínicos reales.
6. Instrumentar OpenTelemetry/Prometheus y paneles en Grafana Cloud.
7. Evaluar ONNX Runtime en el backend para reducir RAM y latencia.
8. Documentar el proceso de aprobación de gastos y el responsable de costos.
9. Revisar la capa gratuita cada 6 meses; las condiciones cambian.
10. Si el proyecto pasa a uso clínico, iniciar el camino regulatorio
    (IEC 62304, ISO 14971, ISO 13485, SaMD) y la validación con radiólogos.

---

## 16. Referencias

Todas las fuentes de planes y capas gratuitas se consultaron el **13 de
noviembre de 2026**. Los precios y límites pueden cambiar; la fecha de consulta
es parte de la evidencia.

### 16.1 Proveedores y planes

1. Oracle Cloud Infrastructure. *Always Free Resources.*
   https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
2. Render. *Deploy for Free.* https://render.com/docs/free
3. Render. *Pricing.* https://render.com/pricing
4. Hugging Face. *Spaces Overview.*
   https://huggingface.co/docs/hub/en/spaces-overview
5. Hugging Face. *Pricing.* https://huggingface.co/pricing
6. Neon. *Plans.* https://neon.com/docs/introduction/plans
7. Supabase. *Pricing.* https://supabase.com/pricing
8. Cloudflare. *R2 Pricing.* https://developers.cloudflare.com/r2/pricing/
9. Cloudflare. *Pages Limits.*
   https://developers.cloudflare.com/pages/platform/limits/
10. GitHub. *Actions billing.*
    https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions
11. Modal. *Pricing.* https://modal.com/pricing
12. Railway. *Pricing.* https://railway.com/pricing
13. Google Cloud. *Free Tier.*
    https://cloud.google.com/free/docs/free-cloud-features
14. Koyeb. *Pricing FAQ.* https://www.koyeb.com/docs/faqs/pricing
15. UptimeRobot. *Pricing.* https://uptimerobot.com/pricing/
16. Sentry. *Pricing.* https://sentry.io/pricing/
17. Grafana Labs. *Pricing.* https://grafana.com/pricing/

### 16.2 Arquitectura, seguridad y operación

18. NIST. *SP 800-145: The NIST Definition of Cloud Computing.* 2011.
19. NIST. *SP 800-190: Application Container Security Guide.* 2017.
20. OWASP. *Application Security Verification Standard (ASVS).*
    https://owasp.org/www-project-application-security-verification-standard/
21. OWASP. *Top 10.* https://owasp.org/www-project-top-ten/
22. ISO/IEC 25010. *Systems and software Quality Requirements and Evaluation
    (SQuaRE) — Quality models.*
23. Google. *Site Reliability Engineering.* O'Reilly, 2016.
24. The Twelve-Factor App. https://12factor.net/
25. Caddy. *Documentation.* https://caddyserver.com/docs/
26. Docker. *Compose specification.* https://docs.docker.com/compose/

### 16.3 Documentación del proyecto

27. `README.md` — arquitectura, contrato, puesta en marcha, offline y APK.
28. `docs/informe-universitario.md` — informe académico y resultados.
29. `docs/mejora-capa-seguridad-clinica.md` — triaje por confianza y margen.
30. `docs/scrum/definition-of-done.md` — criterios de calidad del proyecto.
31. `docs/scrum/sprints.md` — historial de sprints y deuda técnica.
32. `docs/pruebas-software.md` — plan y evidencia de pruebas.

---

## 17. Anexos

### Anexo A — Variables de entorno de producción

```env
APP_NAME="Brain Tumor Classification API"
API_V1_PREFIX=/api/v1
MODEL_PATH=/data/models/mobilenetv3/best.pt
MODEL_VERSION=mobilenetv3-v1
IMAGE_SIZE=224
ENABLE_GRADCAM=true

DATABASE_URL=sqlite:////data/db.sqlite3
MEDIA_ROOT=/data/media
MAX_UPLOAD_BYTES=10485760

JWT_SECRET=<32+ bytes aleatorios>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

CORS_ORIGINS=["https://app.example.com"]
CORS_ORIGIN_REGEX=""

CLINICAL_CONFIDENCE_THRESHOLD=0.70
CLINICAL_MARGIN_THRESHOLD=0.10
CLINICAL_HIGH_CONFIDENCE_THRESHOLD=0.90

SENTRY_DSN=<opcional>
TZ=UTC
```

### Anexo B — Compose completo de referencia

```yaml
name: btc

services:
  api:
    image: ghcr.io/sonedxe/brain-tumor-classification-api:${TAG:-latest}
    build:
      context: .
      dockerfile: backend/Dockerfile
      platforms: [linux/arm64]
    env_file: /etc/btc/api.env
    environment:
      HOME: /tmp
      TORCH_HOME: /tmp/torch
    volumes:
      - /srv/btc/data:/data:rw
      - /srv/btc/models:/data/models:ro
    expose: ["8000"]
    mem_limit: 2g
    cpus: 1.8
    restart: unless-stopped
    read_only: true
    tmpfs: ["/tmp:size=256m"]
    security_opt: ["no-new-privileges:true"]
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 90s

  caddy:
    image: caddy:2.8-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    depends_on: [api]

volumes:
  caddy_data:
  caddy_config:
```

### Anexo C — Script de backup

```bash
#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date -u +%Y%m%d)"
DATA="/srv/btc/data"
BACKUPS="/srv/btc/backups"
REMOTE="remote:btc-backups/${STAMP}"
mkdir -p "${BACKUPS}/${STAMP}"

# SQLite consistente
sqlite3 "${DATA}/db.sqlite3" ".backup '${BACKUPS}/${STAMP}/db.sqlite3'"
sqlite3 "${BACKUPS}/${STAMP}/db.sqlite3" "PRAGMA integrity_check;"

# Grad-CAM
tar -czf "${BACKUPS}/${STAMP}/media.tar.gz" -C "${DATA}" media/gradcam

# Checksums y cifrado
cd "${BACKUPS}/${STAMP}"
sha256sum db.sqlite3 media.tar.gz > SHA256SUMS
age -r "${AGE_PUBLIC_KEY}" -o db.sqlite3.age db.sqlite3
age -r "${AGE_PUBLIC_KEY}" -o media.tar.gz.age media.tar.gz
rm db.sqlite3 media.tar.gz

# Subida y retención
rclone copy "${BACKUPS}/${STAMP}" "${REMOTE}"
find "${BACKUPS}" -mindepth 1 -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +
```

Programar en cron (como usuario `deploy`):

```cron
0 3 * * * /srv/btc/app/scripts/backup.sh >> /var/log/btc-backup.log 2>&1
```

### Anexo D — Checklist de seguridad para el despliegue

- [ ] `JWT_SECRET` aleatorio y distinto de desarrollo.
- [ ] HTTPS con HSTS y TLS 1.2+.
- [ ] CORS restringido al dominio real.
- [ ] Rate limit en `/auth/*` y `/predict`.
- [ ] Validación de imagen y límite de 10 MB.
- [ ] Contenedor no-root, `read_only`, `no-new-privileges`.
- [ ] Firewall: solo 80/443; SSH por Bastion/VPN.
- [ ] Backups cifrados y restore probado.
- [ ] `pip-audit` y Trivy sin críticos/altos.
- [ ] Logs sin PHI, tokens ni imágenes.
- [ ] Alertas de salud, 5xx, disco y memoria.
- [ ] Documento de incidentes y contactos.
- [ ] Revisión de accesos y rotación de claves cada 90 días.

### Anexo E — Glosario

| Término | Definición |
| --- | --- |
| **Always Free** | Recursos gratuitos permanentes de Oracle, sujetos a cuota y reclamación por inactividad |
| **Cold start** | Tiempo que tarda un servicio dormido en atender el primer request |
| **Ephemeral filesystem** | Disco que se pierde al reiniciar/redeployar |
| **Grad-CAM** | Mapa de calor que resalta las regiones que más influyen en la predicción |
| **OOM** | *Out of memory*; el proceso muere por falta de RAM |
| **RPO** | *Recovery Point Objective*: cuántos datos se pueden perder |
| **RTO** | *Recovery Time Objective*: cuánto tarda la recuperación |
| **SLO / SLI** | Objetivo y indicador de nivel de servicio |
| **SQLite WAL** | Modo de journaling que permite lecturas concurrentes con un escritor |
| **Spin-down** | Suspensión automática de un servicio por inactividad |
| **Triaje clínico** | Clasificación de riesgo y recomendación de derivación según confianza/margen |

---

**Fin del documento.**

