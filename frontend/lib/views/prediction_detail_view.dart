import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/formatting.dart';
import '../core/theme.dart';
import '../viewmodels/detail_viewmodel.dart';
import '../widgets/app_states.dart';

/// Detalle de una predicción del historial + feedback humano.
///
/// Abre con el `id` de `GET /history` y pide `GET /predictions/{id}`.
/// MVVM: la vista solo lee [DetailViewModel] y emite intents.
class PredictionDetailView extends StatefulWidget {
  const PredictionDetailView({super.key, required this.predictionId});

  final int predictionId;

  @override
  State<PredictionDetailView> createState() => _PredictionDetailViewState();
}

class _PredictionDetailViewState extends State<PredictionDetailView> {
  String? _correctedLabel;
  final _commentController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DetailViewModel>().load(widget.predictionId);
    });
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 70,
        backgroundColor: Colors.transparent,
        flexibleSpace: Container(
          decoration: const BoxDecoration(gradient: AppTheme.brandGradient),
        ),
        title: Text('#${widget.predictionId} Detalle'),
      ),
      body: SafeArea(
        child: Consumer<DetailViewModel>(
          builder: (context, viewModel, _) {
            if (viewModel.isLoading) {
              return const AppLoading(message: 'Cargando detalle…');
            }
            if (viewModel.hasError) {
              return AppErrorState(
                message: viewModel.errorMessage ?? 'Error',
                onRetry: () => viewModel.load(widget.predictionId),
              );
            }
            final detail = viewModel.detail;
            if (detail == null) {
              return const AppEmptyState(
                icon: Icons.search_off_outlined,
                title: 'Sin detalle',
                message: 'No se encontró la predicción solicitada.',
              );
            }

            final sorted = detail.probabilities.entries.toList()
              ..sort((a, b) => b.value.compareTo(a.value));
            final gradcamUrl = viewModel.gradcamUrl(detail.gradcamPath);
            final color = AppTheme.classColor(detail.label);

            return ListView(
              padding: const EdgeInsets.all(AppSpacing.lg),
              children: [
                Card(
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
                            colors: [
                              color,
                              Color.lerp(color, Colors.black, 0.18)!
                            ],
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              detail.isTumor
                                  ? Icons.warning_amber_rounded
                                  : Icons.check_circle_outline,
                              color: Colors.white,
                              size: 20,
                            ),
                            const SizedBox(width: AppSpacing.sm),
                            Text(
                              detail.isTumor
                                  ? 'Hallazgo detectado'
                                  : 'Sin hallazgos tumorales',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w700,
                                fontSize: 14,
                              ),
                            ),
                            const Spacer(),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: AppSpacing.md,
                                vertical: AppSpacing.xs,
                              ),
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.22),
                                borderRadius:
                                    BorderRadius.circular(AppRadius.pill),
                              ),
                              child: Text(
                                '${(detail.confidence * 100).toStringAsFixed(1)} %',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(AppSpacing.lg),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              className(detail.label),
                              style: Theme.of(context)
                                  .textTheme
                                  .headlineSmall
                                  ?.copyWith(color: color),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${detail.inferenceMs.toStringAsFixed(1)} ms · ${detail.modelVersion} (${detail.architecture})',
                              style: const TextStyle(
                                color: AppTheme.muted,
                                fontSize: 12.5,
                              ),
                            ),
                            Text(
                              '${formatTimestamp(detail.createdAt)} · ${detail.feedbackCount} revisión(es)',
                              style: const TextStyle(
                                color: AppTheme.muted,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.md),
                AppSectionCard(
                  icon: Icons.bar_chart_outlined,
                  iconColor: AppTheme.primary,
                  title: 'Probabilidades',
                  subtitle: 'Distribución completa del modelo',
                  child: Column(
                    children: sorted
                        .map(
                          (e) => Padding(
                            padding:
                                const EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              children: [
                                Container(
                                  width: 10,
                                  height: 10,
                                  decoration: BoxDecoration(
                                    color: AppTheme.classColor(e.key),
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: AppSpacing.sm),
                                Expanded(child: Text(className(e.key))),
                                Text(
                                    '${(e.value * 100).toStringAsFixed(1)} %'),
                              ],
                            ),
                          ),
                        )
                        .toList(),
                  ),
                ),
                if (gradcamUrl != null) ...[
                  const SizedBox(height: AppSpacing.md),
                  AppSectionCard(
                    icon: Icons.blur_on,
                    iconColor: AppTheme.accent,
                    title: 'Mapa de calor Grad-CAM',
                    subtitle: 'Zona que el modelo usó para decidir',
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      child: Image.network(
                        gradcamUrl.toString(),
                        fit: BoxFit.contain,
                        errorBuilder: (_, _, _) => const SizedBox(
                          height: 140,
                          child: Center(child: Text('Sin Grad-CAM')),
                        ),
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: AppSpacing.md),
                _FeedbackCard(
                  viewModel: viewModel,
                  correctedLabel: _correctedLabel,
                  commentController: _commentController,
                  onLabelChanged: (v) => setState(() => _correctedLabel = v),
                ),
                const SizedBox(height: AppSpacing.lg),
                const AppDisclaimer(),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _FeedbackCard extends StatelessWidget {
  const _FeedbackCard({
    required this.viewModel,
    required this.correctedLabel,
    required this.commentController,
    required this.onLabelChanged,
  });

  final DetailViewModel viewModel;
  final String? correctedLabel;
  final TextEditingController commentController;
  final ValueChanged<String?> onLabelChanged;

  @override
  Widget build(BuildContext context) {
    const classes = ['glioma', 'meningioma', 'pituitario', 'no_tumor'];
    return AppSectionCard(
      icon: Icons.feedback_outlined,
      iconColor: AppTheme.accent,
      title: '¿El resultado es correcto?',
      subtitle: 'Tu revisión alimenta el human-in-the-loop',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: viewModel.isSending
                      ? null
                      : () => viewModel.sendFeedback(isCorrect: true),
                  icon: const Icon(Icons.thumb_up_outlined, size: 18),
                  label: const Text('Correcto'),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: viewModel.isSending
                      ? null
                      : () => viewModel.sendFeedback(
                            isCorrect: false,
                            correctedLabel: correctedLabel,
                            comment: commentController.text,
                          ),
                  icon: const Icon(Icons.thumb_down_outlined, size: 18),
                  label: const Text('Corregir'),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          DropdownButtonFormField<String>(
            initialValue: correctedLabel,
            decoration: const InputDecoration(
              labelText: 'Clase correcta (opcional)',
            ),
            items: classes
                .map((c) => DropdownMenuItem(
                      value: c,
                      child: Text(className(c)),
                    ))
                .toList(),
            onChanged: onLabelChanged,
          ),
          const SizedBox(height: AppSpacing.md),
          TextField(
            controller: commentController,
            decoration: const InputDecoration(
              labelText: 'Comentario (opcional)',
              hintText: 'Ej. artefacto en la imagen…',
            ),
            maxLength: 255,
          ),
          if (viewModel.isSending)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: LinearProgressIndicator(),
            ),
          if (viewModel.feedbackMessage != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: AppTheme.successSoft,
                borderRadius: BorderRadius.circular(AppRadius.sm),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle_outline,
                      color: AppTheme.success, size: 18),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Text(
                      viewModel.feedbackMessage!,
                      style: const TextStyle(
                        color: AppTheme.success,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
