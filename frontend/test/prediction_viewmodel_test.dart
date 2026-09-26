import 'dart:io';

import 'package:brain_tumor_classification/data/models/prediction_model.dart';
import 'package:brain_tumor_classification/data/repositories/prediction_repository.dart';
import 'package:brain_tumor_classification/data/services/api_service.dart';
import 'package:brain_tumor_classification/viewmodels/prediction_viewmodel.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:http/testing.dart';

const _payload = {
  'label': 'meningioma',
  'confidence': 0.97,
  'probabilities': {
    'glioma': 0.01,
    'meningioma': 0.97,
    'pituitario': 0.01,
    'no_tumor': 0.01,
  },
  'gradcam_path': '/static/gradcam/9f2a.png',
  'model_version': 'mobilenetv3-v1',
  'inference_ms': 82.4,
};

PredictionViewModel _viewModelWith(MockClient client) {
  final service = ApiService(
    client: client,
    baseUrl: 'http://localhost:8000/api/v1',
  );
  return PredictionViewModel(repository: PredictionRepository(apiService: service));
}

File _tempImage() {
  final file = File('${Directory.systemTemp.path}/mri_test.png');
  file.writeAsBytesSync(List<int>.filled(64, 7));
  return file;
}

void main() {
  group('PredictionModel', () {
    test('parsea el contrato de la API', () {
      final model = PredictionModel.fromJson(_payload);

      expect(model.label, 'meningioma');
      expect(model.confidence, closeTo(0.97, 1e-9));
      expect(model.probabilities.length, 4);
      expect(model.inferenceMs, closeTo(82.4, 1e-9));
      expect(model.modelVersion, 'mobilenetv3-v1');
      expect(model.isTumor, isTrue);
    });

    test('no_tumor se reconoce como caso sano', () {
      final model = PredictionModel.fromJson({..._payload, 'label': 'no_tumor'});

      expect(model.isTumor, isFalse);
    });

    test('tolera un payload incompleto', () {
      final model = PredictionModel.fromJson({'label': 'glioma'});

      expect(model.confidence, 0.0);
      expect(model.probabilities, isEmpty);
      expect(model.gradcamPath, isNull);
    });
  });

  group('ApiService', () {
    test('resuelve gradcam_path contra la raiz del servidor', () {
      final service = ApiService(baseUrl: 'http://10.0.2.2:8000/api/v1');

      final resolved = service.resolveStaticPath('/static/gradcam/9f2a.png');

      expect(
        resolved.toString(),
        'http://10.0.2.2:8000/api/v1/static/gradcam/9f2a.png',
      );
    });

    test('envia el archivo en el campo file', () async {
      late http.BaseRequest captured;
      late String capturedBody;
      final client = MockClient((request) async {
        captured = request;
        capturedBody = request.body;
        return http.Response('{"label":"glioma","confidence":0.9,'
            '"probabilities":{},"model_version":"v1","inference_ms":10.0}', 201);
      });
      final service = ApiService(client: client);

      await service.predict(_tempImage());

      expect(captured.method, 'POST');
      expect(captured.url.path, endsWith('/predict'));
      expect(
        captured.headers['content-type'],
        contains('multipart/form-data'),
      );
      expect(capturedBody, contains('name="file"'));
    });

    test('traduce un 422 de FastAPI a ApiException', () async {
      final client = MockClient(
        (_) async => http.Response('{"detail":"Field required"}', 422),
      );
      final service = ApiService(client: client);

      expect(
        () => service.predict(_tempImage()),
        throwsA(
          isA<ApiException>()
              .having((e) => e.statusCode, 'statusCode', 422)
              .having((e) => e.message, 'message', 'Field required'),
        ),
      );
    });
  });

  group('PredictionViewModel', () {
    test('arranca en estado idle', () {
      final viewModel = _viewModelWith(MockClient((_) async => http.Response('', 500)));

      expect(viewModel.status, PredictionStatus.idle);
      expect(viewModel.prediction, isNull);
      expect(viewModel.canClassify, isFalse);
    });

    test('no permite clasificar sin imagen', () async {
      final viewModel = _viewModelWith(MockClient((_) async => http.Response('', 500)));

      await viewModel.classify();

      expect(viewModel.status, PredictionStatus.error);
      expect(viewModel.errorMessage, isNotNull);
    });

    test('cambia a loading y luego a success', () async {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(
              '{"label":"glioma","confidence":0.88,'
              '"probabilities":{"glioma":0.88},"model_version":"v1","inference_ms":42.0}',
              201,
            )),
      );
      final states = <PredictionStatus>[];
      viewModel.addListener(() => states.add(viewModel.status));

      viewModel.selectImage(_tempImage());
      await viewModel.classify();

      expect(states, contains(PredictionStatus.loading));
      expect(viewModel.status, PredictionStatus.success);
      expect(viewModel.prediction?.label, 'glioma');
      expect(viewModel.prediction?.confidence, closeTo(0.88, 1e-9));
    });

    test('expone el estado de error sin lanzar excepcion', () async {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response('{"detail":"formato no permitido"}', 400)),
      );
      viewModel.selectImage(_tempImage());

      await viewModel.classify();

      expect(viewModel.status, PredictionStatus.error);
      expect(viewModel.errorMessage, 'formato no permitido');
      expect(viewModel.prediction, isNull);
    });

    test('gradcamUrl es null cuando el backend no devuelve mapa', () {
      final viewModel = _viewModelWith(MockClient((_) async => http.Response('', 500)));

      expect(viewModel.gradcamUrl, isNull);
    });

    test('clear restablece el estado inicial', () async {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(
              '{"label":"glioma","confidence":0.5,'
              '"probabilities":{},"model_version":"v1","inference_ms":1.0}',
              201,
            )),
      );
      viewModel.selectImage(_tempImage());
      await viewModel.classify();

      viewModel.clear();

      expect(viewModel.status, PredictionStatus.idle);
      expect(viewModel.selectedImage, isNull);
      expect(viewModel.prediction, isNull);
      expect(viewModel.errorMessage, isNull);
    });

    test('seleccionar una imagen invalida el resultado anterior', () async {
      final viewModel = _viewModelWith(
        MockClient((_) async => http.Response(
              '{"label":"glioma","confidence":0.5,'
              '"probabilities":{},"model_version":"v1","inference_ms":1.0}',
              201,
            )),
      );
      viewModel.selectImage(_tempImage());
      await viewModel.classify();

      viewModel.selectImage(_tempImage());

      expect(viewModel.status, PredictionStatus.idle);
      expect(viewModel.prediction, isNull);
    });
  });
}
