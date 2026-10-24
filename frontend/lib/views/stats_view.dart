import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/formatting.dart';
import '../core/theme.dart';
import '../viewmodels/stats_viewmodel.dart';
import '../widgets/app_states.dart';
import '../widgets/section_header.dart';

/// Dashboard de uso: consume `GET /stats/summary`.
///
/// MVVM: solo observa el ViewModel y pide `load()`.
class StatsView extends StatelessWidget {
  const StatsView({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<StatsViewModel>(
      builder: (context, viewModel, _) {
        return RefreshIndicator(
          onRefresh: () => viewModel.load(),
          child: _StatsBody(viewModel: viewModel),
        );
      },
    );
  }
}

class _StatsBody extends StatelessWidget {
  const _StatsBody({required this.viewModel});

  final StatsViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    if (viewModel.isLoading && viewModel.summary == null) {
      return const AppLoading(message: 'Cargando panel…');
    }
    if (viewModel.hasError && viewModel.summary == null) {
      return AppErrorState(
        message: viewModel.errorMessage ?? 'No se pudo cargar',
        onRetry: () => viewModel.load(),
      );
    }

    final summary = viewModel.summary;
    if (summary == null) {
      return const AppEmptyState(
        icon: Icons.dashboard_outlined,
        title: 'Sin datos todavía',
        message: 'Clasifica una imagen para estrenar el panel.',
      );
    }

    final maxCount = summary.byClass.fold<int>(
      1,
      (prev, e) => e.count > prev ? e.count : prev,
    );

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: [
        const SectionHeader(
          icon: Icons.dashboard_outlined,
          title: 'Panel de uso',
          subtitle: 'Actividad registrada por el backend',
        ),
        const SizedBox(height: AppSpacing.md),
        GridView.count(
          crossAxisCount: 3,
          crossAxisSpacing: AppSpacing.md,
          mainAxisSpacing: AppSpacing.md,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 0.92,
          children: [
            _Kpi(
              icon: Icons.biotech_outlined,
              label: 'Predicciones',
              value: '${summary.totalPredictions}',
            ),
            _Kpi(
              icon: Icons.image_outlined,
              label: 'Imágenes únicas',
              value: '${summary.uniqueImages}',
            ),
            _Kpi(
              icon: Icons.speed,
              label: 'Latencia media',
              value: summary.avgInferenceMs == null
                  ? '—'
                  : '${summary.avgInferenceMs!.toStringAsFixed(1)} ms',
            ),
            _Kpi(
              icon: Icons.verified_outlined,
              label: 'Confianza media',
              value: summary.avgConfidence == null
                  ? '—'
                  : '${(summary.avgConfidence! * 100).toStringAsFixed(1)} %',
            ),
            _Kpi(
              icon: Icons.feedback_outlined,
              label: 'Revisiones',
              value: '${summary.totalFeedback}',
            ),
            _Kpi(
              icon: Icons.memory_outlined,
              label: 'Modelos',
              value: '${summary.modelsRegistered}',
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.lg),
        AppSectionCard(
          icon: Icons.pie_chart_outline,
          iconColor: AppTheme.primary,
          title: 'Distribución por clase',
          subtitle: 'Conteo y confianza media',
          child: summary.byClass.isEmpty
              ? const Text(
                  'Aún no hay predicciones registradas.',
                  style: TextStyle(color: AppTheme.muted),
                )
              : Column(
                  children: summary.byClass
                      .map(
                        (stat) => _ClassBar(
                          code: stat.code,
                          count: stat.count,
                          maxCount: maxCount,
                          avgConfidence: stat.avgConfidence,
                        ),
                      )
                      .toList(),
                ),
        ),
        const SizedBox(height: AppSpacing.md),
        const Text(
          'Fuente: GET /stats/summary · desliza para actualizar',
          style: TextStyle(color: AppTheme.muted, fontSize: 12),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _Kpi extends StatelessWidget {
  const _Kpi({required this.icon, required this.label, required this.value});

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(
          vertical: AppSpacing.md,
          horizontal: AppSpacing.sm,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppTheme.primary.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(AppRadius.sm),
              ),
              child: Icon(icon, color: AppTheme.primary, size: 19),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              value,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 15,
              ),
            ),
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppTheme.muted, fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}

class _ClassBar extends StatelessWidget {
  const _ClassBar({
    required this.code,
    required this.count,
    required this.maxCount,
    this.avgConfidence,
  });

  final String code;
  final int count;
  final int maxCount;
  final double? avgConfidence;

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.classColor(code);
    final fraction = maxCount == 0 ? 0.0 : count / maxCount;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 10,
                    height: 10,
                    decoration:
                        BoxDecoration(color: color, shape: BoxShape.circle),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Text(
                    className(code),
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 13.5),
                  ),
                ],
              ),
              Text(
                avgConfidence == null
                    ? '$count'
                    : '$count · ${(avgConfidence! * 100).toStringAsFixed(1)} %',
                style: const TextStyle(color: AppTheme.muted, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          ClipRRect(
            borderRadius: BorderRadius.circular(AppRadius.pill),
            child: LinearProgressIndicator(
              value: fraction.clamp(0.0, 1.0),
              minHeight: 8,
              backgroundColor: const Color(0xFFE9EEF5),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }
}
