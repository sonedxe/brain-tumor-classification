import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/config.dart';
import '../core/theme.dart';
import '../viewmodels/prediction_viewmodel.dart';
import '../widgets/image_picker_button.dart';
import '../widgets/result_card.dart';

/// Vista principal.
///
/// MVVM: no contiene llamadas HTTP, no lee `dart:io` y no contiene reglas.
/// Solo lee el estado del ViewModel y emite intents.
class HomeView extends StatelessWidget {
  const HomeView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(AppConfig.appTitle),
      ),
      body: SafeArea(
        child: Consumer<PredictionViewModel>(
          builder: (context, viewModel, _) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ImagePickerButton(
                    image: viewModel.selectedImage,
                    isBusy: viewModel.isBusy,
                    onPickGallery: viewModel.pickFromGallery,
                    onPickCamera: viewModel.pickFromCamera,
                    onClear: viewModel.clear,
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    onPressed:
                        viewModel.canClassify ? viewModel.classify : null,
                    icon: viewModel.isBusy
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.biotech_outlined),
                    label: Text(
                      viewModel.isBusy ? 'Analizando...' : 'Clasificar',
                    ),
                  ),
                  if (viewModel.status == PredictionStatus.error) ...[
                    const SizedBox(height: 16),
                    _ErrorBanner(message: viewModel.errorMessage ?? ''),
                  ],
                  if (viewModel.hasResult) ...[
                    const SizedBox(height: 20),
                    ResultCard(
                      prediction: viewModel.prediction!,
                      gradcamUrl: viewModel.gradcamUrl,
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFDEDEC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFF5B7B1)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, size: 20, color: AppTheme.error),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                fontSize: 13,
                color: AppTheme.error,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
