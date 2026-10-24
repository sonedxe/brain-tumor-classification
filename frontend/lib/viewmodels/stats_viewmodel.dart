import 'package:flutter/foundation.dart';

import '../data/models/stats_summary.dart';
import '../data/repositories/stats_repository.dart';
import '../data/services/api_service.dart';

enum StatsStatus { idle, loading, success, error }

/// ViewModel del dashboard (MVVM).
class StatsViewModel extends ChangeNotifier {
  StatsViewModel({StatsRepository? repository})
      : _repository = repository ?? StatsRepository();

  final StatsRepository _repository;

  StatsStatus _status = StatsStatus.idle;
  StatsSummary? _summary;
  String? _errorMessage;

  StatsStatus get status => _status;
  StatsSummary? get summary => _summary;
  String? get errorMessage => _errorMessage;
  bool get isLoading => _status == StatsStatus.loading;
  bool get hasError => _status == StatsStatus.error;

  Future<void> load() async {
    _status = StatsStatus.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      _summary = await _repository.fetchSummary();
      _status = StatsStatus.success;
    } on ApiException catch (error) {
      _errorMessage = error.message;
      _status = StatsStatus.error;
    } on Exception catch (error) {
      _errorMessage = 'Ocurrio un error inesperado: $error';
      _status = StatsStatus.error;
    }
    notifyListeners();
  }

  @override
  void dispose() {
    _repository.dispose();
    super.dispose();
  }
}
