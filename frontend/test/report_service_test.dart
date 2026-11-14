import 'package:brain_tumor_classification/data/models/prediction_model.dart';
import 'package:brain_tumor_classification/data/services/report_service.dart';
import 'package:flutter_test/flutter_test.dart';

PredictionModel _prediction({
  required String label,
  required double confidence,
  required String triage,
  required String recommendation,
  required Map<String, double> probabilities,
  String modelVersion = 'mobilenetv3-v1',
}) {
  return PredictionModel(
    label: label,
    confidence: confidence,
    probabilities: probabilities,
    modelVersion: modelVersion,
    inferenceMs: 82.4,
    isConclusive: true,
    triageLevel: triage,
    recommendation: recommendation,
    confidenceThreshold: 0.70,
    topTwoMargin: 0.93,
  );
}

void main() {
  test('genera un PDF válido con resultado y triaje', () async {
    final report = ReportData.fromPrediction(
      _prediction(
        label: 'glioma',
        confidence: 0.95,
        triage: 'alto',
        recommendation: 'Hallazgo tumoral con alta confianza.',
        probabilities: const {
          'glioma': 0.95,
          'meningioma': 0.02,
          'pituitario': 0.02,
          'no_tumor': 0.01,
        },
      ),
    );

    final bytes = await ReportService().buildReport(data: report);

    expect(bytes.length, greaterThan(1000));
    expect(String.fromCharCodes(bytes.take(5)), '%PDF-');
  });

  test('genera un PDF sin Grad-CAM (modo offline)', () async {
    final report = ReportData.fromPrediction(
      _prediction(
        label: 'no_tumor',
        confidence: 0.91,
        triage: 'bajo',
        recommendation: 'No se detectó hallazgo tumoral.',
        probabilities: const {
          'no_tumor': 0.91,
          'glioma': 0.04,
          'meningioma': 0.03,
          'pituitario': 0.02,
        },
        modelVersion: 'mobilenetv3-onnx',
      ),
    );

    final bytes = await ReportService().buildReport(data: report);

    expect(bytes.length, greaterThan(1000));
  });
}
