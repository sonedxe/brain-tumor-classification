import 'package:brain_tumor_classification/core/clinical_safety.dart';
import 'package:brain_tumor_classification/data/models/prediction_detail.dart';
import 'package:brain_tumor_classification/data/models/prediction_model.dart';
import 'package:flutter_test/flutter_test.dart';

const _classes = ['glioma', 'meningioma', 'pituitario', 'no_tumor'];

Map<String, double> _distribution(String topLabel, double top) {
  final rest = (1.0 - top) / (_classes.length - 1);
  return {
    for (final name in _classes) name: name == topLabel ? top : rest,
  };
}

void main() {
  group('ClinicalAssessment', () {
    test('no_tumor concluyente es riesgo bajo', () {
      final result = ClinicalAssessment.assess(
        label: 'no_tumor',
        confidence: 0.95,
        probabilities: _distribution('no_tumor', 0.95),
      );

      expect(result.isConclusive, isTrue);
      expect(result.triageLevel, 'bajo');
      expect(result.recommendation, contains('radiología'));
    });

    test('tumor con alta confianza es riesgo alto', () {
      final result = ClinicalAssessment.assess(
        label: 'glioma',
        confidence: 0.96,
        probabilities: _distribution('glioma', 0.96),
      );

      expect(result.isConclusive, isTrue);
      expect(result.triageLevel, 'alto');
      expect(result.recommendation, contains('Deriva'));
    });

    test('tumor con confianza moderada es riesgo medio', () {
      final result = ClinicalAssessment.assess(
        label: 'meningioma',
        confidence: 0.75,
        probabilities: _distribution('meningioma', 0.75),
      );

      expect(result.isConclusive, isTrue);
      expect(result.triageLevel, 'medio');
    });

    test('confianza baja es no concluyente', () {
      final result = ClinicalAssessment.assess(
        label: 'pituitario',
        confidence: 0.45,
        probabilities: _distribution('pituitario', 0.45),
      );

      expect(result.isConclusive, isFalse);
      expect(result.triageLevel, 'no_concluyente');
      expect(result.recommendation.toLowerCase(), contains('no concluyente'));
    });

    test('margen insuficiente es no concluyente aunque la confianza sea alta',
        () {
      final result = ClinicalAssessment.assess(
        label: 'glioma',
        confidence: 0.40,
        probabilities: const {
          'glioma': 0.40,
          'meningioma': 0.38,
          'pituitario': 0.12,
          'no_tumor': 0.10,
        },
        confidenceThreshold: 0.30,
        marginThreshold: 0.10,
      );

      expect(result.isConclusive, isFalse);
      expect(result.triageLevel, 'no_concluyente');
      expect(result.topTwoMargin, closeTo(0.02, 1e-9));
    });
  });

  group('PredictionModel con capa de seguridad', () {
    test('lee los campos de triaje del backend', () {
      final model = PredictionModel.fromJson(const {
        'label': 'glioma',
        'confidence': 0.95,
        'probabilities': {
          'glioma': 0.95,
          'meningioma': 0.02,
          'pituitario': 0.02,
          'no_tumor': 0.01,
        },
        'model_version': 'mobilenetv3-v1',
        'inference_ms': 40.0,
        'is_conclusive': true,
        'triage_level': 'alto',
        'recommendation': 'Deriva a especialista.',
        'confidence_threshold': 0.70,
        'top_two_margin': 0.93,
      });

      expect(model.isConclusive, isTrue);
      expect(model.triageLevel, 'alto');
      expect(model.recommendation, 'Deriva a especialista.');
      expect(model.confidenceThreshold, closeTo(0.70, 1e-9));
      expect(model.topTwoMargin, closeTo(0.93, 1e-9));
    });

    test('calcula el triaje si el backend no lo envía', () {
      final model = PredictionModel.fromJson(const {
        'label': 'glioma',
        'confidence': 0.95,
        'probabilities': {'glioma': 0.95, 'no_tumor': 0.05},
        'model_version': 'v1',
        'inference_ms': 10.0,
      });

      expect(model.triageLevel, 'alto');
      expect(model.isConclusive, isTrue);
      expect(model.recommendation, isNotEmpty);
    });

    test('con confianza baja marca no concluyente', () {
      final model = PredictionModel.fromJson(const {
        'label': 'glioma',
        'confidence': 0.30,
        'probabilities': {'glioma': 0.30, 'no_tumor': 0.26},
        'model_version': 'v1',
        'inference_ms': 10.0,
      });

      expect(model.isConclusive, isFalse);
      expect(model.triageLevel, 'no_concluyente');
    });
  });

  group('PredictionDetail con capa de seguridad', () {
    test('calcula el triaje desde las probabilidades', () {
      final detail = PredictionDetail.fromJson(const {
        'id': 7,
        'predicted_class': {'code': 'meningioma'},
        'model': {'version': 'v1', 'architecture': 'mobilenetv3'},
        'confidence': 0.80,
        'inference_ms': 12.0,
        'created_at': '2026-01-01T00:00:00',
        'scores': [
          {'probability': 0.80, 'lesion_class': {'code': 'meningioma'}},
          {'probability': 0.10, 'lesion_class': {'code': 'glioma'}},
          {'probability': 0.05, 'lesion_class': {'code': 'pituitario'}},
          {'probability': 0.05, 'lesion_class': {'code': 'no_tumor'}},
        ],
      });

      expect(detail.triageLevel, 'medio');
      expect(detail.isConclusive, isTrue);
      expect(detail.recommendation, isNotEmpty);
      expect(detail.topTwoMargin, closeTo(0.70, 1e-9));
    });
  });
}
