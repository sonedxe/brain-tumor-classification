/// Capa de seguridad clínica compartida entre la app y el backend.
///
/// Espejo de `backend/app/services/clinical_safety.py`. Se usa como respaldo
/// cuando el resultado viene del modelo local (ONNX) o de un backend antiguo
/// que aún no envía los campos de triaje. Las reglas son las mismas:
///
/// 1. Confianza mínima (`0.70`): por debajo, el resultado es *no concluyente*.
/// 2. Margen top-1 / top-2 (`0.10`): si las dos clases más probables están
///    casi empatadas, el modelo no discrimina aunque la confianza sea alta.
/// 3. Riesgo por clase: tumor con confianza >= 0.90 → alto; tumor con
///    confianza moderada → medio; sin tumor → bajo.
library;

class ClinicalAssessment {
  const ClinicalAssessment({
    required this.isConclusive,
    required this.triageLevel,
    required this.recommendation,
    required this.confidenceThreshold,
    required this.topTwoMargin,
  });

  final bool isConclusive;

  /// `bajo` | `medio` | `alto` | `no_concluyente`.
  final String triageLevel;
  final String recommendation;
  final double confidenceThreshold;
  final double topTwoMargin;

  static const double defaultConfidenceThreshold = 0.70;
  static const double defaultMarginThreshold = 0.10;
  static const double defaultHighConfidenceThreshold = 0.90;

  static const String noTumorClass = 'no_tumor';

  static const String recommendationInconclusive =
      'Resultado no concluyente: la confianza o el margen entre clases es '
      'insuficiente. No uses este resultado para decidir; repite el estudio o '
      'consulta a un especialista en radiología.';

  static const String recommendationNoTumor =
      'No se detectó un hallazgo tumoral con confianza suficiente. Aun así, la '
      'lectura de un especialista en radiología sigue siendo la referencia.';

  static const String recommendationMedium =
      'Posible hallazgo tumoral. Se recomienda revisión por un especialista en '
      'radiología o neurocirugía antes de cualquier decisión clínica.';

  static const String recommendationHigh =
      'Hallazgo tumoral con alta confianza. Deriva a un especialista en '
      'radiología o neurocirugía para confirmación diagnóstica.';

  static ClinicalAssessment assess({
    required String label,
    required double confidence,
    Map<String, double> probabilities = const {},
    double confidenceThreshold = defaultConfidenceThreshold,
    double marginThreshold = defaultMarginThreshold,
    double highConfidenceThreshold = defaultHighConfidenceThreshold,
  }) {
    final values = probabilities.values.toList()..sort((a, b) => b.compareTo(a));
    final top1 = values.isNotEmpty ? values.first : confidence;
    final top2 = values.length > 1 ? values[1] : 0.0;
    final margin = (top1 - top2).clamp(0.0, 1.0).toDouble();
    final conclusive =
        confidence >= confidenceThreshold && margin >= marginThreshold;

    if (!conclusive) {
      return ClinicalAssessment(
        isConclusive: false,
        triageLevel: 'no_concluyente',
        recommendation: recommendationInconclusive,
        confidenceThreshold: confidenceThreshold,
        topTwoMargin: margin,
      );
    }

    if (label == noTumorClass) {
      return ClinicalAssessment(
        isConclusive: true,
        triageLevel: 'bajo',
        recommendation: recommendationNoTumor,
        confidenceThreshold: confidenceThreshold,
        topTwoMargin: margin,
      );
    }

    if (confidence >= highConfidenceThreshold) {
      return ClinicalAssessment(
        isConclusive: true,
        triageLevel: 'alto',
        recommendation: recommendationHigh,
        confidenceThreshold: confidenceThreshold,
        topTwoMargin: margin,
      );
    }

    return ClinicalAssessment(
      isConclusive: true,
      triageLevel: 'medio',
      recommendation: recommendationMedium,
      confidenceThreshold: confidenceThreshold,
      topTwoMargin: margin,
    );
  }
}
