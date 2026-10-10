# Diseno de pantallas (Flutter)

Pantallas consolidadas de la aplicacion movil, su estado por pantalla y su
correspondencia con la arquitectura MVVM. Evidencia el punto "interaccion y
diseno de pantallas consolidadas en Flutter".

## Navegacion general

`AppShell` (`frontend/lib/views/app_shell.dart`) concentra la navegacion con un
`NavigationBar` de cuatro destinos. Las pantallas se mantienen vivas con un
`IndexedStack`, de modo que no se pierde el estado al cambiar de pestana (por
ejemplo, la imagen ya elegida en "Analizar").

```
┌──────────────────────────────────────────┐
│  AppBar: titulo de la pestana actual      │
├──────────────────────────────────────────┤
│                                          │
│            (cuerpo de la vista)          │
│                                          │
├──────────────────────────────────────────┤
│ Analizar | Historial | Info | Cuenta      │
└──────────────────────────────────────────┘
```

## 1. Analizar (HomeView)

- **Archivo:** `lib/views/home_view.dart`
- **Proposito:** elegir una MRI, clasificarla y ver el resultado.
- **Estados:**
  - `idle` — sin imagen: se ofrecen "Elegir de la galeria" y "Tomar una foto".
  - `imagen elegida` — vista previa + boton "Clasificar".
  - `loading` — boton deshabilitado con indicador "Analizando...".
  - `success` — `ResultCard` con etiqueta, confianza, probabilidades y Grad-CAM.
  - `error` — banner rojo con el mensaje normalizado.
- **ViewModel:** `PredictionViewModel` (estado + intents).
- **Widgets:** `ImagePickerButton`, `ResultCard`.

## 2. Historial (HistoryView)

- **Archivo:** `lib/views/history_view.dart`
- **Proposito:** listar las ultimas predicciones (`GET /history`).
- **Estados:**
  - `loading` — indicador centrado.
  - `success` con datos — lista de tarjetas (etiqueta, confianza, modelo, fecha).
  - `success` vacio — mensaje "Aun no hay predicciones".
  - `error` — mensaje + boton "Reintentar".
  - Todos los estados admiten pull-to-refresh.
- **ViewModel:** `HistoryViewModel`.
- **Nota MVVM:** la vista NO hace HTTP ni parsea JSON; eso ocurre en
  `HistoryRepository`/`ApiService`.

## 3. Info (InfoView)

- **Archivo:** `lib/views/info_view.dart`
- **Proposito:** contenido educativo de las cuatro clases (RF-06).
- **Estado:** estatico, sin backend. Solo lectura + tema.
- **ViewModel:** ninguno (no hay estado que cambiar).

## 4. Cuenta (AuthView)

- **Archivo:** `lib/views/auth_view.dart`
- **Proposito:** login/registro opcional (RF-01/02/03). La clasificacion
  funciona sin cuenta.
- **Estados:** formulario (login o registro) / sesion activa.
- **ViewModel:** `AuthViewModel`.
- **Endpoints:** `POST /auth/register`, `POST /auth/login` (modo mock).

## Pantallas auxiliares

- **ResultView** (`lib/views/result_view.dart`): detalle del resultado,
  reutilizable si mas adelante se abre desde el historial. Comparte el
  `PredictionViewModel`, no duplica estado.

## Correspondencia MVVM

| Capa | Ubicacion | Responsabilidad |
| --- | --- | --- |
| Model (DTO) | `lib/data/models/` | Contrato de datos puro |
| Repository | `lib/data/repositories/` | Une modelo y servicio |
| Service | `lib/data/services/` | Unico punto que conoce la URL/HTTP |
| ViewModel | `lib/viewmodels/` | Estado, reglas y notificacion |
| View | `lib/views/` + `lib/widgets/` | Presentacion y captura de intents |
| Tema | `lib/core/theme.dart` | Colores y tipografia centralizados |

El flujo de una accion es siempre:

```
View  --intent-->  ViewModel  --peticion-->  Repository  -->  Service  --> API
  ^                                                                        |
  └───────────────── notifyListeners() <── estado <───────────────────────┘
```

## Tema y accesibilidad

- Un unico `AppTheme` (Material 3) con `seedColor` azul (`0xFF0F4C81`).
- Colores por clase centralizados en `AppTheme.classColors` (no se repiten en
  las vistas).
- Aviso medico visible en `ResultCard` (`_Disclaimer`).
