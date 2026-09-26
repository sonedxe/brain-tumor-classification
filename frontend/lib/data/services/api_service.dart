import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../core/config.dart';
import '../models/prediction_model.dart';

/// Error de dominio, ya normalizado para que la vista lo muestre en espanol.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// Cliente HTTP. Pertenece a la capa Model de MVVM.
///
/// Es el unico punto del frontend que conoce la URL y el formato de la
/// peticion.
class ApiService {
  ApiService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _client;
  final String _baseUrl;

  String get baseUrl => _baseUrl;

  /// Resuelve una ruta relativa de `media/` contra la raiz del servidor.
  ///
  /// El backend devuelve `gradcam_path` como ruta relativa, y no como base64,
  /// para no inflar la respuesta. Hay que anteponer el host aqui.
  Uri resolveStaticPath(String path) {
    final base = Uri.parse(_baseUrl);
    final segments = <String>[
      ...base.pathSegments.where((segment) => segment.isNotEmpty),
      ...path.split('/').where((segment) => segment.isNotEmpty),
    ];
    return base.replace(pathSegments: segments);
  }

  Uri _endpoint(String path) {
    final base = Uri.parse(_baseUrl);
    final segments = <String>[
      ...base.pathSegments.where((segment) => segment.isNotEmpty),
      path,
    ];
    return base.replace(pathSegments: segments);
  }

  Future<Map<String, dynamic>> _decode(http.Response response) async {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic>) {
        return decoded;
      }
      throw const ApiException('La respuesta del servidor no es un objeto JSON');
    }

    throw ApiException(
      _extractDetail(response) ?? 'Error ${response.statusCode}',
      statusCode: response.statusCode,
    );
  }

  String? _extractDetail(http.Response response) {
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded['detail'] != null) {
        return decoded['detail'].toString();
      }
    } on FormatException {
      return null;
    }
    return null;
  }

  Future<bool> checkHealth() async {
    try {
      final response = await _client.get(_endpoint('health'));
      return response.statusCode == 200;
    } on SocketException {
      return false;
    } on TimeoutException {
      return false;
    }
  }

  Future<PredictionModel> predict(File image) async {
    if (!await image.exists()) {
      throw const ApiException('No se encontro la imagen seleccionada');
    }

    final length = await image.length();
    if (length > AppConfig.maxImageBytes) {
      throw const ApiException('La imagen supera el limite de 10 MB');
    }

    try {
      final request = http.MultipartRequest('POST', _endpoint('predict'))
        ..files.add(await http.MultipartFile.fromPath('file', image.path))
        ..fields['client'] = 'flutter-android';

      final streamed = await _client
          .send(request)
          .timeout(AppConfig.requestTimeout);
      final response = await http.Response.fromStream(streamed);

      return PredictionModel.fromJson(await _decode(response));
    } on SocketException {
      throw const ApiException(
        'No hay conexion con el servidor. Verifica que el backend este '
        'corriendo y que API_BASE_URL apunte a el.',
      );
    } on TimeoutException {
      throw const ApiException('El servidor tardo demasiado en responder');
    } on http.ClientException catch (error) {
      throw ApiException('Error de red: ${error.message}');
    }
  }

  void dispose() => _client.close();
}
