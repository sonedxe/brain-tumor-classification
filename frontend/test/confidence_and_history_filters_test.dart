import 'package:brain_tumor_classification/core/confidence.dart';
import 'package:brain_tumor_classification/data/models/prediction_model.dart';
import 'package:brain_tumor_classification/data/repositories/history_repository.dart';
import 'package:brain_tumor_classification/data/services/api_service.dart';
import 'package:brain_tumor_classification/viewmodels/history_viewmodel.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _payload = '''
[
  {"id": 1, "image_hash": "a", "label": "glioma", "confidence": 0.95,
   "model_version": "mobilenetv3-v1", "inference_ms": 80.0,
   "created_at": "2026-10-01T10:00:00"},
  {"id": 2, "image_hash": "b", "label": "no_tumor", "confidence": 0.70,
   "model_version": "mobilenetv3-v1", "inference_ms": 70.0,
   "created_at": "2026-10-03T10:00:00"},
  {"id": 3, "image_hash": "c", "label": "meningioma", "confidence": 0.88,
   "model_version": "mobilenetv3-v1", "inference_ms": 75.0,
   "created_at": "2026-10-02T10:00:00"}
]
''';

PredictionModel _prediction(String label, double confidence) =>
    PredictionModel(
      label: label,
      confidence: confidence,
      probabilities: const {},
      modelVersion: 'v1',
      inferenceMs: 10,
    );

void main() {
  group('nivel de confianza', () {
    test('clasifica en alta, moderada y baja (umbral 75 %)', () {
      expect(confidenceLevelOf(0.95), ConfidenceLevel.high);
      expect(confidenceLevelOf(0.80), ConfidenceLevel.moderate);
      expect(confidenceLevelOf(0.75), ConfidenceLevel.moderate);
      expect(confidenceLevelOf(0.74), ConfidenceLevel.low);
    });
  });

  group('alerta clinica', () {
    test('sin tumor y confianza alta no genera alerta', () {
      expect(clinicalAlertFor(_prediction('no_tumor', 0.97)), isNull);
    });

    test('confianza baja sin tumor genera aviso', () {
      final alert = clinicalAlertFor(_prediction('no_tumor', 0.60));
      expect(alert?.severity, AlertSeverity.warning);
    });

    test('tumor genera alerta critica', () {
      final alert = clinicalAlertFor(_prediction('glioma', 0.93));
      expect(alert?.severity, AlertSeverity.critical);
    });
  });

  group('HistoryViewModel: busqueda, filtro y orden', () {
    Future<HistoryViewModel> loaded() async {
      final service = ApiService(
        client: MockClient((_) async => http.Response(_payload, 200)),
        baseUrl: 'http://localhost:8000/api/v1',
      );
      final viewModel =
          HistoryViewModel(repository: HistoryRepository(apiService: service));
      await viewModel.load();
      return viewModel;
    }

    test('ordena por fecha, mas recientes primero por defecto', () async {
      final viewModel = await loaded();
      expect(viewModel.visibleEntries.map((e) => e.id), [2, 3, 1]);

      viewModel.setNewestFirst(false);
      expect(viewModel.visibleEntries.map((e) => e.id), [1, 3, 2]);
    });

    test('filtra por clase y cuenta por filtro', () async {
      final viewModel = await loaded();
      viewModel.setClassFilter('glioma');

      expect(viewModel.visibleEntries.map((e) => e.id), [1]);
      expect(viewModel.countFor('no_tumor'), 1);
      expect(viewModel.countFor(classFilterAll), 3);
    });

    test('la busqueda por texto y limpiar filtros funcionan', () async {
      final viewModel = await loaded();
      viewModel.setQuery('menin');
      expect(viewModel.visibleEntries.map((e) => e.id), [3]);

      viewModel.setQuery('zzz');
      expect(viewModel.visibleEntries, isEmpty);

      viewModel.clearFilters();
      expect(viewModel.visibleEntries.length, 3);
      expect(viewModel.hasActiveFilters, isFalse);
    });
  });
}
