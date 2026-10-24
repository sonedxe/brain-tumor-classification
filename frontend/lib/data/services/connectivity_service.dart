import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

/// Estado de conectividad de la app.
///
/// En pruebas nunca toca el canal de plataforma: `initialize()` es lo unico
/// que se suscribe al plugin, y por defecto el estado es "online".
class ConnectivityService extends ChangeNotifier {
  ConnectivityService();

  static final ConnectivityService instance = ConnectivityService();

  bool _online = true;
  StreamSubscription<List<ConnectivityResult>>? _subscription;
  final StreamController<bool> _onlineController =
      StreamController<bool>.broadcast();

  bool get isOnline => _online;
  bool get isOffline => !_online;

  /// Emite `true` cada vez que se recupera la conexión (para sincronizar).
  Stream<bool> get onlineChanges => _onlineController.stream;

  Future<void> initialize() async {
    if (_subscription != null) {
      return;
    }
    try {
      final results = await Connectivity().checkConnectivity();
      _set(_hasConnection(results));
      _subscription = Connectivity()
          .onConnectivityChanged
          .listen((results) => _set(_hasConnection(results)));
    } on Exception catch (error) {
      // Si el plugin no esta disponible, se asume online y se deja que las
      // peticiones HTTP fallen y activen el fallback offline.
      debugPrint('ConnectivityService no disponible: $error');
      _set(true);
    }
  }

  /// Fuerza el estado; util para pruebas y para el boton "reintentar".
  void setOnlineForTesting(bool online) => _set(online);

  bool _hasConnection(List<ConnectivityResult> results) =>
      results.any((result) => result != ConnectivityResult.none);

  void _set(bool online) {
    if (_online == online) {
      return;
    }
    _online = online;
    notifyListeners();
    _onlineController.add(online);
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _onlineController.close();
    super.dispose();
  }
}
