import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../data/models/prediction_model.dart';

/// Tarjeta con el resultado de la clasificacion.
///
/// MVVM: recibe el modelo ya construido y solo lo presenta. No calcula
/// probabilidades ni decide el color de la clase.
class ResultCard extends StatelessWidget {
  const ResultCard({
    super.key,
    required this.prediction,
    required this.gradcamUrl,
  });

  final PredictionModel prediction;
  final Uri? gradcamUrl;

  Color get _labelColor =>
      AppTheme.classColors[prediction.label] ?? AppTheme.primary;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Resultado',
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: AppTheme.muted,
                      ),
                ),
                const SizedBox(height: 8),
                Text(
                  _labelFor(prediction.label),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: _labelColor,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Confianza ${prediction.confidencePercent.toStringAsFixed(2)} %',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  'Inferencia ${prediction.inferenceMs.toStringAsFixed(1)} ms '
                  '| ${prediction.modelVersion}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppTheme.muted,
                      ),
                ),
                const SizedBox(height: 16),
                Text(
                  'Probabilidades por clase',
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: AppTheme.muted,
                      ),
                ),
                const SizedBox(height: 8),
                ...prediction.probabilities.entries
                    .map((entry) => _ProbabilityBar(
                          name: entry.key,
                          value: entry.value,
                          color: AppTheme.classColors[entry.key] ??
                              AppTheme.primary,
                        )),
              ],
            ),
          ),
        ),
        if (gradcamUrl != null) ...[
          const SizedBox(height: 4),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Mapa de calor Grad-CAM',
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: AppTheme.muted,
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Zona que el modelo uso para decidir',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppTheme.muted,
                        ),
                  ),
                  const SizedBox(height: 12),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.network(
                      gradcamUrl.toString(),
                      fit: BoxFit.contain,
                      errorBuilder: (_, _, _) => const SizedBox(
                        height: 180,
                        child: Center(
                          child: Text(
                            'No se pudo cargar el mapa de calor',
                            style: TextStyle(color: AppTheme.muted),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 8),
        const _Disclaimer(),
      ],
    );
  }

  String _labelFor(String value) {
    switch (value) {
      case 'glioma':
        return 'Glioma';
      case 'meningioma':
        return 'Meningioma';
      case 'pituitario':
        return 'Tumor pituitario';
      case 'no_tumor':
        return 'Sin tumor';
      default:
        return value;
    }
  }
}

class _ProbabilityBar extends StatelessWidget {
  const _ProbabilityBar({
    required this.name,
    required this.value,
    required this.color,
  });

  final String name;
  final double value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(name, style: const TextStyle(fontSize: 13)),
              Text(
                '${(value * 100).toStringAsFixed(2)} %',
                style: const TextStyle(fontSize: 13, color: AppTheme.muted),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: value.clamp(0.0, 1.0),
              minHeight: 8,
              backgroundColor: const Color(0xFFE4E8EC),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }
}

class _Disclaimer extends StatelessWidget {
  const _Disclaimer();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF4E5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFF0C98A)),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline, size: 20, color: AppTheme.muted),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Herramienta de apoyo academico. No es un dispositivo medico y '
              'no sustituye el criterio de un radiologo.',
              style: TextStyle(fontSize: 12, color: AppTheme.muted, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}
