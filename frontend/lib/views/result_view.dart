import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../data/models/prediction_model.dart';
import '../viewmodels/prediction_viewmodel.dart';
import '../widgets/result_card.dart';

/// Vista de detalle del resultado.
///
/// Existe separada de `HomeView` para que la navegacion cuando se integre el
/// historial no complique la pantalla principal. Comparte el mismo
/// ViewModel, por lo que no duplica estado.
class ResultView extends StatelessWidget {
  const ResultView({super.key, this.prediction});

  final PredictionModel? prediction;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 70,
        backgroundColor: Colors.transparent,
        flexibleSpace: Container(
          decoration: const BoxDecoration(gradient: AppTheme.brandGradient),
        ),
        title: const Text('Resultado del analisis'),
        actions: [
          IconButton(
            tooltip: 'Limpiar',
            onPressed: () {
              context.read<PredictionViewModel>().clear();
              Navigator.of(context).pop();
            },
            icon: const Icon(Icons.delete_outline),
          ),
        ],
      ),
      body: SafeArea(
        child: Consumer<PredictionViewModel>(
          builder: (context, viewModel, _) {
            final result = prediction ?? viewModel.prediction;

            if (result == null) {
              return const _EmptyResult();
            }

            return ListView(
              padding: const EdgeInsets.all(AppSpacing.lg),
              children: [
                ResultCard(
                  prediction: result,
                  gradcamUrl: viewModel.gradcamUrl,
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _EmptyResult extends StatelessWidget {
  const _EmptyResult();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 76,
              height: 76,
              decoration: const BoxDecoration(
                color: AppTheme.soft,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.image_search,
                size: 36,
                color: AppTheme.primary,
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              'Todavia no hay ningun resultado que mostrar.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: AppSpacing.xs),
            const Text(
              'Clasifica una imagen desde la pantalla Analizar.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppTheme.muted),
            ),
          ],
        ),
      ),
    );
  }
}
