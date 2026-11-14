import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/confidence.dart';
import '../../core/formatting.dart';
import '../models/prediction_model.dart';

/// Frecuencia del recordatorio de control medico.
enum ReminderPeriod { daily, weekly }

/// Preferencias de notificaciones, persistidas en `SharedPreferences`.
class NotificationSettings {
  const NotificationSettings({
    this.resultsEnabled = true,
    this.reminderEnabled = false,
    this.reminderPeriod = ReminderPeriod.weekly,
  });

  final bool resultsEnabled;
  final bool reminderEnabled;
  final ReminderPeriod reminderPeriod;

  NotificationSettings copyWith({
    bool? resultsEnabled,
    bool? reminderEnabled,
    ReminderPeriod? reminderPeriod,
  }) {
    return NotificationSettings(
      resultsEnabled: resultsEnabled ?? this.resultsEnabled,
      reminderEnabled: reminderEnabled ?? this.reminderEnabled,
      reminderPeriod: reminderPeriod ?? this.reminderPeriod,
    );
  }
}

/// Notificaciones locales: analisis completado y recordatorio de seguimiento.
///
/// En plataformas sin soporte (web, escritorio) todas las operaciones son
/// no-ops, de modo que el resto de la app no necesita comprobar la plataforma.
class NotificationService {
  NotificationService({FlutterLocalNotificationsPlugin? plugin})
      : _plugin = plugin ?? FlutterLocalNotificationsPlugin();

  static const String _resultsKey = 'notif_results_enabled';
  static const String _reminderKey = 'notif_reminder_enabled';
  static const String _periodKey = 'notif_reminder_period';

  static const int _reminderId = 1001;
  static const int _resultId = 1002;

  final FlutterLocalNotificationsPlugin _plugin;
  bool _initialized = false;

  bool get isSupported =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);

  Future<void> init() async {
    if (!isSupported || _initialized) {
      return;
    }
    const settings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      iOS: DarwinInitializationSettings(
        requestAlertPermission: false,
        requestBadgePermission: false,
        requestSoundPermission: false,
      ),
    );
    await _plugin.initialize(settings);
    _initialized = true;
  }

  /// Pide permiso al sistema (Android 13+ / iOS). `true` si quedo concedido.
  Future<bool> requestPermission() async {
    if (!isSupported) {
      return false;
    }
    await init();
    if (defaultTargetPlatform == TargetPlatform.android) {
      final android = _plugin.resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>();
      return await android?.requestNotificationsPermission() ?? false;
    }
    final ios = _plugin.resolvePlatformSpecificImplementation<
        IOSFlutterLocalNotificationsPlugin>();
    return await ios?.requestPermissions(
          alert: true,
          badge: true,
          sound: true,
        ) ??
        false;
  }

  // --- Preferencias -------------------------------------------------------

  Future<NotificationSettings> loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final periodName = prefs.getString(_periodKey);
    return NotificationSettings(
      resultsEnabled: prefs.getBool(_resultsKey) ?? true,
      reminderEnabled: prefs.getBool(_reminderKey) ?? false,
      reminderPeriod: ReminderPeriod.values.firstWhere(
        (value) => value.name == periodName,
        orElse: () => ReminderPeriod.weekly,
      ),
    );
  }

  Future<void> saveSettings(NotificationSettings settings) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_resultsKey, settings.resultsEnabled);
    await prefs.setBool(_reminderKey, settings.reminderEnabled);
    await prefs.setString(_periodKey, settings.reminderPeriod.name);
  }

  // --- Notificaciones -----------------------------------------------------

  NotificationDetails _details(String channelId, String channelName) {
    return NotificationDetails(
      android: AndroidNotificationDetails(
        channelId,
        channelName,
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: const DarwinNotificationDetails(),
    );
  }

  /// Notificacion local al terminar un analisis, si el usuario la activo.
  Future<void> showAnalysisComplete(PredictionModel prediction) async {
    if (!isSupported) {
      return;
    }
    try {
      final settings = await loadSettings();
      if (!settings.resultsEnabled) {
        return;
      }
      await init();
      final percent = prediction.confidencePercent.toStringAsFixed(1);
      final needsReview = clinicalAlertFor(prediction) != null;
      await _plugin.show(
        _resultId,
        'Análisis completado',
        '${className(prediction.label)} · confianza $percent %'
            '${needsReview ? ' · requiere revisión médica' : ''}',
        _details('analysis_results', 'Resultados de análisis'),
      );
    } on Exception catch (error) {
      // Una notificacion fallida nunca debe romper el flujo de analisis.
      debugPrint('No se pudo mostrar la notificacion: $error');
    }
  }

  /// Programa (o cancela) el recordatorio periodico segun [settings].
  Future<void> applyReminder(NotificationSettings settings) async {
    if (!isSupported) {
      return;
    }
    try {
      await init();
      await _plugin.cancel(_reminderId);
      if (!settings.reminderEnabled) {
        return;
      }
      await _plugin.periodicallyShow(
        _reminderId,
        'Recordatorio de control médico',
        'Revisa tu seguimiento: agenda o confirma tu control con el '
            'especialista.',
        settings.reminderPeriod == ReminderPeriod.daily
            ? RepeatInterval.daily
            : RepeatInterval.weekly,
        _details('follow_up_reminder', 'Recordatorio de seguimiento'),
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      );
    } on Exception catch (error) {
      debugPrint('No se pudo programar el recordatorio: $error');
    }
  }
}
