import '../models/prediction_detail.dart';
import '../services/api_service.dart';

/// Repositorio del detalle y feedback de una predicción.
///
/// MVVM: el ViewModel depende de esta abstracción y nunca de
/// `ApiService` directamente, lo que permite inyectar un fake en pruebas.
class DetailRepository {
  DetailRepository({ApiService? apiService})
      : _apiService = apiService ?? ApiService();

  final ApiService _apiService;

  Future<PredictionDetail> fetchDetail(int id) =>
      _apiService.fetchPredictionDetail(id);

  Future<void> sendFeedback({
    required int predictionId,
    required bool isCorrect,
    String? correctedLabel,
    String? comment,
  }) =>
      _apiService.sendFeedback(
        predictionId: predictionId,
        isCorrect: isCorrect,
        correctedLabel: correctedLabel,
        comment: comment,
      );

  Uri resolveStaticPath(String path) => _apiService.resolveStaticPath(path);

  void dispose() => _apiService.dispose();
}
