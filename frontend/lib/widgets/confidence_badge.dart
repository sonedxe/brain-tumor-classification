import 'package:flutter/material.dart';

import '../core/confidence.dart';
import '../core/theme.dart';

/// Etiqueta con el nivel de confianza (alta / moderada / baja con alerta).
class ConfidenceBadge extends StatelessWidget {
  const ConfidenceBadge({super.key, required this.confidence});

  final double confidence;

  @override
  Widget build(BuildContext context) {
    final level = confidenceLevelOf(confidence);
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm + 2,
        vertical: AppSpacing.xs + 1,
      ),
      decoration: BoxDecoration(
        color: level.softColor,
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: level.color.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(level.icon, size: 14, color: level.color),
          const SizedBox(width: AppSpacing.xs + 1),
          Text(
            level.label,
            style: TextStyle(
              color: level.color,
              fontSize: 11.5,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
