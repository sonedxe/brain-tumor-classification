/// Niveles de confianza del modelo y alertas clinicas derivadas.
///
/// Logica pura (sin widgets) para poder probarla y reutilizarla en el
/// resultado, el historial y las notificaciones.
library;

import 'package:flutter/material.dart';

import '../data/models/prediction_model.dart';
import 'theme.dart';

/// Por debajo de este valor el resultado exige revision humana.
const double lowConfidenceThreshold = 0.75;

/// A partir de este valor la confianza se considera alta.
const double highConfidenceThreshold = 0.90;

enum ConfidenceLevel { high, moderate, low }

ConfidenceLevel confidenceLevelOf(double confidence) {
  if (confidence >= highConfidenceThreshold) {
    return ConfidenceLevel.high;
  }
  if (confidence >= lowConfidenceThreshold) {
    return ConfidenceLevel.moderate;
  }
  return ConfidenceLevel.low;
}

extension ConfidenceLevelStyle on ConfidenceLevel {
  String get label => switch (this) {
        ConfidenceLevel.high => 'Confianza alta',
        ConfidenceLevel.moderate => 'Confianza moderada',
        ConfidenceLevel.low => 'Confianza baja',
      };

  Color get color => switch (this) {
        ConfidenceLevel.high => AppTheme.success,
        ConfidenceLevel.moderate => AppTheme.warning,
        ConfidenceLevel.low => AppTheme.error,
      };

  Color get softColor => switch (this) {
        ConfidenceLevel.high => AppTheme.successSoft,
        ConfidenceLevel.moderate => AppTheme.warningSoft,
        ConfidenceLevel.low => AppTheme.errorSoft,
      };

  IconData get icon => switch (this) {
        ConfidenceLevel.high => Icons.verified_outlined,
        ConfidenceLevel.moderate => Icons.info_outline,
        ConfidenceLevel.low => Icons.warning_amber_rounded,
      };
}

enum AlertSeverity { warning, critical }

/// Aviso clinico mostrado en la app cuando un analisis requiere atencion.
class ClinicalAlert {
  const ClinicalAlert({
    required this.severity,
    required this.title,
    required this.message,
  });

  final AlertSeverity severity;
  final String title;
  final String message;
}

/// Devuelve el aviso que corresponde a [prediction], o `null` si no requiere
/// atencion especial (sin tumor y con confianza suficiente).
ClinicalAlert? clinicalAlertFor(PredictionModel prediction) {
  final lowConfidence = prediction.confidence < lowConfidenceThreshold;

  if (prediction.isTumor && lowConfidence) {
    return const ClinicalAlert(
      severity: AlertSeverity.critical,
      title: 'Revisión médica prioritaria',
      message: 'Se detectó un posible hallazgo y la confianza del modelo es '
          'baja. Consulta cuanto antes con un especialista.',
    );
  }
  if (prediction.isTumor) {
    return const ClinicalAlert(
      severity: AlertSeverity.critical,
      title: 'Hallazgo que requiere revisión médica',
      message: 'El modelo detectó un posible tumor. Este resultado es solo un '
          'apoyo: debe ser confirmado por un profesional de la salud.',
    );
  }
  if (lowConfidence) {
    return const ClinicalAlert(
      severity: AlertSeverity.warning,
      title: 'Confianza baja',
      message: 'El resultado no es concluyente. Repite el análisis con una '
          'imagen de mejor calidad o consulta con un especialista.',
    );
  }
  return null;
}
