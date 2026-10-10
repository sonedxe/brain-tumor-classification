import 'package:brain_tumor_classification/data/models/history_entry.dart';
import 'package:brain_tumor_classification/data/repositories/history_repository.dart';
import 'package:brain_tumor_classification/data/services/api_service.dart';
import 'package:brain_tumor_classification/viewmodels/history_viewmodel.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _historyPayload = '''
[
  {
    "id": 2,
    "image_hash": "aa",
    "label": "meningioma",
    "confidence": 0.91,
    "model_version": "mobilenetv3-v1",
    "inference_ms": 80.0,
    "created_at": "2026-10-08T12:00:00"
  },
  {
    "id": 1,
    "image_hash": "bb",
    "label": "no_tumor",
    "confidence": 0.77,
    "model_version": "mobilenetv3-v1",
    "inference_ms": 75.0,
    "created_at": "2026-10-08T11:00:00"
  }
]
''';

HistoryViewModel _viewModelWith(MockClient client) {
  final service = ApiService(
    client: client,
    baseUrl: 'http://localhost:8000/api/v1',
  );
  return HistoryViewModel(repository: HistoryRepository(apiService: service));
}

void main() {
  group('HistoryEntry', () {
    test('parsea el contrato de GET /history', () {
      final entry = HistoryEntry.fromJson({
        'id': 1,
        'label': 'glioma',
        'confidence': 0.88,
        'model_version': 'v1',
        'inference_ms': 42.0,
        'created_at': '2026-10-08T10:00:00',
        'image_hash': 'abc',
      });

      expect(entry.id, 1);
      expect(entry.label, 'glioma');
      expect(entry.confidence, closeTo(0.88, 1e-9));
      expect(entry.inferenceMs, closeTo(42.0, 1e-9));
      expect(entry.isTumor, isTrue);
    });
  });

  group('HistoryViewModel', () {
    test('carga las entradas del endpoint', () async {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(_historyPayload, 200)),
      );

      await viewModel.load();

      expect(viewModel.status, HistoryStatus.success);
      expect(viewModel.entries.length, 2);
      expect(viewModel.entries.first.label, 'meningioma');
    });

    test('marca vacio cuando el backend no tiene registros', () async {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response('[]', 200)),
      );

      await viewModel.load();

      expect(viewModel.isEmpty, isTrue);
      expect(viewModel.entries, isEmpty);
    });

    test('expone el error sin lanzar excepcion', () async {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response('{"detail":"fallo"}', 500)),
      );

      await viewModel.load();

      expect(viewModel.status, HistoryStatus.error);
      expect(viewModel.errorMessage, 'fallo');
    });
  });
}
