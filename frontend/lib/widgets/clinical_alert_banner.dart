import 'package:flutter/material.dart';

import '../core/confidence.dart';
import '../core/theme.dart';
import '../data/models/prediction_model.dart';

/// Banner destacado para analisis con baja confianza o hallazgo tumoral.
/// No ocupa espacio si el analisis no requiere atencion.
class ClinicalAlertBanner extends StatelessWidget {
  const ClinicalAlertBanner({super.key, required this.prediction});

  final PredictionModel prediction;

  @override
  Widget build(BuildContext context) {
    final alert = clinicalAlertFor(prediction);
    if (alert == null) {
      return const SizedBox.shrink();
    }

    final critical = alert.severity == AlertSeverity.critical;
    final color = critical ? AppTheme.error : AppTheme.warning;
    final background = critical ? AppTheme.errorSoft : AppTheme.warningSoft;

    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: color.withValues(alpha: 0.45), width: 1.4),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            critical ? Icons.emergency_outlined : Icons.warning_amber_rounded,
            color: color,
            size: 26,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  alert.title,
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.w800,
                    fontSize: 14.5,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  alert.message,
                  style: const TextStyle(
                    color: AppTheme.onSurface,
                    fontSize: 12.5,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
