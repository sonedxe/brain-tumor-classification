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
              return const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Text(
                    'Todavia no hay ningun resultado que mostrar.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppTheme.muted),
                  ),
                ),
              );
            }

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: ResultCard(
                prediction: result,
                gradcamUrl: viewModel.gradcamUrl,
              ),
            );
          },
        ),
      ),
    );
  }
}
