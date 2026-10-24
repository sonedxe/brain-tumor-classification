import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../viewmodels/prediction_viewmodel.dart';
import '../widgets/app_states.dart';
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
              const _HeroCard(),
              const SizedBox(height: AppSpacing.lg),
              const SectionHeader(
                icon: Icons.add_photo_alternate_outlined,
                title: 'Nueva clasificación',
                subtitle: 'Paso 1 · Sube una MRI · Paso 2 · Clasifica · Paso 3 · Revisa',
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
                const SectionHeader(
                  icon: Icons.verified_outlined,
                  title: 'Resultado',
                  subtitle: 'Etiqueta, confianza y mapa Grad-CAM',
                ),
                const SizedBox(height: AppSpacing.md),
                if (viewModel.usedOffline) ...[
                  Container(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    decoration: BoxDecoration(
                      color: AppTheme.infoSoft,
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      border: Border.all(
                        color: AppTheme.primary.withValues(alpha: 0.18),
                      ),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.offline_bolt_outlined,
                            size: 18, color: AppTheme.primary),
                        SizedBox(width: AppSpacing.sm),
                        Expanded(
                          child: Text(
                            'Calculado sin conexión con el modelo local. '
                            'Se enviará al backend al reconectar.',
                            style: TextStyle(
                              color: AppTheme.primaryDark,
                              fontSize: 12,
                              height: 1.35,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),
                ],
                ResultCard(
                  prediction: viewModel.prediction!,
                  gradcamUrl: viewModel.gradcamUrl,
                ),
              ] else if (viewModel.status == PredictionStatus.idle &&
                  viewModel.selectedImage == null) ...[
                const SizedBox(height: AppSpacing.lg),
                const _HowItWorks(),
              ],
              const SizedBox(height: AppSpacing.lg),
              const AppDisclaimer(),
            ],
          ),
        );
      },
    );
  }
}

/// Hero de bienvenida: primera impresión con gradiente de marca.
class _HeroCard extends StatelessWidget {
  const _HeroCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        gradient: AppTheme.brandGradient,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        boxShadow: AppShadow.button,
      ),
      child: Row(
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: const Icon(
              Icons.monitor_heart_outlined,
              color: Colors.white,
              size: 28,
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Análisis asistido de MRI',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                    fontSize: 17,
                    letterSpacing: -0.3,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'MobileNetV3 · Grad-CAM · 4 clases',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 12.5,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md,
              vertical: AppSpacing.sm,
            ),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(AppRadius.pill),
            ),
            child: const Row(
              children: [
                Icon(Icons.bolt, color: Colors.white, size: 14),
                SizedBox(width: 4),
                Text(
                  'IA real',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
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

/// Tres pasos siempre visibles hasta el primer resultado.
class _HowItWorks extends StatelessWidget {
  const _HowItWorks();

  @override
  Widget build(BuildContext context) {
    const steps = [
      (icon: Icons.upload_outlined, text: 'Sube la MRI'),
      (icon: Icons.auto_awesome_outlined, text: 'Clasifica'),
      (icon: Icons.history_outlined, text: 'Revisa el historial'),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Row(
          children: [
            for (var i = 0; i < steps.length; i++) ...[
              Expanded(
                child: Column(
                  children: [
                    Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(AppRadius.sm),
                      ),
                      child: Icon(
                        steps[i].icon,
                        color: AppTheme.primary,
                        size: 20,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      '${i + 1}. ${steps[i].text}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.muted,
                      ),
                    ),
                  ],
                ),
              ),
              if (i < steps.length - 1)
                const Padding(
                  padding: EdgeInsets.only(bottom: 28),
                  child: Icon(
                    Icons.chevron_right,
                    size: 16,
                    color: AppTheme.border,
                  ),
                ),
            ],
          ],
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
