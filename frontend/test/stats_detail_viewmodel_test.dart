import 'package:brain_tumor_classification/data/repositories/detail_repository.dart';
import 'package:brain_tumor_classification/data/repositories/stats_repository.dart';
import 'package:brain_tumor_classification/data/services/api_service.dart';
import 'package:brain_tumor_classification/viewmodels/detail_viewmodel.dart';
import 'package:brain_tumor_classification/viewmodels/stats_viewmodel.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _statsPayload = '''
{
  "total_predictions": 10,
  "unique_images": 8,
  "models_registered": 5,
  "total_feedback": 2,
  "avg_confidence": 0.9,
  "avg_inference_ms": 80.0,
  "by_class": [
    {"code": "glioma", "display_name": "Glioma", "count": 4, "avg_confidence": 0.88},
    {"code": "no_tumor", "display_name": "Sin tumor", "count": 6, "avg_confidence": 0.92}
  ]
}
''';

const _detailPayload = '''
{
  "id": 7,
  "image": {"sha256": "aa", "width": 224, "height": 224, "format": "PNG", "size_bytes": 10},
  "model": {"id": 1, "name": "mobilenetv3", "architecture": "mobilenetv3", "version": "mobilenetv3-v1", "dataset": "nickparvar2024", "is_active": true},
  "predicted_class": {"id": 1, "code": "meningioma", "display_name": "Meningioma", "index": 1, "is_tumor": true},
  "confidence": 0.91,
  "inference_ms": 80.0,
  "gradcam_path": "/static/gradcam/aa.png",
  "source": "flutter",
  "created_at": "2026-10-08T12:00:00",
  "scores": [
    {"probability": 0.91, "lesion_class": {"id": 1, "code": "meningioma", "display_name": "Meningioma", "index": 1, "is_tumor": true}},
    {"probability": 0.09, "lesion_class": {"id": 4, "code": "no_tumor", "display_name": "Sin tumor", "index": 3, "is_tumor": false}}
  ],
  "feedback": []
}
''';

void main() {
  group('StatsViewModel', () {
    test('carga el resumen del endpoint', () async {
      final service = ApiService(
        client: MockClient((_) async => http.Response(_statsPayload, 200)),
        baseUrl: 'http://localhost:8000/api/v1',
      );
      final viewModel =
          StatsViewModel(repository: StatsRepository(apiService: service));

      await viewModel.load();

      expect(viewModel.status, StatsStatus.success);
      expect(viewModel.summary?.totalPredictions, 10);
      expect(viewModel.summary?.byClass.length, 2);
    });

    test('expone error sin lanzar', () async {
      final service = ApiService(
        client: MockClient(
            (_) async => http.Response('{"detail":"fallo"}', 500)),
        baseUrl: 'http://localhost:8000/api/v1',
      );
      final viewModel =
          StatsViewModel(repository: StatsRepository(apiService: service));

      await viewModel.load();

      expect(viewModel.status, StatsStatus.error);
    });
  });

  group('DetailViewModel', () {
    test('carga detalle y envia feedback', () async {
      var feedbackCalled = false;
      final service = ApiService(
        client: MockClient((request) async {
          if (request.url.path.endsWith('/feedback')) {
            feedbackCalled = true;
            return http.Response('{"id":1}', 201);
          }
          return http.Response(_detailPayload, 200);
        }),
        baseUrl: 'http://localhost:8000/api/v1',
      );
      final viewModel =
          DetailViewModel(repository: DetailRepository(apiService: service));

      await viewModel.load(7);
      expect(viewModel.status, DetailStatus.success);
      expect(viewModel.detail?.label, 'meningioma');

      await viewModel.sendFeedback(isCorrect: true);
      expect(feedbackCalled, isTrue);
      expect(viewModel.feedbackMessage, isNotNull);
    });
  });
}
