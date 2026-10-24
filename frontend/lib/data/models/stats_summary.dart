/// Modelo de datos: corresponde a `GET /api/v1/stats/summary`.
///
/// MVVM: DTO puro. No conoce widgets ni HTTP; solo el formato del backend.
library;

class ClassStat {
  const ClassStat({
    required this.code,
    required this.displayName,
    required this.count,
    this.avgConfidence,
  });

  final String code;
  final String displayName;
  final int count;
  final double? avgConfidence;

  factory ClassStat.fromJson(Map<String, dynamic> json) {
    return ClassStat(
      code: json['code'] as String? ?? 'desconocido',
      displayName: json['display_name'] as String? ?? '',
      count: (json['count'] as num?)?.toInt() ?? 0,
      avgConfidence: (json['avg_confidence'] as num?)?.toDouble(),
    );
  }
}

class StatsSummary {
  const StatsSummary({
    required this.totalPredictions,
    required this.uniqueImages,
    required this.modelsRegistered,
    required this.totalFeedback,
    this.avgConfidence,
    this.avgInferenceMs,
    this.byClass = const [],
  });

  final int totalPredictions;
  final int uniqueImages;
  final int modelsRegistered;
  final int totalFeedback;
  final double? avgConfidence;
  final double? avgInferenceMs;
  final List<ClassStat> byClass;

  factory StatsSummary.fromJson(Map<String, dynamic> json) {
    final raw = (json['by_class'] as List?) ?? const [];
    return StatsSummary(
      totalPredictions: (json['total_predictions'] as num?)?.toInt() ?? 0,
      uniqueImages: (json['unique_images'] as num?)?.toInt() ?? 0,
      modelsRegistered: (json['models_registered'] as num?)?.toInt() ?? 0,
      totalFeedback: (json['total_feedback'] as num?)?.toInt() ?? 0,
      avgConfidence: (json['avg_confidence'] as num?)?.toDouble(),
      avgInferenceMs: (json['avg_inference_ms'] as num?)?.toDouble(),
      byClass: raw
          .whereType<Map<String, dynamic>>()
          .map(ClassStat.fromJson)
          .toList(),
    );
  }
}
