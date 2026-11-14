import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/confidence.dart';
import '../core/formatting.dart';
import '../core/theme.dart';
import '../data/models/history_entry.dart';
import '../viewmodels/detail_viewmodel.dart';
import '../viewmodels/history_viewmodel.dart';
import '../widgets/app_states.dart';
import '../widgets/export_pdf_button.dart';
import '../widgets/section_header.dart';
import 'prediction_detail_view.dart';

/// Historial de predicciones (RF-05).
///
/// MVVM: la vista no hace HTTP ni parsea JSON. Observa el
/// [HistoryViewModel]; busqueda, filtro y orden viven en el ViewModel.
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
  final TextEditingController _search = TextEditingController();

  static const _filters = [
    (code: classFilterAll, label: 'Todas'),
    (code: 'glioma', label: 'Glioma'),
    (code: 'meningioma', label: 'Meningioma'),
    (code: 'no_tumor', label: 'Sin Tumor'),
    (code: 'pituitario', label: 'Pituitaria'),
  ];

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
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

    final visible = viewModel.visibleEntries;

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: [
        const SectionHeader(
          icon: Icons.history_outlined,
          title: 'Predicciones recientes',
          subtitle: 'Busca, filtra por lesión y exporta el informe PDF',
        ),
        const SizedBox(height: AppSpacing.md),
        TextField(
          controller: _search,
          onChanged: viewModel.setQuery,
          textInputAction: TextInputAction.search,
          decoration: InputDecoration(
            hintText: 'Buscar por clase, modelo o fecha',
            prefixIcon: const Icon(Icons.search),
            suffixIcon: viewModel.query.isEmpty
                ? null
                : IconButton(
                    tooltip: 'Borrar búsqueda',
                    icon: const Icon(Icons.close),
                    onPressed: () {
                      _search.clear();
                      viewModel.setQuery('');
                    },
                  ),
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        SizedBox(
          height: 40,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: _filters.length,
            separatorBuilder: (_, __) => const SizedBox(width: AppSpacing.sm),
            itemBuilder: (context, index) {
              final filter = _filters[index];
              return _FilterChip(
                label: '${filter.label} (${viewModel.countFor(filter.code)})',
                selected: viewModel.classFilter == filter.code,
                onTap: () => viewModel.setClassFilter(filter.code),
              );
            },
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        Row(
          children: [
            Expanded(
              child: Text(
                '${visible.length} de ${viewModel.entries.length} análisis',
                style: const TextStyle(color: AppTheme.muted, fontSize: 12.5),
              ),
            ),
            SegmentedButton<bool>(
              showSelectedIcon: false,
              style: const ButtonStyle(
                visualDensity: VisualDensity.compact,
              ),
              segments: const [
                ButtonSegment(value: true, label: Text('Más recientes')),
                ButtonSegment(value: false, label: Text('Más antiguos')),
              ],
              selected: {viewModel.newestFirst},
              onSelectionChanged: (value) =>
                  viewModel.setNewestFirst(value.first),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.md),
        if (visible.isEmpty)
          _NoMatches(
            onClear: () {
              _search.clear();
              viewModel.clearFilters();
            },
          )
        else
          ...visible.map(
            (entry) => _HistoryTile(
              entry: entry,
              thumbnail: viewModel.thumbnailUrl(entry),
            ),
          ),
      ],
    );
  }
}

class _NoMatches extends StatelessWidget {
  const _NoMatches({required this.onClear});

  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.xl),
      child: Column(
        children: [
          const Icon(Icons.search_off, size: 44, color: AppTheme.muted),
          const SizedBox(height: AppSpacing.md),
          Text(
            'Sin coincidencias',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: AppSpacing.xs),
          const Text(
            'Ningún análisis cumple la búsqueda o el filtro actual.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppTheme.muted),
          ),
          const SizedBox(height: AppSpacing.md),
          OutlinedButton.icon(
            onPressed: onClear,
            icon: const Icon(Icons.filter_alt_off_outlined),
            label: const Text('Limpiar filtros'),
          ),
        ],
      ),
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
  const _HistoryTile({required this.entry, required this.thumbnail});

  final HistoryEntry entry;
  final Uri? thumbnail;

  void _openDetail(BuildContext context) {
    // El DetailViewModel es global (ver main.dart).
    context.read<DetailViewModel>().load(entry.id);
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PredictionDetailView(predictionId: entry.id),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.classColor(entry.label);
    final level = confidenceLevelOf(entry.confidence);

    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _Thumbnail(url: thumbnail, color: color, isTumor: entry.isTumor),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Wrap(
                        spacing: AppSpacing.sm,
                        runSpacing: AppSpacing.xs,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.md,
                              vertical: AppSpacing.xs + 1,
                            ),
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.12),
                              borderRadius:
                                  BorderRadius.circular(AppRadius.pill),
                            ),
                            child: Text(
                              className(entry.label),
                              style: TextStyle(
                                color: color,
                                fontWeight: FontWeight.w800,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          if (entry.pendingSync) const _PendingBadge(),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Row(
                        children: [
                          Icon(level.icon, size: 16, color: level.color),
                          const SizedBox(width: AppSpacing.xs),
                          Text(
                            '${entry.confidencePercent.toStringAsFixed(1)} %',
                            style: TextStyle(
                              color: level.color,
                              fontWeight: FontWeight.w800,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Flexible(
                            child: Text(
                              level.label,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                color: level.color,
                                fontSize: 11.5,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Row(
                        children: [
                          const Icon(
                            Icons.schedule,
                            size: 13,
                            color: AppTheme.muted,
                          ),
                          const SizedBox(width: AppSpacing.xs),
                          Flexible(
                            child: Text(
                              formatTimestamp(entry.createdAt),
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                color: AppTheme.muted,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
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
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            if (entry.pendingSync)
              const Text(
                'Se podrá ver el detalle y exportar el PDF al sincronizar.',
                style: TextStyle(color: AppTheme.muted, fontSize: 12),
              )
            else
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _openDetail(context),
                      icon: const Icon(Icons.visibility_outlined, size: 18),
                      label: const Text('Ver detalle'),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  ExportPdfButton(predictionId: entry.id, compact: true),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _Thumbnail extends StatelessWidget {
  const _Thumbnail({
    required this.url,
    required this.color,
    required this.isTumor,
  });

  final Uri? url;
  final Color color;
  final bool isTumor;

  @override
  Widget build(BuildContext context) {
    final fallback = Container(
      color: color.withValues(alpha: 0.12),
      alignment: Alignment.center,
      child: Icon(
        isTumor ? Icons.warning_amber_rounded : Icons.verified_outlined,
        color: color,
        size: 28,
      ),
    );

    return ClipRRect(
      borderRadius: BorderRadius.circular(AppRadius.sm),
      child: SizedBox(
        width: 76,
        height: 76,
        child: url == null
            ? fallback
            : Image.network(
                url.toString(),
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => fallback,
                loadingBuilder: (context, child, progress) =>
                    progress == null ? child : fallback,
              ),
      ),
    );
  }
}

class _PendingBadge extends StatelessWidget {
  const _PendingBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
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
          Icon(Icons.cloud_upload_outlined, size: 12, color: AppTheme.warning),
          SizedBox(width: 4),
          Text(
            'Pendiente',
            style: TextStyle(
              color: AppTheme.warning,
              fontSize: 10.5,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
