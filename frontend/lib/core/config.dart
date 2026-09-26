/// Configuracion de la capa de presentacion.
///
/// MVVM: aqui viven valores de entorno, nunca logica de negocio ni llamadas
/// HTTP. Las vistas y los ViewModel no deben conocer la URL del backend.
library;

class AppConfig {
  const AppConfig._();

  /// Base de la API v1.
  ///
  /// 10.0.2.2 es el alias que el emulador de Android usa para alcanzar el
  /// host. En el simulador de iOS es `localhost`, y en un dispositivo fisico
  /// la IP local de la maquina, por lo que se inyecta en tiempo de ejecucion:
  ///
  /// ```
  /// flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
  /// ```
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  static const Duration requestTimeout = Duration(seconds: 30);
  static const int maxImageBytes = 10 * 1024 * 1024;
  static const String appTitle = 'Clasificacion de tumores cerebrales';
}
