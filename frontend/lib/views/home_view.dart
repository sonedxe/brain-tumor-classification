import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../viewmodels/prediction_viewmodel.dart';
import '../widgets/image_picker_button.dart';
import '../widgets/primary_gradient_button.dart';
import '../widgets/result_card.dart';
import '../widgets/section_header.dart';

/// Vista principal.
///
/// MVVM: no contiene llamadas HTTP, no lee `dart:io` y no contiene reglas.
/// Solo lee el estado del ViewModel y emite intents.
class HomeView extends StatelessWidget {
  const HomeView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: SafeArea(child: HomeViewContent()),
    );
  }
}

/// Contenido del home sin Scaffold, reutilizable dentro de [AppShell].
class HomeViewContent extends StatelessWidget {
  const HomeViewContent({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<PredictionViewModel>(
      builder: (context, viewModel, _) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const _StudyHint(),
              const SizedBox(height: AppSpacing.lg),
              const SectionHeader(
                title: 'Nueva clasificacion',
                subtitle: 'Sube una MRI cerebral para analizarla',
              ),
              const SizedBox(height: AppSpacing.md),
              ImagePickerButton(
                image: viewModel.selectedImage,
                isBusy: viewModel.isBusy,
                onPickGallery: viewModel.pickFromGallery,
                onPickCamera: viewModel.pickFromCamera,
                onClear: viewModel.clear,
              ),
              const SizedBox(height: AppSpacing.lg),
              PrimaryGradientButton(
                label: viewModel.isBusy ? 'Analizando...' : 'Clasificar imagen',
                icon: Icons.auto_awesome,
                busy: viewModel.isBusy,
                onPressed: viewModel.canClassify ? viewModel.classify : null,
              ),
              if (viewModel.status == PredictionStatus.error) ...[
                const SizedBox(height: AppSpacing.lg),
                _ErrorBanner(message: viewModel.errorMessage ?? ''),
              ],
              if (viewModel.hasResult) ...[
                const SizedBox(height: AppSpacing.xl),
                ResultCard(
                  prediction: viewModel.prediction!,
                  gradcamUrl: viewModel.gradcamUrl,
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}

/// Recordatorio de uso responsable, siempre visible.
class _StudyHint extends StatelessWidget {
  const _StudyHint();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppTheme.primary.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.12)),
      ),
      child: Row(
        children: [
          const Icon(Icons.school_outlined, color: AppTheme.primary, size: 20),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              'Apoyo academico. No sustituye el diagnostico de un radiologo.',
              style: TextStyle(
                fontSize: 12.5,
                color: AppTheme.primaryDark,
                height: 1.3,
              ),
            ),
          ),
        ],
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
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppTheme.errorSoft,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppTheme.error.withValues(alpha: 0.30)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, size: 20, color: AppTheme.error),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                fontSize: 13.5,
                color: AppTheme.error,
                height: 1.4,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
