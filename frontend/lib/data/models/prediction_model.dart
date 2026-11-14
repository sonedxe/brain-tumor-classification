/// Modelo de datos: corresponde al contrato de `POST /api/v1/predict`.
///
/// MVVM: es un DTO puro. No sabe nada de widgets, de HTTP ni de la API mas
/// alla del formato de la respuesta.
library;

class PredictionModel {
  const PredictionModel({
    required this.label,
    required this.confidence,
    required this.probabilities,
    required this.modelVersion,
    required this.inferenceMs,
    this.gradcamPath,
    this.id,
  });

  /// Id de la prediccion en el backend (nulo si se calculo sin conexion).
  final int? id;
  final String label;
  final double confidence;
  final Map<String, double> probabilities;
  final String? gradcamPath;
  final String modelVersion;
  final double inferenceMs;

  bool get isTumor => label != 'no_tumor';

  double get confidencePercent => confidence * 100;

  factory PredictionModel.fromJson(Map<String, dynamic> json) {
    final rawProbabilities = (json['probabilities'] as Map?) ?? const {};
    final probabilities = <String, double>{};
    rawProbabilities.forEach((key, value) {
      if (key is String && value is num) {
        probabilities[key] = value.toDouble();
      }
    });

    return PredictionModel(
      id: (json['id'] as num?)?.toInt(),
      label: json['label'] as String? ?? 'desconocido',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      probabilities: probabilities,
      gradcamPath: json['gradcam_path'] as String?,
      modelVersion: json['model_version'] as String? ?? 'desconocido',
      inferenceMs: (json['inference_ms'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() => {
        if (id != null) 'id': id,
        'label': label,
        'confidence': confidence,
        'probabilities': probabilities,
        'gradcam_path': gradcamPath,
        'model_version': modelVersion,
        'inference_ms': inferenceMs,
      };
}
