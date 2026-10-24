import 'dart:async';

import 'package:image_picker/image_picker.dart' show XFile;

import '../local/local_db.dart';
import 'api_service.dart';
import 'auth_service.dart';
import 'connectivity_service.dart';
import 'session_store.dart';

/// Sincroniza con el backend todo lo producido sin conexión.
///
/// Orden: cuentas pendientes -> feedback en cola -> predicciones pendientes.
/// Las predicciones se reenvían con su imagen original, de modo que el backend
/// vuelve a inferir y guarda el registro con su `id` real.
class SyncService {
  SyncService({
    required LocalDB db,
    ApiService? apiService,
    AuthService? authService,
    SessionStore? sessionStore,
  })  : _db = db,
        _apiService = apiService ?? ApiService(),
        _authService = authService ?? AuthService(),
        _sessionStore = sessionStore ?? SharedPreferencesSessionStore();

  final LocalDB _db;
  final ApiService _apiService;
  final AuthService _authService;
  final SessionStore _sessionStore;

  StreamSubscription<bool>? _subscription;
  bool _running = false;

  /// Escucha la conectividad y sincroniza automáticamente al reconectar.
  void attach(ConnectivityService connectivity) {
    _subscription ??= connectivity.onlineChanges.listen((online) {
      if (online) {
        unawaited(syncNow());
      }
    });
  }

  Future<SyncResult> syncNow() async {
    if (_running || ConnectivityService.instance.isOffline) {
      return const SyncResult.empty();
    }
    _running = true;
    var accounts = 0;
    var predictions = 0;
    var feedback = 0;
    try {
      accounts = await _syncAccounts();
      feedback = await _syncFeedback();
      predictions = await _syncPredictions();
    } on Exception {
      // Un fallo de red deja la cola intacta para el siguiente intento.
    } finally {
      _running = false;
    }
    return SyncResult(
      accounts: accounts,
      predictions: predictions,
      feedback: feedback,
    );
  }

  Future<int> _syncAccounts() async {
    final pending =
        (await _db.readAccounts()).where((a) => a.pendingSync).toList();
    var synced = 0;
    for (final account in pending) {
      try {
        final data = await _authService.register(
          account.name,
          account.email,
          account.password,
        );
        await _persistSession(data, account.name.isEmpty ? account.email : account.name);
        await _db.saveAccount(account.copyWith(pendingSync: false));
        synced++;
      } on ApiException catch (error) {
        // La cuenta ya existe en el backend: se intenta iniciar sesión.
        if (error.statusCode == 400 || error.statusCode == 409) {
          try {
            final data = await _authService.login(
              account.email,
              account.password,
            );
            await _persistSession(
              data,
              account.name.isEmpty ? account.email : account.name,
            );
            await _db.saveAccount(account.copyWith(pendingSync: false));
            synced++;
          } on ApiException {
            // Credenciales distintas: se conserva para revisión manual.
          }
        }
      }
    }
    return synced;
  }

  Future<void> _persistSession(
    Map<String, dynamic> data,
    String fallbackName,
  ) async {
    final token = data['access_token'] as String?;
    if (token == null || token.isEmpty) {
      return;
    }
    await _sessionStore.save(
      token: token,
      name: (data['name'] as String?) ?? fallbackName,
    );
  }

  Future<int> _syncFeedback() async {
    final queue = await _db.readFeedbackQueue();
    var synced = 0;
    for (final item in queue) {
      try {
        await _apiService.sendFeedback(
          predictionId: item.predictionId,
          isCorrect: item.isCorrect,
          correctedLabel: item.correctedLabel,
          comment: item.comment,
        );
        synced++;
      } on ApiException catch (error) {
        if (error.isNetwork) {
          return synced;
        }
        // 404/422: la predicción ya no existe; se descarta para no bloquear.
      }
    }
    if (synced == queue.length) {
      await _db.clearFeedbackQueue();
    }
    return synced;
  }

  Future<int> _syncPredictions() async {
    final pending = await _db.readPending();
    var synced = 0;
    for (final item in pending) {
      final bytes = await _db.readPendingImage(item.localId);
      if (bytes == null) {
        await _db.removePending(item.localId);
        continue;
      }
      try {
        await _apiService.predict(
          XFile.fromData(bytes, name: '${item.localId}.jpg'),
        );
        await _db.removePending(item.localId);
        synced++;
      } on ApiException catch (error) {
        if (error.isNetwork) {
          return synced;
        }
        // 4xx: imagen inválida o similar; se descarta para no bloquear la cola.
        await _db.removePending(item.localId);
      }
    }
    return synced;
  }

  Future<void> dispose() async {
    await _subscription?.cancel();
    _apiService.dispose();
    _authService.dispose();
  }
}

class SyncResult {
  const SyncResult({
    required this.accounts,
    required this.predictions,
    required this.feedback,
  });

  const SyncResult.empty()
      : accounts = 0,
        predictions = 0,
        feedback = 0;

  final int accounts;
  final int predictions;
  final int feedback;

  bool get hasChanges => accounts + predictions + feedback > 0;
}
