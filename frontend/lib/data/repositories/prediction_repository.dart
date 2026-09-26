import 'dart:io';

import '../models/prediction_model.dart';
import '../services/api_service.dart';

/// Repositorio: unica pieza que conoce a la vez el modelo y el servicio.
///
/// MVVM: el ViewModel depende de esta abstraccion y nunca de `ApiService`
/// directamente, lo que permite sustituirlo por un fake en las pruebas.
class PredictionRepository {
  PredictionRepository({ApiService? apiService})
      : _apiService = apiService ?? ApiService();

  final ApiService _apiService;

  String get baseUrl => _apiService.baseUrl;

  Future<PredictionModel> classify(File image) => _apiService.predict(image);

  Future<bool> isBackendReachable() => _apiService.checkHealth();

  Uri resolveStaticPath(String path) => _apiService.resolveStaticPath(path);

  void dispose() => _apiService.dispose();
}
