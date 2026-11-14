/// Modelo de datos: corresponde al contrato de `POST /api/v1/predict`.
///
/// MVVM: es un DTO puro. No sabe nada de widgets, de HTTP ni de la API mas
/// alla del formato de la respuesta.
library;

import '../../core/clinical_safety.dart';

class PredictionModel {
  const PredictionModel({
    required this.label,
    required this.confidence,
    required this.probabilities,
    required this.modelVersion,
    required this.inferenceMs,
    this.gradcamPath,
    this.isConclusive = true,
    this.triageLevel = 'bajo',
    this.recommendation = '',
    this.confidenceThreshold = ClinicalAssessment.defaultConfidenceThreshold,
    this.topTwoMargin = 0.0,
  });

  final String label;
  final double confidence;
  final Map<String, double> probabilities;
  final String? gradcamPath;
  final String modelVersion;
  final double inferenceMs;

  /// Capa de seguridad clinica devuelta por el backend (o calculada en local).
  final bool isConclusive;
  final String triageLevel;
  final String recommendation;
  final double confidenceThreshold;
  final double topTwoMargin;

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

    final label = json['label'] as String? ?? 'desconocido';
    final confidence = (json['confidence'] as num?)?.toDouble() ?? 0.0;

    // Respaldo local: si el backend no trae la capa de seguridad, se calcula
    // con las mismas reglas (util para el modo offline y clientes antiguos).
    final assessment = ClinicalAssessment.assess(
      label: label,
      confidence: confidence,
      probabilities: probabilities,
    );

    return PredictionModel(
      label: label,
      confidence: confidence,
      probabilities: probabilities,
      gradcamPath: json['gradcam_path'] as String?,
      modelVersion: json['model_version'] as String? ?? 'desconocido',
      inferenceMs: (json['inference_ms'] as num?)?.toDouble() ?? 0.0,
      isConclusive: json['is_conclusive'] as bool? ?? assessment.isConclusive,
      triageLevel: json['triage_level'] as String? ?? assessment.triageLevel,
      recommendation: (json['recommendation'] as String?)?.isNotEmpty == true
          ? json['recommendation'] as String
          : assessment.recommendation,
      confidenceThreshold: (json['confidence_threshold'] as num?)?.toDouble() ??
          assessment.confidenceThreshold,
      topTwoMargin: (json['top_two_margin'] as num?)?.toDouble() ??
          assessment.topTwoMargin,
    );
  }

  Map<String, dynamic> toJson() => {
        'label': label,
        'confidence': confidence,
        'probabilities': probabilities,
        'gradcam_path': gradcamPath,
        'model_version': modelVersion,
        'inference_ms': inferenceMs,
        'is_conclusive': isConclusive,
        'triage_level': triageLevel,
        'recommendation': recommendation,
        'confidence_threshold': confidenceThreshold,
        'top_two_margin': topTwoMargin,
      };
}
