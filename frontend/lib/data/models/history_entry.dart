/// Modelo de datos: corresponde a un elemento de `GET /api/v1/history`.
///
/// MVVM: DTO puro. No conoce widgets ni HTTP; solo el formato del backend.
library;

class HistoryEntry {
  const HistoryEntry({
    required this.id,
    required this.label,
    required this.confidence,
    required this.modelVersion,
    required this.inferenceMs,
    required this.createdAt,
    this.imageHash = '',
  });

  final int id;
  final String label;
  final double confidence;
  final String modelVersion;
  final double inferenceMs;
  final String createdAt;
  final String imageHash;

  bool get isTumor => label != 'no_tumor';

  double get confidencePercent => confidence * 100;

  factory HistoryEntry.fromJson(Map<String, dynamic> json) {
    return HistoryEntry(
      id: (json['id'] as num?)?.toInt() ?? 0,
      label: json['label'] as String? ?? 'desconocido',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      modelVersion: json['model_version'] as String? ?? '',
      inferenceMs: (json['inference_ms'] as num?)?.toDouble() ?? 0.0,
      createdAt: json['created_at'] as String? ?? '',
      imageHash: json['image_hash'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'label': label,
        'confidence': confidence,
        'model_version': modelVersion,
        'inference_ms': inferenceMs,
        'created_at': createdAt,
        'image_hash': imageHash,
      };
}
