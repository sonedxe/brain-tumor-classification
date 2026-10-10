# App Flutter — Clasificación de tumores cerebrales

Cliente móvil con arquitectura **MVVM** que consume la API del backend.

## Arquitectura

```
lib/
├── core/            # config (URL de la API) y tema
├── data/
│   ├── models/      # DTOs (PredictionModel, HistoryEntry)
│   ├── repositories/# une modelo + servicio
│   └── services/    # ApiService y AuthService (único punto HTTP)
├── viewmodels/      # estado + reglas (Prediction, History, Auth)
├── views/           # pantallas (Analizar, Historial, Info, Cuenta)
└── widgets/         # componentes de presentación reutilizables
```

Regla de oro: **ninguna vista hace HTTP, parsea JSON ni lee archivos**. La
vista observa el ViewModel y emite intents; el ViewModel usa un repository
inyectable, lo que permite probarlo con un `MockClient`.

## Pantallas consolidadas

`AppShell` reúne cuatro pantallas con un `NavigationBar` y `IndexedStack`:
Analizar, Historial, Info y Cuenta. Ver `docs/diseno-pantallas.md` en la raíz.

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
