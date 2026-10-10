import 'package:flutter/foundation.dart';

import '../data/services/auth_service.dart';

/// ViewModel de sesion (camino opcional).
///
/// MVVM: guarda token + nombre en memoria. Sin persistencia para ir rapido;
/// con `SharedPreferences` se agrega despues sin tocar las vistas.
class AuthViewModel extends ChangeNotifier {
  AuthViewModel({AuthService? service}) : _service = service ?? AuthService();

  final AuthService _service;
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
      return true;
    } catch (e) {
      _error = e.toString().replaceFirst('ApiException(null): ', '');
      return false;
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  void logout() {
    _token = null;
    _userName = null;
    _error = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }
}
