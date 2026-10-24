import '../models/stats_summary.dart';
import '../services/api_service.dart';

/// Repositorio de estadísticas.
///
/// MVVM: el ViewModel nunca toca `ApiService` directamente.
class StatsRepository {
  StatsRepository({ApiService? apiService})
      : _apiService = apiService ?? ApiService();

  final ApiService _apiService;

  Future<StatsSummary> fetchSummary() => _apiService.fetchStatsSummary();

  void dispose() => _apiService.dispose();
}
