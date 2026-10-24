import 'package:flutter/foundation.dart';

import '../data/models/prediction_detail.dart';
import '../data/repositories/detail_repository.dart';
import '../data/services/api_service.dart';

enum DetailStatus { idle, loading, success, error, sendingFeedback, feedbackSent }

/// ViewModel del detalle + feedback humano (MVVM).
class DetailViewModel extends ChangeNotifier {
  DetailViewModel({DetailRepository? repository})
      : _repository = repository ?? DetailRepository();

  final DetailRepository _repository;

  DetailStatus _status = DetailStatus.idle;
  PredictionDetail? _detail;
  String? _errorMessage;
  String? _feedbackMessage;

  DetailStatus get status => _status;
  PredictionDetail? get detail => _detail;
  String? get errorMessage => _errorMessage;
  String? get feedbackMessage => _feedbackMessage;
  bool get isLoading => _status == DetailStatus.loading;
  bool get hasError => _status == DetailStatus.error;
  bool get isSending => _status == DetailStatus.sendingFeedback;

  Uri? gradcamUrl(String? path) {
    if (path == null || path.isEmpty) return null;
    return _repository.resolveStaticPath(path);
  }

  Future<void> load(int id) async {
    _status = DetailStatus.loading;
    _errorMessage = null;
    _feedbackMessage = null;
    notifyListeners();

    try {
      _detail = await _repository.fetchDetail(id);
      _status = DetailStatus.success;
    } on ApiException catch (error) {
      _errorMessage = error.message;
      _status = DetailStatus.error;
    } on Exception catch (error) {
      _errorMessage = 'Ocurrio un error inesperado: $error';
      _status = DetailStatus.error;
    }
    notifyListeners();
  }

  Future<void> sendFeedback({
    required bool isCorrect,
    String? correctedLabel,
    String? comment,
  }) async {
    final current = _detail;
    if (current == null) return;
    _status = DetailStatus.sendingFeedback;
    _feedbackMessage = null;
    notifyListeners();

    try {
      await _repository.sendFeedback(
        predictionId: current.id,
        isCorrect: isCorrect,
        correctedLabel: correctedLabel,
        comment: comment,
      );
      _feedbackMessage = 'Gracias, tu revision quedo registrada.';
      // Recarga el detalle para reflejar el nuevo conteo de feedback.
      _detail = await _repository.fetchDetail(current.id);
      _status = DetailStatus.feedbackSent;
    } on ApiException catch (error) {
      _feedbackMessage = error.message;
      _status = DetailStatus.success;
    } on Exception catch (error) {
      _feedbackMessage = 'Ocurrio un error inesperado: $error';
      _status = DetailStatus.success;
    }
    notifyListeners();
  }

  @override
  void dispose() {
    _repository.dispose();
    super.dispose();
  }
}
