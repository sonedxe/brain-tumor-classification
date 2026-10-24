/// Predicción realizada sin conexión y pendiente de sincronizar.
///
/// Se guarda localmente con la imagen original (para reenviarla al backend)
/// y el resultado del modelo ONNX, de modo que el historial ya la muestre
/// mientras se recupera la conexión.
library;

class PendingPrediction {
  const PendingPrediction({
    required this.localId,
    required this.label,
    required this.confidence,
    required this.probabilities,
    required this.modelVersion,
    required this.inferenceMs,
    required this.createdAt,
    required this.imagePath,
    this.imageHash = '',
  });

  final String localId;
  final String label;
  final double confidence;
  final Map<String, double> probabilities;
  final String modelVersion;
  final double inferenceMs;
  final String createdAt;
  final String imagePath;
  final String imageHash;

  Map<String, dynamic> toJson() => {
        'local_id': localId,
        'label': label,
        'confidence': confidence,
        'probabilities': probabilities,
        'model_version': modelVersion,
        'inference_ms': inferenceMs,
        'created_at': createdAt,
        'image_path': imagePath,
        'image_hash': imageHash,
      };

  factory PendingPrediction.fromJson(Map<String, dynamic> json) {
    final raw = (json['probabilities'] as Map?) ?? const {};
    final probabilities = <String, double>{};
    raw.forEach((key, value) {
      if (key is String && value is num) {
        probabilities[key] = value.toDouble();
      }
    });
    return PendingPrediction(
      localId: json['local_id'] as String? ?? '',
      label: json['label'] as String? ?? 'desconocido',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
      probabilities: probabilities,
      modelVersion: json['model_version'] as String? ?? '',
      inferenceMs: (json['inference_ms'] as num?)?.toDouble() ?? 0,
      createdAt: json['created_at'] as String? ?? '',
      imagePath: json['image_path'] as String? ?? '',
      imageHash: json['image_hash'] as String? ?? '',
    );
  }
}
