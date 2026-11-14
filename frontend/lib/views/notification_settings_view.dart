import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../data/services/notification_service.dart';
import '../viewmodels/notification_viewmodel.dart';

/// Ajustes de notificaciones: resultados y recordatorio de control medico.
class NotificationSettingsView extends StatelessWidget {
  const NotificationSettingsView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notificaciones')),
      body: SafeArea(
        child: Consumer<NotificationViewModel>(
          builder: (context, viewModel, _) {
            final message = viewModel.takeMessage();
            if (message != null) {
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context)
                      .showSnackBar(SnackBar(content: Text(message)));
                }
              });
            }

            final settings = viewModel.settings;
            return ListView(
              padding: const EdgeInsets.all(AppSpacing.lg),
              children: [
                if (!viewModel.isSupported)
                  const Padding(
                    padding: EdgeInsets.only(bottom: AppSpacing.lg),
                    child: Text(
                      'Las notificaciones locales solo están disponibles en '
                      'Android e iOS. Tus preferencias se guardan igualmente.',
                      style: TextStyle(color: AppTheme.muted, height: 1.4),
                    ),
                  ),
                Card(
                  child: Column(
                    children: [
                      SwitchListTile(
                        secondary: const Icon(Icons.notifications_active_outlined),
                        title: const Text('Resultados de análisis'),
                        subtitle: const Text(
                          'Avisa cuando termina una clasificación con el '
                          'resumen del resultado.',
                        ),
                        value: settings.resultsEnabled,
                        onChanged: viewModel.setResultsEnabled,
                      ),
                      const Divider(height: 1),
                      SwitchListTile(
                        secondary: const Icon(Icons.event_repeat_outlined),
                        title: const Text('Recordatorio de control médico'),
                        subtitle: const Text(
                          'Notificación periódica para dar seguimiento con '
                          'tu especialista.',
                        ),
                        value: settings.reminderEnabled,
                        onChanged: viewModel.setReminderEnabled,
                      ),
                      if (settings.reminderEnabled)
                        Padding(
                          padding: const EdgeInsets.fromLTRB(
                            AppSpacing.lg,
                            0,
                            AppSpacing.lg,
                            AppSpacing.lg,
                          ),
                          child: SizedBox(
                            width: double.infinity,
                            child: SegmentedButton<ReminderPeriod>(
                              showSelectedIcon: false,
                              segments: const [
                                ButtonSegment(
                                  value: ReminderPeriod.daily,
                                  label: Text('Diario'),
                                ),
                                ButtonSegment(
                                  value: ReminderPeriod.weekly,
                                  label: Text('Semanal'),
                                ),
                              ],
                              selected: {settings.reminderPeriod},
                              onSelectionChanged: (value) =>
                                  viewModel.setReminderPeriod(value.first),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
