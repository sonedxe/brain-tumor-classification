import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/history_entry.dart';
import '../models/pending_prediction.dart';

/// Cuenta creada sin conexión, pendiente de registrar en el backend.
class OfflineAccount {
  const OfflineAccount({
    required this.email,
    required this.name,
    required this.password,
    this.pendingSync = true,
  });

  final String email;
  final String name;
  final String password;
  final bool pendingSync;

  OfflineAccount copyWith({bool? pendingSync}) => OfflineAccount(
        email: email,
        name: name,
        password: password,
        pendingSync: pendingSync ?? this.pendingSync,
      );

  Map<String, dynamic> toJson() => {
        'email': email,
        'name': name,
        // Demo academica: se conserva para poder reproducir el registro en el
        // backend al recuperar la conexion. No se envia a ningun tercero.
        'password': base64Encode(utf8.encode(password)),
        'pending_sync': pendingSync,
      };

  factory OfflineAccount.fromJson(Map<String, dynamic> json) => OfflineAccount(
        email: json['email'] as String? ?? '',
        name: json['name'] as String? ?? '',
        password: _decode(json['password'] as String? ?? ''),
        pendingSync: json['pending_sync'] as bool? ?? true,
      );

  static String _decode(String value) {
    try {
      return utf8.decode(base64Decode(value));
    } on FormatException {
      return '';
    } on ArgumentError {
      return '';
    }
  }
}

/// Accion de feedback registrada sin conexión.
class QueuedFeedback {
  const QueuedFeedback({
    required this.predictionId,
    required this.isCorrect,
    this.correctedLabel,
    this.comment,
  });

  final int predictionId;
  final bool isCorrect;
  final String? correctedLabel;
  final String? comment;

  Map<String, dynamic> toJson() => {
        'prediction_id': predictionId,
        'is_correct': isCorrect,
        'corrected_label': correctedLabel,
        'comment': comment,
      };

  factory QueuedFeedback.fromJson(Map<String, dynamic> json) => QueuedFeedback(
        predictionId: (json['prediction_id'] as num?)?.toInt() ?? 0,
        isCorrect: json['is_correct'] as bool? ?? false,
        correctedLabel: json['corrected_label'] as String?,
        comment: json['comment'] as String?,
      );
}

/// Almacenamiento local del modo offline.
///
/// Usa `SharedPreferences` para los metadatos JSON y un directorio de archivos
/// para las imagenes pendientes. El directorio es inyectable para poder probar
/// la logica sin canales de plataforma.
class LocalDB {
  LocalDB({Directory? rootDir, SharedPreferences? preferences})
      : _rootDir = rootDir,
        _prefsOverride = preferences;

  static const _historyKey = 'offline_history_cache';
  static const _pendingKey = 'offline_pending_predictions';
  static const _accountsKey = 'offline_accounts';
  static const _feedbackKey = 'offline_feedback_queue';

  final Directory? _rootDir;
  final SharedPreferences? _prefsOverride;

  SharedPreferences? _prefs;
  Directory? _imageDir;

  Future<void> init() async {
    _prefs ??= _prefsOverride ?? await SharedPreferences.getInstance();
    if (_imageDir == null) {
      final root = _rootDir ?? await getApplicationDocumentsDirectory();
      _imageDir = Directory('${root.path}/offline_images');
      if (!_imageDir!.existsSync()) {
        await _imageDir!.create(recursive: true);
      }
    }
  }

  Future<SharedPreferences> get _store async {
    await init();
    return _prefs!;
  }

  Future<Directory> get _images async {
    await init();
    return _imageDir!;
  }

  // --- Historial cacheado del backend -------------------------------------

  Future<List<HistoryEntry>> readHistoryCache() async {
    final raw = (await _store).getString(_historyKey);
    return _decodeList(raw).map(HistoryEntry.fromJson).toList();
  }

