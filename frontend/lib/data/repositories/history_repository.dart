import '../models/history_entry.dart';
import '../services/api_service.dart';

/// Repositorio del historial.
///
/// MVVM: el ViewModel de historial depende de esta abstraccion y nunca de
/// `ApiService` directamente, lo que permite inyectar un fake en las pruebas.
class HistoryRepository {
  HistoryRepository({ApiService? apiService})
      : _apiService = apiService ?? ApiService();

  final ApiService _apiService;

  Future<List<HistoryEntry>> fetch({int limit = 20}) =>
      _apiService.fetchHistory(limit: limit);

  void dispose() => _apiService.dispose();
}
