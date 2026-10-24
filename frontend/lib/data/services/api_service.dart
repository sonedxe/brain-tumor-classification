import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart' show XFile;

import '../../core/config.dart';
import '../models/history_entry.dart';
import '../models/prediction_detail.dart';
import '../models/prediction_model.dart';
import '../models/stats_summary.dart';

/// Error de dominio, ya normalizado para que la vista lo muestre en espanol.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode, this.isNetwork = false});

  final String message;
  final int? statusCode;

  /// `true` cuando el fallo es de conexión: habilita el fallback offline.
  final bool isNetwork;

  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// Cliente HTTP. Pertenece a la capa Model de MVVM.
///
/// Es el unico punto del frontend que conoce la URL y el formato de la
/// peticion. Usa `XFile` (no `dart:io`) para que la misma logica funcione en
/// movil y en web/Chrome.
class ApiService {
  ApiService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _client;
  final String _baseUrl;

  String get baseUrl => _baseUrl;

  /// Resuelve una ruta relativa de `media/` contra la **raiz del servidor**.
  ///
  /// El backend devuelve `gradcam_path` como ruta relativa (`/static/...`) y
  /// monta los estaticos en la raiz, no bajo el prefijo de la API. Por eso se
  /// conservan solo esquema, host y puerto de `_baseUrl` y se descarta su ruta
  /// (`/api/v1`); de lo contrario la imagen daria 404.
  Uri resolveStaticPath(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return Uri.parse(path);
    }
    final base = Uri.parse(_baseUrl);
    final segments =
        path.split('/').where((segment) => segment.isNotEmpty).toList();
    return base.replace(pathSegments: segments);
  }

  Uri _endpoint(String path) {
    final base = Uri.parse(_baseUrl);
    final segments = <String>[
      ...base.pathSegments.where((segment) => segment.isNotEmpty),
      ...path.split('/').where((segment) => segment.isNotEmpty),
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
      final response = await _client
          .get(_endpoint('health'))
          .timeout(AppConfig.requestTimeout);
      return response.statusCode == 200;
    } on http.ClientException {
      return false;
    } on TimeoutException {
      return false;
    }
  }

  /// `GET /history` — ultimas predicciones registradas por el backend.
  Future<List<HistoryEntry>> fetchHistory({int limit = 20}) async {
    try {
      final uri = _endpoint('history').replace(
        queryParameters: {'limit': '$limit'},
      );
      final response = await _client.get(uri).timeout(AppConfig.requestTimeout);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        if (decoded is List) {
          return decoded
              .whereType<Map<String, dynamic>>()
              .map(HistoryEntry.fromJson)
              .toList();
        }
        throw const ApiException('El historial no es una lista JSON');
      }

      throw ApiException(
        _extractDetail(response) ?? 'Error ${response.statusCode}',
        statusCode: response.statusCode,
      );
    } on http.ClientException {
      throw const ApiException(
        'No hay conexion con el servidor. Verifica que el backend este '
        'corriendo y que API_BASE_URL apunte a el.',
        isNetwork: true,
      );
    } on TimeoutException {
      throw const ApiException(
        'El servidor tardo demasiado en responder',
        isNetwork: true,
      );
    }
  }

  Future<PredictionModel> predict(XFile image) async {
    final bytes = await image.readAsBytes();
    if (bytes.length > AppConfig.maxImageBytes) {
      throw const ApiException('La imagen supera el limite de 10 MB');
    }

    try {
      final request = http.MultipartRequest('POST', _endpoint('predict'))
        ..files.add(
          http.MultipartFile.fromBytes('file', bytes, filename: image.name),
        )
        ..fields['client'] = 'flutter';

      final streamed =
          await _client.send(request).timeout(AppConfig.requestTimeout);
      final response = await http.Response.fromStream(streamed);

      return PredictionModel.fromJson(await _decode(response));
    } on http.ClientException {
      throw const ApiException(
        'No hay conexion con el servidor. Verifica que el backend este '
        'corriendo y que API_BASE_URL apunte a el.',
        isNetwork: true,
      );
    } on TimeoutException {
      throw const ApiException(
        'El servidor tardo demasiado en responder',
        isNetwork: true,
      );
    }
  }

  /// `GET /stats/summary` — conteos por clase y latencias medias.
  Future<StatsSummary> fetchStatsSummary() async {
    try {
      final response =
          await _client.get(_endpoint('stats/summary')).timeout(AppConfig.requestTimeout);
      return StatsSummary.fromJson(await _decode(response));
    } on http.ClientException {
      throw const ApiException(
        'No hay conexion con el servidor. Verifica que el backend este '
        'corriendo y que API_BASE_URL apunte a el.',
        isNetwork: true,
      );
    } on TimeoutException {
      throw const ApiException(
        'El servidor tardo demasiado en responder',
        isNetwork: true,
      );
    }
  }

  /// `GET /predictions/{id}` — detalle con las 4 probabilidades y Grad-CAM.
  Future<PredictionDetail> fetchPredictionDetail(int id) async {
    try {
      final response = await _client
          .get(_endpoint('predictions/$id'))
          .timeout(AppConfig.requestTimeout);
      return PredictionDetail.fromJson(await _decode(response));
    } on http.ClientException {
      throw const ApiException(
        'No hay conexion con el servidor. Verifica que el backend este '
        'corriendo y que API_BASE_URL apunte a el.',
        isNetwork: true,
      );
    } on TimeoutException {
      throw const ApiException(
        'El servidor tardo demasiado en responder',
        isNetwork: true,
      );
    }
  }

  /// `POST /predictions/{id}/feedback` — revision humana (human-in-the-loop).
  Future<void> sendFeedback({
    required int predictionId,
    required bool isCorrect,
    String? correctedLabel,
    String? comment,
  }) async {
    try {
      final body = <String, dynamic>{
        'is_correct': isCorrect,
        // ignore: use_null_aware_elements
        if (correctedLabel != null) 'corrected_label': correctedLabel,
        if (comment?.isNotEmpty ?? false) 'comment': comment,
      };
      final response = await _client
          .post(
            _endpoint('predictions/$predictionId/feedback'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(AppConfig.requestTimeout);
      await _decode(response);
    } on http.ClientException {
      throw const ApiException(
        'No hay conexion con el servidor. Verifica que el backend este '
        'corriendo y que API_BASE_URL apunte a el.',
        isNetwork: true,
      );
    } on TimeoutException {
      throw const ApiException(
        'El servidor tardo demasiado en responder',
        isNetwork: true,
      );
    }
  }

  void dispose() => _client.close();
}
