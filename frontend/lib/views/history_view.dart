import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/formatting.dart';
import '../core/theme.dart';
import '../data/models/history_entry.dart';
import '../viewmodels/detail_viewmodel.dart';
import '../viewmodels/history_viewmodel.dart';
import '../widgets/app_states.dart';
import '../widgets/section_header.dart';
import 'prediction_detail_view.dart';

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

class _HistoryBody extends StatefulWidget {
  const _HistoryBody({required this.viewModel});

  final HistoryViewModel viewModel;

  @override
  State<_HistoryBody> createState() => _HistoryBodyState();
}

class _HistoryBodyState extends State<_HistoryBody> {
  String _filter = 'todos';

  List<HistoryEntry> get _filtered {
    final entries = widget.viewModel.entries;
    switch (_filter) {
      case 'tumor':
        return entries.where((e) => e.isTumor).toList();
      case 'no_tumor':
        return entries.where((e) => !e.isTumor).toList();
      default:
        return entries;
    }
  }

  @override
  Widget build(BuildContext context) {
    final viewModel = widget.viewModel;

    if (viewModel.isLoading && viewModel.entries.isEmpty) {
      return const AppLoading(message: 'Cargando historial…');
    }

    if (viewModel.hasError && viewModel.entries.isEmpty) {
      return AppErrorState(
        message: viewModel.errorMessage ?? 'No se pudo cargar',
        onRetry: () => viewModel.load(),
      );
    }

    if (viewModel.isEmpty) {
      return const AppEmptyState(
        icon: Icons.history_toggle_off_outlined,
        title: 'Aún no hay predicciones',
        message: 'Clasifica una imagen y aparecerá aquí con su confianza y '
            'versión del modelo. Toca una tarjeta para ver el detalle.',
      );
    }

    final filtered = _filtered;

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: [
        const SectionHeader(
          icon: Icons.history_outlined,
          title: 'Predicciones recientes',
          subtitle: 'Toca una tarjeta para ver detalle y dar feedback',
        ),
        const SizedBox(height: AppSpacing.md),
        Wrap(
          spacing: AppSpacing.sm,
          children: [
            _FilterChip(
              label: 'Todos (${viewModel.entries.length})',
              selected: _filter == 'todos',
              onTap: () => setState(() => _filter = 'todos'),
            ),
            _FilterChip(
              label:
                  'Tumor (${viewModel.entries.where((e) => e.isTumor).length})',
              selected: _filter == 'tumor',
              onTap: () => setState(() => _filter = 'tumor'),
            ),
            _FilterChip(
              label:
                  'Sin tumor (${viewModel.entries.where((e) => !e.isTumor).length})',
              selected: _filter == 'no_tumor',
              onTap: () => setState(() => _filter = 'no_tumor'),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.md),
        if (filtered.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: AppSpacing.xl),
            child: Text(
              'Sin resultados para este filtro.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppTheme.muted),
            ),
          )
        else
          ...filtered.map((entry) => _HistoryTile(entry: entry)),
      ],
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => onTap(),
      selectedColor: AppTheme.primary.withValues(alpha: 0.14),
      labelStyle: TextStyle(
        color: selected ? AppTheme.primaryDark : AppTheme.muted,
        fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
      ),
      side: BorderSide(
        color: selected ? AppTheme.primary : AppTheme.border,
      ),
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
      child: InkWell(
        borderRadius: BorderRadius.circular(AppRadius.lg),
        onTap: entry.pendingSync
            ? null
            : () {
                // El DetailViewModel es global (ver main.dart).
                context.read<DetailViewModel>().load(entry.id);
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        PredictionDetailView(predictionId: entry.id),
                  ),
                );
              },
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
                    if (entry.pendingSync) ...[
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.sm,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.warningSoft,
                          borderRadius: BorderRadius.circular(AppRadius.pill),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.cloud_upload_outlined,
                              size: 12,
                              color: AppTheme.warning,
                            ),
                            SizedBox(width: 4),
                            Text(
                              'Pendiente de sincronizar',
                              style: TextStyle(
                                color: AppTheme.warning,
                                fontSize: 10.5,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
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
              const SizedBox(width: AppSpacing.sm),
              if (entry.pendingSync)
                const Icon(
                  Icons.cloud_off_outlined,
                  color: AppTheme.warning,
                  size: 20,
                )
              else
                const Icon(
                  Icons.chevron_right,
                  color: AppTheme.muted,
                  size: 20,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
