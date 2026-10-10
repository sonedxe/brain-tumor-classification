import 'package:flutter/material.dart';

import '../core/theme.dart';

/// Encabezado de seccion con titulo y, opcionalmente, una accion.
///
/// MVVM: es presentacion pura; no conoce estado ni modelos.
class SectionHeader extends StatelessWidget {
  const SectionHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.trailing,
  });

  final String title;
  final String? subtitle;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              if (subtitle != null) ...[
                const SizedBox(height: AppSpacing.xs),
                Text(
                  subtitle!,
                  style: const TextStyle(color: AppTheme.muted, fontSize: 13),
                ),
              ],
            ],
          ),
        ),
        ?trailing,
      ],
    );
  }
}