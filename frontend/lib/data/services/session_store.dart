import 'package:shared_preferences/shared_preferences.dart';

/// Persistencia de la sesion (token JWT + nombre).
///
/// Se define como interfaz para poder inyectar una implementacion en memoria
/// en las pruebas y no depender del canal de plataforma de `SharedPreferences`.
abstract class SessionStore {
  Future<String?> readToken();
  Future<String?> readName();
  Future<void> save({required String token, required String name});
  Future<void> clear();
}

/// Implementacion real sobre almacenamiento local del dispositivo.
class SharedPreferencesSessionStore implements SessionStore {
  static const String _tokenKey = 'auth_token';
  static const String _nameKey = 'auth_name';

  @override
  Future<String?> readToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  @override
  Future<String?> readName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_nameKey);
  }

  @override
  Future<void> save({required String token, required String name}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    await prefs.setString(_nameKey, name);
  }

  @override
  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_nameKey);
  }
}
