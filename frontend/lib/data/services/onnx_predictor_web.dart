import 'dart:typed_data';

import '../../core/model_contract.dart';
import '../models/prediction_model.dart';

/// Stub web de `OnnxPredictor`.
///
/// `package:onnxruntime` usa `dart:ffi` y no compila a JavaScript, por eso
/// la version nativa vive en `onnx_predictor_io.dart` y este archivo solo
/// expone la misma API para que `flutter build web` compile. En web la
/// inferencia local no esta disponible: se usa el backend via HTTP.
class OnnxPredictor {
  OnnxPredictor({String assetPath = ModelContract.onnxAsset});

  static bool get isSupported => false;

  Future<PredictionModel> predict(Uint8List imageBytes) async {
    throw UnsupportedError(
      'La inferencia offline requiere una plataforma nativa (APK/iOS). '
      'En web usa el backend.',
    );
  }

  Future<void> dispose() async {}
}
