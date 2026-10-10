import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../core/formatting.dart';
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

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.classColor(prediction.label);
    final sorted = prediction.probabilities.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _VerdictCard(prediction: prediction, color: color),
        if (sorted.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.lg),
          _ProbabilitiesCard(entries: sorted),
        ],
        if (gradcamUrl != null) ...[
          const SizedBox(height: AppSpacing.lg),
          _GradCamCard(url: gradcamUrl!),
        ],
        const SizedBox(height: AppSpacing.lg),
        const _Disclaimer(),
      ],
    );
  }
}

/// Veredicto: etiqueta, estado y medidor de confianza.
class _VerdictCard extends StatelessWidget {
  const _VerdictCard({required this.prediction, required this.color});

  final PredictionModel prediction;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.lg,
              vertical: AppSpacing.md,
            ),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [color, Color.lerp(color, Colors.black, 0.18)!],
              ),
            ),
            child: Row(
              children: [
                Icon(
                  prediction.isTumor
                      ? Icons.warning_amber_rounded
                      : Icons.check_circle_outline,
                  color: Colors.white,
                  size: 20,
                ),
                const SizedBox(width: AppSpacing.sm),
                Text(
                  prediction.isTumor
                      ? 'Hallazgo detectado'
                      : 'Sin hallazgos tumorales',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(AppSpacing.xl),
            child: Row(
              children: [
                _ConfidenceGauge(
                  value: prediction.confidence,
                  color: color,
                ),
                const SizedBox(width: AppSpacing.xl),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Resultado',
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              color: AppTheme.muted,
                            ),
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        className(prediction.label),
                        style: Theme.of(context)
                            .textTheme
                            .headlineSmall
                            ?.copyWith(
                              color: color,
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      Wrap(
                        spacing: AppSpacing.sm,
                        runSpacing: AppSpacing.sm,
                        children: [
                          _MetaChip(
                            icon: Icons.speed,
                            text:
                                '${prediction.inferenceMs.toStringAsFixed(1)} ms',
                          ),
                          _MetaChip(
                            icon: Icons.memory,
                            text: prediction.modelVersion,
                          ),
                        ],
                      ),
                    ],
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

class _ConfidenceGauge extends StatelessWidget {
  const _ConfidenceGauge({required this.value, required this.color});

  final double value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final clamped = value.clamp(0.0, 1.0);
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: clamped),
      duration: const Duration(milliseconds: 900),
      curve: Curves.easeOutCubic,
      builder: (context, animated, _) {
        return SizedBox(
          width: 96,
          height: 96,
          child: Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 96,
                height: 96,
                child: CircularProgressIndicator(
                  value: animated,
                  strokeWidth: 9,
                  strokeCap: StrokeCap.round,
                  backgroundColor: color.withValues(alpha: 0.12),
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    (animated * 100).toStringAsFixed(1),
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                      color: color,
                      height: 1,
                    ),
                  ),
                  const Text(
                    '% conf.',
                    style: TextStyle(fontSize: 10.5, color: AppTheme.muted),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.xs + 2,
      ),
      decoration: BoxDecoration(
        color: AppTheme.soft,
        borderRadius: BorderRadius.circular(AppRadius.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppTheme.muted),
          const SizedBox(width: AppSpacing.xs),
          Text(
            text,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppTheme.onSurface,
            ),
          ),
        ],
      ),
    );
  }
}

/// Probabilidades por clase, ordenadas de mayor a menor.
class _ProbabilitiesCard extends StatelessWidget {
  const _ProbabilitiesCard({required this.entries});

  final List<MapEntry<String, double>> entries;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Probabilidades por clase',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
            ),
            const SizedBox(height: AppSpacing.md),
            ...entries.map(
              (entry) => _ProbabilityBar(
                name: entry.key,
                value: entry.value,
                color: AppTheme.classColor(entry.key),
              ),
            ),
          ],
        ),
      ),
    );
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
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                name,
                style: const TextStyle(
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Text(
                '${(value * 100).toStringAsFixed(1)} %',
                style: const TextStyle(
                  fontSize: 13,
                  color: AppTheme.muted,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xs + 2),
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: value.clamp(0.0, 1.0)),
            duration: const Duration(milliseconds: 800),
            curve: Curves.easeOutCubic,
            builder: (context, animated, _) => ClipRRect(
              borderRadius: BorderRadius.circular(AppRadius.pill),
              child: LinearProgressIndicator(
                value: animated,
                minHeight: 8,
                backgroundColor: const Color(0xFFE9EEF5),
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GradCamCard extends StatelessWidget {
  const _GradCamCard({required this.url});

  final Uri url;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: AppTheme.accent.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                  child: const Icon(
                    Icons.blur_on,
                    color: AppTheme.accent,
                    size: 20,
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Mapa de calor Grad-CAM',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                      ),
                      Text(
                        'Zona que el modelo uso para decidir',
                        style: TextStyle(
                          color: AppTheme.muted,
                          fontSize: 12.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Image.network(
            url.toString(),
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
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppTheme.warningSoft,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: const Color(0xFFF0C98A)),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline, size: 20, color: AppTheme.warning),
          SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              'Herramienta de apoyo academico. No es un dispositivo medico y '
              'no sustituye el criterio de un radiologo.',
              style: TextStyle(
                fontSize: 12.5,
                color: AppTheme.warning,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
