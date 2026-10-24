import 'package:crypto/crypto.dart';
import 'package:image_picker/image_picker.dart' show XFile;

import '../local/local_db.dart';
import '../models/pending_prediction.dart';
import '../models/prediction_model.dart';
import 'onnx_predictor.dart';

/// Clasificación sin conexión con el modelo ONNX local.
///
/// Replica el comportamiento del backend: valida el tamaño, infiere con el
/// mismo `best.pt` exportado y deja la predicción en cola para sincronizarla
/// cuando vuelva la conexión.
class OfflineService {
  OfflineService({LocalDB? db, OnnxPredictor? predictor})
      : _db = db,
        _predictor = predictor ?? OnnxPredictor();

  final LocalDB? _db;
  final OnnxPredictor _predictor;

  static const int maxImageBytes = 10 * 1024 * 1024;

  Future<PredictionModel> classify(XFile image) async {
    final bytes = await image.readAsBytes();
    if (bytes.length > maxImageBytes) {
      throw const OfflineException('La imagen supera el límite de 10 MB');
    }

    final prediction = await _predictor.predict(bytes);

    if (_db != null) {
      final now = DateTime.now().toUtc().toIso8601String();
      final pending = PendingPrediction(
        localId: 'offline-${DateTime.now().microsecondsSinceEpoch}',
        label: prediction.label,
        confidence: prediction.confidence,
        probabilities: prediction.probabilities,
        modelVersion: prediction.modelVersion,
        inferenceMs: prediction.inferenceMs,
        createdAt: now,
        imagePath: '',
        imageHash: sha256.convert(bytes).toString(),
      );
      await _db.addPending(pending, bytes);
    }
    return prediction;
  }

  Future<void> dispose() => _predictor.dispose();
}

class OfflineException implements Exception {
  const OfflineException(this.message);

  final String message;

  @override
  String toString() => message;
}
