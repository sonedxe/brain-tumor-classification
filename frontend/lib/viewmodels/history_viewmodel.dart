import 'package:flutter/foundation.dart';

import '../data/models/history_entry.dart';
import '../data/repositories/history_repository.dart';
import '../data/services/api_service.dart';

enum HistoryStatus { idle, loading, success, error }

/// ViewModel del historial (MVVM).
///
/// La vista solo observa este objeto y pide `load()`; aqui viven el estado de
/// carga, el error normalizado y la lista de entradas. Ninguna capa de UI
/// conoce la URL ni el formato del endpoint.
class HistoryViewModel extends ChangeNotifier {
  HistoryViewModel({HistoryRepository? repository})
      : _repository = repository ?? HistoryRepository();

  final HistoryRepository _repository;

  HistoryStatus _status = HistoryStatus.idle;
  List<HistoryEntry> _entries = const [];
  String? _errorMessage;

  HistoryStatus get status => _status;
  List<HistoryEntry> get entries => _entries;
  String? get errorMessage => _errorMessage;
  bool get isLoading => _status == HistoryStatus.loading;
  bool get hasError => _status == HistoryStatus.error;
  bool get isEmpty => _status == HistoryStatus.success && _entries.isEmpty;

  Future<void> load({int limit = 20}) async {
    _status = HistoryStatus.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      _entries = await _repository.fetch(limit: limit);
      _status = HistoryStatus.success;
    } on ApiException catch (error) {
      _errorMessage = error.message;
      _status = HistoryStatus.error;
    } on Exception catch (error) {
      _errorMessage = 'Ocurrio un error inesperado: $error';
      _status = HistoryStatus.error;
    }
    notifyListeners();
  }

  @override
  void dispose() {
    _repository.dispose();
    super.dispose();
  }
}
