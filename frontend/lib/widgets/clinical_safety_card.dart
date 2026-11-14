import 'package:flutter/material.dart';

import '../core/theme.dart';

/// Tarjeta de la capa de seguridad clínica.
///
/// MVVM: recibe los datos ya calculados (por el backend o por
/// [ClinicalAssessment]) y solo los presenta. Muestra el nivel de triaje, la
/// recomendación y, cuando corresponde, la ruta de derivación a especialista.
class ClinicalSafetyCard extends StatelessWidget {
  const ClinicalSafetyCard({
    super.key,
    required this.label,
    required this.confidence,
    required this.triageLevel,
    required this.recommendation,
    required this.isConclusive,
    required this.confidenceThreshold,
    required this.topTwoMargin,
  });

  final String label;
  final double confidence;
  final String triageLevel;
  final String recommendation;
  final bool isConclusive;
  final double confidenceThreshold;
  final double topTwoMargin;

  bool get _needsReferral => !isConclusive || label != 'no_tumor';

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.triageColor(triageLevel);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                  child: Icon(
                    isConclusive
                        ? Icons.verified_user_outlined
                        : Icons.help_outline,
                    color: color,
                    size: 20,
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Capa de seguridad clínica',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                      ),
                      Text(
                        'Triaje automático por confianza y margen',
                        style: TextStyle(
                          color: AppTheme.muted,
                          fontSize: 12.5,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.md,
                    vertical: AppSpacing.xs + 2,
                  ),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(AppRadius.pill),
                  ),
                  child: Text(
                    AppTheme.triageLabel(triageLevel),
                    style: TextStyle(
                      color: color,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              recommendation,
              style: const TextStyle(fontSize: 13, height: 1.45),
            ),
            const SizedBox(height: AppSpacing.md),
            Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: [
                _MetricChip(
                  icon: Icons.tune,
                  text: 'Umbral ${(confidenceThreshold * 100).toStringAsFixed(0)} %',
                ),
                _MetricChip(
                  icon: Icons.balance,
                  text: 'Margen ${(topTwoMargin * 100).toStringAsFixed(0)} pts',
                ),
              ],
            ),
            if (_needsReferral) ...[
              const SizedBox(height: AppSpacing.md),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () => _showReferralRoute(context, color),
                  icon: const Icon(Icons.local_hospital_outlined, size: 18),
                  label: const Text('Ver ruta de derivación'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showReferralRoute(BuildContext context, Color color) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.xl,
              0,
              AppSpacing.xl,
              AppSpacing.xl,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.local_hospital_outlined, color: color),
                    const SizedBox(width: AppSpacing.sm),
                    const Expanded(
                      child: Text(
                        'Ruta de derivación a especialista',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.lg),
                const _ReferralStep(
                  number: '1',
                  text: 'Lleva la MRI original (DICOM o imagen de calidad) al '
                      'especialista; no solo la captura de la app.',
                ),
                const _ReferralStep(
                  number: '2',
                  text: 'Muestra este resultado, la confianza y el mapa '
                      'Grad-CAM como apoyo, nunca como diagnóstico definitivo.',
                ),
                const _ReferralStep(
                  number: '3',
                  text: 'Un radiólogo o neuroradiólogo confirma con la lectura '
                      'completa del estudio.',
                ),
                const _ReferralStep(
                  number: '4',
                  text: 'Registra la revisión en el detalle de la predicción '
                      '(feedback humano) para auditar el caso.',
                ),
                const SizedBox(height: AppSpacing.md),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: AppTheme.warningSoft,
                    borderRadius: BorderRadius.circular(AppRadius.md),
                  ),
                  child: const Text(
                    'Esta app no emite diagnósticos ni reemplaza el criterio '
                    'médico.',
                    style: TextStyle(
                      color: AppTheme.warning,
                      fontSize: 12.5,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _MetricChip extends StatelessWidget {
  const _MetricChip({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.xs + 2,
      ),
      decoration: BoxDecoration(
        color: AppTheme.soft,
        borderRadius: BorderRadius.circular(AppRadius.pill),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppTheme.muted),
          const SizedBox(width: AppSpacing.xs),
          Text(
            text,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppTheme.onSurface,
            ),
          ),
        ],
      ),
    );
  }
}

class _ReferralStep extends StatelessWidget {
  const _ReferralStep({required this.number, required this.text});

  final String number;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 24,
            height: 24,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: AppTheme.soft,
              shape: BoxShape.circle,
            ),
            child: Text(
              number,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                color: AppTheme.primary,
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 13, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}
