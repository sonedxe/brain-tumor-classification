import 'package:flutter/foundation.dart';

import '../core/formatting.dart';
import '../data/local/local_db.dart';
import '../data/models/history_entry.dart';
import '../data/repositories/history_repository.dart';
import '../data/services/api_service.dart';
import '../data/services/connectivity_service.dart';

enum HistoryStatus { idle, loading, success, error }

/// Valor del filtro de clase que no excluye nada.
const String classFilterAll = 'todas';

/// ViewModel del historial (MVVM).
///
/// Online: consume `GET /history` y cachea el resultado. Offline: muestra la
/// caché más las predicciones pendientes de sincronizar.
class HistoryViewModel extends ChangeNotifier {
  HistoryViewModel({
    HistoryRepository? repository,
    LocalDB? db,
    ConnectivityService? connectivity,
  })  : _repository = repository ?? HistoryRepository(),
        _db = db,
        _connectivity = connectivity ?? ConnectivityService.instance {
    _connectivity.addListener(notifyListeners);
  }

  final HistoryRepository _repository;
  final LocalDB? _db;
  final ConnectivityService _connectivity;

  HistoryStatus _status = HistoryStatus.idle;
  List<HistoryEntry> _entries = const [];
  String? _errorMessage;

  HistoryStatus get status => _status;
  List<HistoryEntry> get entries => _entries;
  String? get errorMessage => _errorMessage;
  bool get isLoading => _status == HistoryStatus.loading;
  bool get hasError => _status == HistoryStatus.error;
  bool get isEmpty => _status == HistoryStatus.success && _entries.isEmpty;
  bool get isOffline => _connectivity.isOffline;

  int get pendingCount => _entries.where((e) => e.pendingSync).length;

  // --- Busqueda, filtro por clase y orden (solo estado de presentacion) ----

  String _query = '';
  String _classFilter = classFilterAll;
  bool _newestFirst = true;

  String get query => _query;
  String get classFilter => _classFilter;
  bool get newestFirst => _newestFirst;
  bool get hasActiveFilters =>
      _query.trim().isNotEmpty || _classFilter != classFilterAll;

  void setQuery(String value) {
    _query = value;
    notifyListeners();
  }

  void setClassFilter(String value) {
    _classFilter = value;
    notifyListeners();
  }

  void setNewestFirst(bool value) {
    _newestFirst = value;
    notifyListeners();
  }

  void clearFilters() {
    _query = '';
    _classFilter = classFilterAll;
    notifyListeners();
  }

  int countFor(String filter) => filter == classFilterAll
      ? _entries.length
      : _entries.where((e) => e.label == filter).length;

  /// Entradas tras aplicar busqueda, filtro por clase y orden por fecha.
  List<HistoryEntry> get visibleEntries {
    final needle = _query.trim().toLowerCase();
    final result = _entries.where((entry) {
      if (_classFilter != classFilterAll && entry.label != _classFilter) {
        return false;
      }
      if (needle.isEmpty) {
        return true;
      }
      final haystack = [
        className(entry.label),
        entry.label,
        entry.modelVersion,
        formatTimestamp(entry.createdAt),
        '#${entry.id}',
      ].join(' ').toLowerCase();
      return haystack.contains(needle);
    }).toList();

    DateTime stamp(HistoryEntry e) =>
        DateTime.tryParse(e.createdAt) ?? DateTime.fromMillisecondsSinceEpoch(0);
    result.sort(
      (a, b) =>
          _newestFirst ? stamp(b).compareTo(stamp(a)) : stamp(a).compareTo(stamp(b)),
    );
    return result;
  }

  /// URL de la miniatura (Grad-CAM) o `null` si la entrada no la tiene.
  Uri? thumbnailUrl(HistoryEntry entry) {
    final path = entry.gradcamPath;
    if (path == null || path.isEmpty) {
      return null;
    }
    return _repository.resolveStaticPath(path);
  }

  Future<void> load({int limit = 20}) async {
    _status = HistoryStatus.loading;
    _errorMessage = null;
    notifyListeners();

    if (_connectivity.isOffline) {
      await _loadOffline();
      return;
    }

    try {
      final remote = await _repository.fetch(limit: limit);
      await _db?.writeHistoryCache(remote);
      _entries = [...await _pendingAsEntries(), ...remote];
      _status = HistoryStatus.success;
    } on ApiException catch (error) {
      if (error.isNetwork) {
        await _loadOffline(fallbackMessage: error.message);
        return;
      }
      _errorMessage = error.message;
      _status = HistoryStatus.error;
    } on Exception catch (error) {
      _errorMessage = 'Ocurrio un error inesperado: $error';
      _status = HistoryStatus.error;
    }
    notifyListeners();
  }

  Future<void> _loadOffline({String? fallbackMessage}) async {
    final pending = await _pendingAsEntries();
    final cached = await _db?.readHistoryCache() ?? const <HistoryEntry>[];
    _entries = [...pending, ...cached];
    _errorMessage = null;
    _status = HistoryStatus.success;
    if (_entries.isEmpty && fallbackMessage != null) {
      _errorMessage = '$fallbackMessage\nSin datos guardados todavía.';
      _status = HistoryStatus.error;
    }
    notifyListeners();
  }

  Future<List<HistoryEntry>> _pendingAsEntries() async {
    final pending = await _db?.readPending() ?? const [];
    return pending
        .map(
          (item) => HistoryEntry(
            id: 0,
            label: item.label,
            confidence: item.confidence,
            modelVersion: item.modelVersion,
            inferenceMs: item.inferenceMs,
            createdAt: item.createdAt,
            imageHash: item.imageHash,
            pendingSync: true,
            localId: item.localId,
          ),
        )
        .toList();
  }

  @override
  void dispose() {
    _connectivity.removeListener(notifyListeners);
    _repository.dispose();
    super.dispose();
  }
}
