import 'package:flutter/foundation.dart';

import '../data/services/auth_service.dart';
import '../data/services/session_store.dart';

/// ViewModel de sesion (camino opcional).
///
/// MVVM: guarda el token y el nombre, y los persiste con [SessionStore] para
/// que la sesion sobreviva al cierre de la app. `restoreSession()` se llama al
/// arrancar y repuebla el estado desde el almacenamiento.
class AuthViewModel extends ChangeNotifier {
  AuthViewModel({AuthService? service, SessionStore? store})
      : _service = service ?? AuthService(),
        _store = store ?? SharedPreferencesSessionStore();

  final AuthService _service;
  final SessionStore _store;
  String? _token;
  String? _userName;
  String? _error;
  bool _busy = false;
  bool _isRegisterMode = false;

  String? get token => _token;
  String? get userName => _userName;
  String? get error => _error;
  bool get busy => _busy;
  bool get isLoggedIn => _token != null;
  bool get isRegisterMode => _isRegisterMode;

  /// Repuebla la sesion desde el almacenamiento local (llamar al arrancar).
  Future<void> restoreSession() async {
    final token = await _store.readToken();
    if (token == null || token.isEmpty) {
      return;
    }
    _token = token;
    _userName = await _store.readName();
    notifyListeners();
  }

  void toggleMode() {
    _isRegisterMode = !_isRegisterMode;
    _error = null;
    notifyListeners();
  }

  Future<bool> submit({required String email, required String password, String? name}) async {
    _busy = true;
    _error = null;
    notifyListeners();
    try {
      final data = _isRegisterMode
          ? await _service.register(name ?? '', email, password)
          : await _service.login(email, password);
      _token = data['access_token'] as String?;
      _userName = data['name'] as String? ?? email;
      if (_token != null) {
        await _store.save(token: _token!, name: _userName ?? email);
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

  Future<void> logout() async {
    _token = null;
    _userName = null;
    _error = null;
    await _store.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }
}
