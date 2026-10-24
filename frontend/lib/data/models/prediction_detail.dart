/// Modelo de datos: corresponde a `GET /api/v1/predictions/{id}`.
///
/// Incluye las 4 probabilidades, Grad-CAM y el feedback humano registrado.
library;

class PredictionDetail {
  const PredictionDetail({
    required this.id,
    required this.label,
    required this.confidence,
    required this.probabilities,
    required this.modelVersion,
    required this.architecture,
    required this.inferenceMs,
    required this.createdAt,
    this.gradcamPath,
    this.feedbackCount = 0,
  });

  final int id;
  final String label;
  final double confidence;
  final Map<String, double> probabilities;
  final String modelVersion;
  final String architecture;
  final double inferenceMs;
  final String createdAt;
  final String? gradcamPath;
  final int feedbackCount;

  bool get isTumor => label != 'no_tumor';

  factory PredictionDetail.fromJson(Map<String, dynamic> json) {
    final predicted = (json['predicted_class'] as Map?)?.cast<String, dynamic>();
    final model = (json['model'] as Map?)?.cast<String, dynamic>();
    final rawScores = (json['scores'] as List?) ?? const [];
    final probabilities = <String, double>{};
    for (final entry in rawScores) {
      if (entry is Map<String, dynamic>) {
        final lesion = (entry['lesion_class'] as Map?);
        final code = lesion?['code'] as String?;
        final prob = (entry['probability'] as num?)?.toDouble();
        if (code != null && prob != null) {
          probabilities[code] = prob;
        }
      }
    }
    // El backend expone ademas `probabilities` como computed field.
    final computed = (json['probabilities'] as Map?);
    if (computed != null) {
      computed.forEach((key, value) {
        if (key is String && value is num && !probabilities.containsKey(key)) {
          probabilities[key] = value.toDouble();
        }
      });
    }
    final feedback = (json['feedback'] as List?) ?? const [];

    return PredictionDetail(
      id: (json['id'] as num?)?.toInt() ?? 0,
      label: (predicted?['code'] as String?) ?? 'desconocido',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      probabilities: probabilities,
      modelVersion: (model?['version'] as String?) ?? '',
      architecture: (model?['architecture'] as String?) ?? '',
      inferenceMs: (json['inference_ms'] as num?)?.toDouble() ?? 0.0,
      createdAt: json['created_at'] as String? ?? '',
      gradcamPath: json['gradcam_path'] as String?,
      feedbackCount: feedback.length,
    );
  }
}