  Future<void> writeHistoryCache(List<HistoryEntry> entries) async {
    await (await _store).setString(
      _historyKey,
      jsonEncode(entries.map((e) => e.toJson()).toList()),
    );
  }

  // --- Predicciones pendientes -------------------------------------------

  Future<List<PendingPrediction>> readPending() async {
    final raw = (await _store).getString(_pendingKey);
    return _decodeList(raw).map(PendingPrediction.fromJson).toList();
  }

  Future<void> addPending(PendingPrediction prediction, Uint8List bytes) async {
    final dir = await _images;
    final file = File('${dir.path}/${prediction.localId}.img');
    await file.writeAsBytes(bytes, flush: true);

    final pending = await readPending();
    pending.insert(0, prediction);
    await (await _store).setString(
      _pendingKey,
      jsonEncode(pending.map((e) => e.toJson()).toList()),
    );
  }

  Future<void> updatePending(PendingPrediction prediction) async {
    final pending = await readPending();
    final index =
        pending.indexWhere((e) => e.localId == prediction.localId);
    if (index >= 0) {
      pending[index] = prediction;
    } else {
      pending.add(prediction);
    }
    await (await _store).setString(
      _pendingKey,
      jsonEncode(pending.map((e) => e.toJson()).toList()),
    );
  }

  Future<void> removePending(String localId) async {
    final pending = await readPending();
    pending.removeWhere((e) => e.localId == localId);
    await (await _store).setString(
      _pendingKey,
      jsonEncode(pending.map((e) => e.toJson()).toList()),
    );
    final dir = await _images;
    final file = File('${dir.path}/$localId.img');
    if (file.existsSync()) {
      await file.delete();
    }
  }

  Future<Uint8List?> readPendingImage(String localId) async {
    final dir = await _images;
    final file = File('${dir.path}/$localId.img');
    if (!file.existsSync()) {
      return null;
    }
    return file.readAsBytes();
  }

  // --- Feedback en cola ---------------------------------------------------

  Future<List<QueuedFeedback>> readFeedbackQueue() async {
    final raw = (await _store).getString(_feedbackKey);
    return _decodeList(raw).map(QueuedFeedback.fromJson).toList();
  }

  Future<void> queueFeedback(QueuedFeedback feedback) async {
    final queue = await readFeedbackQueue();
    queue.add(feedback);
    await (await _store).setString(
      _feedbackKey,
      jsonEncode(queue.map((e) => e.toJson()).toList()),
    );
  }

  Future<void> clearFeedbackQueue() async {
    await (await _store).remove(_feedbackKey);
  }

  // --- Cuentas offline ----------------------------------------------------

  Future<List<OfflineAccount>> readAccounts() async {
    final raw = (await _store).getString(_accountsKey);
    return _decodeList(raw).map(OfflineAccount.fromJson).toList();
  }

  Future<void> saveAccount(OfflineAccount account) async {
    final accounts = await readAccounts();
    final index =
        accounts.indexWhere((e) => e.email.toLowerCase() == account.email.toLowerCase());
    if (index >= 0) {
      accounts[index] = account;
    } else {
      accounts.add(account);
    }
    await (await _store).setString(
      _accountsKey,
      jsonEncode(accounts.map((e) => e.toJson()).toList()),
    );
  }

  Future<OfflineAccount?> findAccount(String email) async {
    final accounts = await readAccounts();
    for (final account in accounts) {
      if (account.email.toLowerCase() == email.toLowerCase()) {
        return account;
      }
    }
    return null;
  }

  /// Hash local para no comparar contrasenas en claro.
  static String hashPassword(String password) =>
      sha256.convert(utf8.encode(password)).toString();

  static List<Map<String, dynamic>> _decodeList(String? raw) {
    if (raw == null || raw.isEmpty) {
      return [];
    }
    final decoded = jsonDecode(raw);
    if (decoded is! List) {
      return [];
    }
    return decoded.whereType<Map<String, dynamic>>().toList();
  }
}
