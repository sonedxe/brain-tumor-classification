import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/formatting.dart';
import '../core/theme.dart';
import '../data/models/history_entry.dart';
import '../viewmodels/history_viewmodel.dart';
import '../widgets/section_header.dart';

/// Historial de predicciones (RF-05).
///
/// MVVM: la vista no hace HTTP ni parsea JSON. Observa el
/// [HistoryViewModel] y le pide `load()` (aqui y en el pull-to-refresh).
class HistoryView extends StatelessWidget {
  const HistoryView({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<HistoryViewModel>(
      builder: (context, viewModel, _) {
        return RefreshIndicator(
          onRefresh: () => viewModel.load(),
          child: _HistoryBody(viewModel: viewModel),
        );
      },
    );
  }
}

class _HistoryBody extends StatelessWidget {
  const _HistoryBody({required this.viewModel});

  final HistoryViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    if (viewModel.isLoading && viewModel.entries.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (viewModel.hasError) {
      return _CenteredMessage(
        icon: Icons.cloud_off_outlined,
        title: 'No se pudo cargar el historial',
        message: viewModel.errorMessage ?? '',
        action: TextButton.icon(
          onPressed: () => viewModel.load(),
          icon: const Icon(Icons.refresh),
          label: const Text('Reintentar'),
        ),
      );
    }

    if (viewModel.isEmpty) {
      return const _CenteredMessage(
        icon: Icons.history_toggle_off_outlined,
        title: 'Aun no hay predicciones',
        message: 'Clasifica una imagen y aparecera aqui con su confianza y '
            'version del modelo.',
      );
    }

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: [
        SectionHeader(
          title: 'Predicciones recientes',
          subtitle:
              '${viewModel.entries.length} registro(s) · desliza para actualizar',
        ),
        const SizedBox(height: AppSpacing.md),
        ...viewModel.entries.map((entry) => _HistoryTile(entry: entry)),
      ],
    );
  }
}

class _HistoryTile extends StatelessWidget {
  const _HistoryTile({required this.entry});

  final HistoryEntry entry;

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.classColor(entry.label);
    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Row(
          children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(AppRadius.sm),
              ),
              child: Icon(
                entry.isTumor
                    ? Icons.warning_amber_rounded
                    : Icons.verified_outlined,
                color: color,
                size: 24,
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    className(entry.label),
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 15.5,
                      color: color,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Row(
                    children: [
                      const Icon(
                        Icons.schedule,
                        size: 13,
                        color: AppTheme.muted,
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      Text(
                        formatTimestamp(entry.createdAt),
                        style: const TextStyle(
                          color: AppTheme.muted,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    entry.modelVersion,
                    style: const TextStyle(
                      color: AppTheme.muted,
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: AppSpacing.sm,
              ),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(AppRadius.pill),
              ),
              child: Text(
                '${entry.confidencePercent.toStringAsFixed(1)} %',
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.w800,
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Mensaje centrado que sigue siendo desplazable para que el
/// `RefreshIndicator` funcione sobre una pantalla vacia.
class _CenteredMessage extends StatelessWidget {
  const _CenteredMessage({
    required this.icon,
    required this.title,
    required this.message,
    this.action,
  });

  final IconData icon;
  final String title;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: ConstrainedBox(
          constraints: BoxConstraints(minHeight: constraints.maxHeight),
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.xl),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 76,
                    height: 76,
                    decoration: BoxDecoration(
                      color: AppTheme.soft,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(icon, size: 36, color: AppTheme.primary),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  Text(
                    title,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    message,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: AppTheme.muted,
                      fontSize: 13.5,
                      height: 1.4,
                    ),
                  ),
                  if (action != null) ...[
                    const SizedBox(height: AppSpacing.md),
                    action!,
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
