# App Flutter — Clasificación de tumores cerebrales

Cliente móvil con arquitectura **MVVM** que consume la API del backend.

## Arquitectura

```
lib/
├── core/            # config (URL de la API), tema y contrato del modelo
├── data/
│   ├── local/       # almacén offline (caché, cola de sync, cuentas)
│   ├── models/      # DTOs (PredictionModel, HistoryEntry, StatsSummary, PredictionDetail)
│   ├── repositories/# une modelo + servicio
│   └── services/    # HTTP, ONNX local, conectividad y sincronización
├── viewmodels/      # estado + reglas (Prediction, History, Stats, Detail, Auth)
├── views/           # pantallas (Analizar, Historial, Panel, Info, Cuenta, Detalle)
└── widgets/         # componentes de presentación reutilizables
```

Regla de oro: **ninguna vista hace HTTP, parsea JSON ni lee archivos**. La
vista observa el ViewModel y emite intents; el ViewModel usa un repository
inyectable, lo que permite probarlo con un `MockClient`.

## Pantallas consolidadas

`AppShell` reúne cinco pantallas con un `NavigationBar` y `IndexedStack`:
Analizar, Historial, Panel, Info y Cuenta. El Historial abre `PredictionDetailView`
(detalle + feedback humano). Ver `docs/diseno-pantallas.md` en la raíz.

## Modo offline

`assets/models/model.onnx` es una copia del `best.pt` del backend. Si no hay
conexión (o el backend no responde), `OfflineService` clasifica con
`OnnxPredictor` y guarda la imagen y el resultado en `LocalDB`; al reconectar,
`SyncService` reenvía la cola a la API. Regenerar el modelo:

```bash
backend/.venv/bin/python ml/export_mobile_onnx.py --model mobilenetv3 --verify
```

## Ejecutar

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

`10.0.2.2` es el alias del host desde el emulador de Android. En iOS Simulator
usar `http://localhost:8000/api/v1`; en dispositivo físico, la IP local.

## Pruebas

```bash
flutter analyze
flutter test
```

Las pruebas cubren el parseo de los DTOs, el contrato de `ApiService` y la
lógica de los ViewModels con un `MockClient` de `package:http/testing`.
