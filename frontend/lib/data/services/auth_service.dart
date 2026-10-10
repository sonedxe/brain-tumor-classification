import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../core/config.dart';
import 'api_service.dart';

/// Servicio de autenticacion (camino opcional).
///
/// El analisis funciona sin cuenta. El login solo sirve para el historial
/// por usuario y para las capturas del informe (RF-01/02/03).
class AuthService {
  AuthService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _client;
  final String _baseUrl;

  Uri _endpoint(String path) {
    final base = Uri.parse(_baseUrl);
    final segments = [
      ...base.pathSegments.where((s) => s.isNotEmpty),
      ...path.split('/').where((s) => s.isNotEmpty),
    ];
    return base.replace(pathSegments: segments);
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final response = await _client
        .post(_endpoint(path),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body))
        .timeout(AppConfig.requestTimeout);
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return (decoded as Map).cast<String, dynamic>();
    }
    final detail = (decoded is Map && decoded['detail'] != null)
        ? decoded['detail'].toString()
        : 'Error ${response.statusCode}';
    throw ApiException(detail, statusCode: response.statusCode);
  }

  Future<Map<String, dynamic>> login(String email, String password) =>
      _post('auth/login', {'email': email, 'password': password});

  Future<Map<String, dynamic>> register(String name, String email, String password) =>
      _post('auth/register', {'name': name, 'email': email, 'password': password});

  void dispose() => _client.close();
}
