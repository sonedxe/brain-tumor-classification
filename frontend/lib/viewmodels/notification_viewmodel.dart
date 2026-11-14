import 'package:flutter/foundation.dart';

import '../data/services/notification_service.dart';

/// ViewModel de las preferencias de notificaciones.
class NotificationViewModel extends ChangeNotifier {
  NotificationViewModel({required NotificationService service})
      : _service = service;

  final NotificationService _service;

  NotificationSettings _settings = const NotificationSettings();
  bool _loaded = false;
  String? _message;

  NotificationSettings get settings => _settings;
  bool get loaded => _loaded;
  bool get isSupported => _service.isSupported;

  /// Aviso para mostrar (p. ej. permiso denegado); se consume al leerlo.
  String? takeMessage() {
    final message = _message;
    _message = null;
    return message;
  }

  Future<void> load() async {
    _settings = await _service.loadSettings();
    _loaded = true;
    notifyListeners();
    await _service.applyReminder(_settings);
  }

  Future<void> setResultsEnabled(bool value) async {
    if (value && !await _ensurePermission()) {
      return;
    }
    await _update(_settings.copyWith(resultsEnabled: value));
  }

  Future<void> setReminderEnabled(bool value) async {
    if (value && !await _ensurePermission()) {
      return;
    }
    await _update(_settings.copyWith(reminderEnabled: value));
  }

  Future<void> setReminderPeriod(ReminderPeriod period) =>
      _update(_settings.copyWith(reminderPeriod: period));

  Future<bool> _ensurePermission() async {
    if (!_service.isSupported) {
      return true;
    }
    final granted = await _service.requestPermission();
    if (!granted) {
      _message = 'Permiso de notificaciones denegado. '
          'Actívalo en los ajustes del sistema.';
      notifyListeners();
    }
    return granted;
  }

  Future<void> _update(NotificationSettings next) async {
    _settings = next;
    notifyListeners();
    await _service.saveSettings(next);
    await _service.applyReminder(next);
  }
}
