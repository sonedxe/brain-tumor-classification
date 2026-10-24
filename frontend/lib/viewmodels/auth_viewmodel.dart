import 'package:flutter/foundation.dart';

import '../data/local/local_db.dart';
import '../data/services/auth_service.dart';
import '../data/services/connectivity_service.dart';
import '../data/services/session_store.dart';

/// ViewModel de sesion (camino opcional).
///
/// MVVM: guarda el token y el nombre, y los persiste con [SessionStore] para
/// que la sesion sobreviva al cierre de la app. Sin conexión, el registro y el
/// login se resuelven contra el almacén local y se sincronizan al reconectar.
class AuthViewModel extends ChangeNotifier {
  AuthViewModel({
    AuthService? service,
    SessionStore? store,
    LocalDB? db,
    ConnectivityService? connectivity,
  })  : _service = service ?? AuthService(),
        _store = store ?? SharedPreferencesSessionStore(),
        _db = db,
        _connectivity = connectivity ?? ConnectivityService.instance {
    _connectivity.addListener(notifyListeners);
  }

  final AuthService _service;
  final SessionStore _store;
  final LocalDB? _db;
  final ConnectivityService _connectivity;
  String? _token;
  String? _userName;
  String? _error;
  bool _busy = false;
  bool _isRegisterMode = false;
  bool _offlineSession = false;

  String? get token => _token;
  String? get userName => _userName;
  String? get error => _error;
  bool get busy => _busy;
  bool get isLoggedIn => _token != null;
  bool get isRegisterMode => _isRegisterMode;
  bool get isOfflineSession => _offlineSession;

  /// Repuebla la sesion desde el almacenamiento local (llamar al arrancar).
  Future<void> restoreSession() async {
    final token = await _store.readToken();
    if (token == null || token.isEmpty) {
      return;
    }
    _token = token;
    _userName = await _store.readName();
    _offlineSession = token.startsWith('offline:');
    notifyListeners();
  }

  void toggleMode() {
    _isRegisterMode = !_isRegisterMode;
    _error = null;
    notifyListeners();
  }

  Future<bool> submit({
    required String email,
    required String password,
    String? name,
  }) async {
    _busy = true;
    _error = null;
    notifyListeners();
    try {
      if (_connectivity.isOffline) {
        final ok = await _submitOffline(
          email: email,
          password: password,
          name: name,
        );
        if (ok) {
          _isRegisterMode = false;
        }
        return ok;
      }
      final data = _isRegisterMode
          ? await _service.register(name ?? '', email, password)
          : await _service.login(email, password);
      _token = data['access_token'] as String?;
      _userName = data['name'] as String? ?? email;
      _offlineSession = false;
      _isRegisterMode = false;
      if (_token != null) {
        await _store.save(token: _token!, name: _userName ?? email);
      }
      // Si la cuenta se creó offline, al validarse online queda sincronizada.
      final account = await _db?.findAccount(email);
      if (account != null && account.pendingSync) {
        await _db?.saveAccount(account.copyWith(pendingSync: false));
      }
      return true;
    } catch (e) {
      _error = e.toString().replaceFirst('ApiException(null): ', '');
      return false;
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<bool> _submitOffline({
    required String email,
    required String password,
    String? name,
  }) async {
    final db = _db;
    if (db == null) {
      _error = 'El modo sin conexión no está disponible.';
      return false;
    }
    final account = await db.findAccount(email);

    if (_isRegisterMode) {
      if (account != null) {
        _error = 'Ya existe una cuenta local con ese correo.';
        return false;
      }
      await db.saveAccount(
        OfflineAccount(
          email: email,
          name: name ?? email,
          password: password,
        ),
      );
    } else {
      if (account == null || account.password != password) {
        _error = 'Credenciales inválidas (modo sin conexión).';
        return false;
      }
    }

    _token = 'offline:$email';
    _userName = account?.name ?? (name ?? email);
    _offlineSession = true;
    await _store.save(token: _token!, name: _userName ?? email);
    return true;
  }

  Future<void> logout() async {
    _token = null;
    _userName = null;
    _error = null;
    _offlineSession = false;
    await _store.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    _connectivity.removeListener(notifyListeners);
    _service.dispose();
    super.dispose();
  }
}
