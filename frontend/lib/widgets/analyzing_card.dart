import 'package:flutter/material.dart';

import '../core/theme.dart';

/// Estado de carga explicito mientras se procesa la imagen.
class AnalyzingCard extends StatelessWidget {
  const AnalyzingCard({super.key, required this.offline});

  /// `true` si se clasifica con el modelo local ONNX (sin red).
  final bool offline;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2.6),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Text(
                    'Analizando imagen…',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            const ClipRRect(
              borderRadius: BorderRadius.all(Radius.circular(AppRadius.pill)),
              child: LinearProgressIndicator(minHeight: 6),
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              offline
                  ? 'Sin conexión: clasificando con el modelo local. '
                      'No cierres la app.'
                  : 'Enviando la MRI, clasificando y generando el mapa '
                      'Grad-CAM. Puede tardar unos segundos.',
              style: const TextStyle(
                color: AppTheme.muted,
                fontSize: 12.5,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
