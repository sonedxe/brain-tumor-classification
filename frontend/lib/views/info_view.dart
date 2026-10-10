import 'package:flutter/material.dart';

import '../core/theme.dart';
import '../widgets/section_header.dart';

/// Informacion educativa (RF-06). Contenido estatico, sin backend.
class InfoView extends StatelessWidget {
  const InfoView({super.key});

  static const _items = [
    (
      title: 'Glioma',
      body:
          'Tumor del tejido glial. Suele requerir resonancia con contraste y '
              'valoracion neuroquirurgica.',
      key: 'glioma',
      icon: Icons.grain,
    ),
    (
      title: 'Meningioma',
      body:
          'Tumor de las meninges, a menudo benigno. Cefalea y crisis son '
              'motivos frecuentes de consulta.',
      key: 'meningioma',
      icon: Icons.layers_outlined,
    ),
    (
      title: 'Tumor pituitario',
      body:
          'Adenoma hipofisario. Puede alterar hormonas; la clinica endocrina '
              'orienta el manejo.',
      key: 'pituitario',
      icon: Icons.water_drop_outlined,
    ),
    (
      title: 'Sin tumor',
      body:
          'Sin hallazgos tumorales en la imagen analizada. Ante sintomas, '
              'acudir a control medico.',
      key: 'no_tumor',
      icon: Icons.verified_outlined,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: [
        const SectionHeader(
          title: 'Las cuatro clases',
          subtitle: 'Que significa cada resultado del modelo',
        ),
        const SizedBox(height: AppSpacing.md),
        ..._items.map(
          (item) => _InfoCard(
            title: item.title,
            body: item.body,
            color: AppTheme.classColor(item.key),
            icon: item.icon,
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        const _ResponsibleNote(),
      ],
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.title,
    required this.body,
    required this.color,
    required this.icon,
  });

  final String title;
  final String body;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      clipBehavior: Clip.antiAlias,
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(width: 5, color: color),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(AppRadius.sm),
                      ),
                      child: Icon(icon, color: color, size: 22),
                    ),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            title,
                            style: Theme.of(context)
                                .textTheme
                                .titleSmall
                                ?.copyWith(
                                  fontWeight: FontWeight.w700,
                                  color: color,
                                ),
                          ),
                          const SizedBox(height: AppSpacing.xs),
                          Text(
                            body,
                            style: const TextStyle(
                              fontSize: 13.5,
                              height: 1.45,
                              color: AppTheme.onSurface,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ResponsibleNote extends StatelessWidget {
  const _ResponsibleNote();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppTheme.soft,
        borderRadius: BorderRadius.circular(AppRadius.md),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.health_and_safety_outlined, color: AppTheme.primary),
          SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              'Ante cualquier hallazgo, acude siempre a un especialista. Esta '
              'app es un apoyo academico, no un diagnostico.',
              style: TextStyle(
                fontSize: 13,
                color: AppTheme.muted,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
