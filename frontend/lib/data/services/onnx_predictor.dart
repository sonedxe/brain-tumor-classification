import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:image/image.dart' as img;
import 'package:onnxruntime/onnxruntime.dart';

import '../../core/model_contract.dart';
import '../models/prediction_model.dart';

/// Inferencia local con el mismo modelo que sirve el backend.
///
/// Carga `assets/models/model.onnx` (exportado desde el `best.pt` activo) y
/// reproduce el preprocesamiento del backend: RGB, 224x224 bilineal,
/// normalizacion ImageNet y tensor NCHW float32.
class OnnxPredictor {
  OnnxPredictor({String assetPath = ModelContract.onnxAsset})
      : _assetPath = assetPath;

  final String _assetPath;
  OrtSession? _session;
  bool _envReady = false;

  /// ONNX Runtime solo esta disponible en plataformas nativas.
  static bool get isSupported =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS ||
          defaultTargetPlatform == TargetPlatform.macOS ||
          defaultTargetPlatform == TargetPlatform.linux ||
          defaultTargetPlatform == TargetPlatform.windows);

  Future<void> _ensureSession() async {
    if (_session != null) {
      return;
    }
    if (!isSupported) {
      throw UnsupportedError(
        'La inferencia offline requiere una plataforma nativa (APK/iOS).',
      );
    }
    if (!_envReady) {
      OrtEnv.instance.init();
      _envReady = true;
    }
    final raw = await rootBundle.load(_assetPath);
    final bytes = raw.buffer.asUint8List();
    final options = OrtSessionOptions();
    _session = OrtSession.fromBuffer(bytes, options);
  }

  Future<PredictionModel> predict(Uint8List imageBytes) async {
    await _ensureSession();
    final session = _session!;

    final watch = Stopwatch()..start();
    final tensor = _toTensor(imageBytes);
    final input = OrtValueTensor.createTensorWithDataList(
      tensor,
      [1, 3, ModelContract.inputSize, ModelContract.inputSize],
    );
    final runOptions = OrtRunOptions();
    List<OrtValue?>? outputs;
    try {
      outputs = await session.runAsync(runOptions, {
        session.inputNames.first: input,
      });
      final raw = outputs?.first?.value;
      final logits = _extractLogits(raw);
      final probabilities = _softmax(logits);
      watch.stop();

      var bestIndex = 0;
      for (var i = 1; i < probabilities.length; i++) {
        if (probabilities[i] > probabilities[bestIndex]) {
          bestIndex = i;
        }
      }
      final classes = ModelContract.classes;
      return PredictionModel(
        label: classes[bestIndex],
        confidence: probabilities[bestIndex],
        probabilities: {
          for (var i = 0; i < classes.length; i++) classes[i]: probabilities[i],
        },
        modelVersion: ModelContract.offlineModelVersion,
        inferenceMs: watch.elapsedMicroseconds / 1000.0,
      );
    } finally {
      input.release();
      runOptions.release();
      outputs?.forEach((value) => value?.release());
    }
  }

  /// Convierte bytes de imagen a NCHW float32 normalizado (como el backend).
  Float32List _toTensor(Uint8List bytes) {
    final decoded = img.decodeImage(bytes);
    if (decoded == null) {
      throw const FormatException('No se pudo decodificar la imagen');
    }
    final resized = img.copyResize(
      decoded,
      width: ModelContract.inputSize,
      height: ModelContract.inputSize,
      interpolation: img.Interpolation.linear,
    );

    const size = ModelContract.inputSize;
    final tensor = Float32List(3 * size * size);
    for (var y = 0; y < size; y++) {
      for (var x = 0; x < size; x++) {
        final pixel = resized.getPixel(x, y);
        final index = y * size + x;
        tensor[index] = (pixel.r / 255.0 - ModelContract.mean[0]) /
            ModelContract.std[0];
        tensor[size * size + index] =
            (pixel.g / 255.0 - ModelContract.mean[1]) / ModelContract.std[1];
        tensor[2 * size * size + index] =
            (pixel.b / 255.0 - ModelContract.mean[2]) / ModelContract.std[2];
      }
    }
    return tensor;
  }

  List<double> _extractLogits(Object? value) {
    // onnxruntime devuelve List<List<double>> para un lote de 1.
    if (value is List && value.isNotEmpty) {
      final first = value.first;
      if (first is List) {
        return first.map((e) => (e as num).toDouble()).toList();
      }
    }
    throw StateError('Salida ONNX inesperada: $value');
  }

  List<double> _softmax(List<double> logits) {
    final maxLogit = logits.reduce(math.max);
    final exps = logits.map((value) => math.exp(value - maxLogit)).toList();
    final sum = exps.fold<double>(0, (acc, value) => acc + value);
    return exps.map((value) => value / sum).toList();
  }

  Future<void> dispose() async {
    _session?.release();
    _session = null;
  }
}
