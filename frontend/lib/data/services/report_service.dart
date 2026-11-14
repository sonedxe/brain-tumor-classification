import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../models/prediction_detail.dart';
import '../models/prediction_model.dart';

/// Datos mínimos para construir un reporte PDF (DTO puro).
class ReportData {
  const ReportData({
    required this.label,
    required this.confidence,
    required this.probabilities,
    required this.modelVersion,
    required this.inferenceMs,
    required this.triageLevel,
    required this.recommendation,
    required this.isConclusive,
    required this.confidenceThreshold,
    required this.topTwoMargin,
    this.createdAt,
    this.offline = false,
  });

  final String label;
  final double confidence;
  final Map<String, double> probabilities;
  final String modelVersion;
  final double inferenceMs;
  final String triageLevel;
  final String recommendation;
  final bool isConclusive;
  final double confidenceThreshold;
  final double topTwoMargin;
  final String? createdAt;
  final bool offline;

  factory ReportData.fromPrediction(PredictionModel prediction) {
    return ReportData(
      label: prediction.label,
      confidence: prediction.confidence,
      probabilities: prediction.probabilities,
      modelVersion: prediction.modelVersion,
      inferenceMs: prediction.inferenceMs,
      triageLevel: prediction.triageLevel,
      recommendation: prediction.recommendation,
      isConclusive: prediction.isConclusive,
      confidenceThreshold: prediction.confidenceThreshold,
      topTwoMargin: prediction.topTwoMargin,
      offline: prediction.modelVersion.contains('onnx'),
    );
  }

  factory ReportData.fromDetail(PredictionDetail detail) {
    return ReportData(
      label: detail.label,
      confidence: detail.confidence,
      probabilities: detail.probabilities,
      modelVersion: detail.modelVersion,
      inferenceMs: detail.inferenceMs,
      triageLevel: detail.triageLevel,
      recommendation: detail.recommendation,
      isConclusive: detail.isConclusive,
      confidenceThreshold: detail.confidenceThreshold,
      topTwoMargin: detail.topTwoMargin,
      createdAt: detail.createdAt,
    );
  }
}

/// Genera el reporte PDF del resultado clínico.
///
/// MVVM: es un servicio de la capa Model; las vistas solo lo invocan.
class ReportService {
  Future<Uint8List> buildReport({
    required ReportData data,
    Uri? gradcamUrl,
    Uint8List? gradcamBytes,
  }) async {
    // La descarga vive en el servicio (MVVM): el widget no hace HTTP.
    final imageBytes = gradcamBytes ?? await fetchImage(gradcamUrl);
    final doc = pw.Document();
    final triageColor = _triageColor(data.triageLevel);
    final sorted = data.probabilities.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    final date = _formatDate(data.createdAt);

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        footer: (context) => pw.Container(
          alignment: pw.Alignment.centerRight,
          margin: const pw.EdgeInsets.only(top: 12),
          child: pw.Text(
            'Brain Tumor Classification · Página ${context.pageNumber} de '
            '${context.pagesCount}',
            style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600),
          ),
        ),
        build: (context) => [
          _header(),
          pw.SizedBox(height: 18),
          _resultCard(data, triageColor, date),
          pw.SizedBox(height: 16),
          _sectionTitle('Recomendación clínica'),
          pw.SizedBox(height: 6),
          pw.Container(
            padding: const pw.EdgeInsets.all(12),
            decoration: pw.BoxDecoration(
              color: PdfColors.grey100,
              borderRadius: pw.BorderRadius.circular(8),
              border: pw.Border.all(color: triageColor, width: 1.5),
            ),
            child: pw.Text(
              data.recommendation,
              style: const pw.TextStyle(fontSize: 10.5, lineSpacing: 3),
            ),
          ),
          pw.SizedBox(height: 16),
          _sectionTitle('Probabilidades por clase'),
          pw.SizedBox(height: 6),
          _probabilityTable(sorted),
          if (imageBytes != null) ...[
            pw.SizedBox(height: 16),
            _sectionTitle('Mapa de calor Grad-CAM'),
            pw.SizedBox(height: 6),
            pw.Center(
              child: pw.Image(
                pw.MemoryImage(imageBytes),
                height: 220,
                fit: pw.BoxFit.contain,
              ),
            ),
          ],
          pw.SizedBox(height: 16),
          _sectionTitle('Trazabilidad'),
          pw.SizedBox(height: 6),
          _traceabilityTable(data, date),
          pw.SizedBox(height: 16),
          _disclaimer(),
        ],
      ),
    );

    return doc.save();
  }

  /// Descarga el Grad-CAM. Devuelve `null` si no hay URL o falla la red.
  Future<Uint8List?> fetchImage(Uri? url) async {
    if (url == null) {
      return null;
    }
    try {
      final response = await http.get(url).timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        return response.bodyBytes;
      }
    } on Exception {
      // El reporte se genera sin imagen si la descarga falla.
    }
    return null;
  }

  pw.Widget _header() {
    return pw.Row(
      mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
      crossAxisAlignment: pw.CrossAxisAlignment.center,
      children: [
        pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              'Reporte de clasificación',
              style: pw.TextStyle(
                fontSize: 20,
                fontWeight: pw.FontWeight.bold,
                color: PdfColor.fromHex('#0F4C81'),
              ),
            ),
            pw.SizedBox(height: 2),
            pw.Text(
              'Tumores cerebrales en imágenes de resonancia magnética (MRI)',
              style: const pw.TextStyle(fontSize: 10, color: PdfColors.grey700),
            ),
          ],
        ),
        pw.Container(
          padding: const pw.EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: pw.BoxDecoration(
            color: PdfColor.fromHex('#0F4C81'),
            borderRadius: pw.BorderRadius.circular(6),
          ),
          child: pw.Text(
            'IA · Grad-CAM',
            style: pw.TextStyle(
              color: PdfColors.white,
              fontSize: 9,
              fontWeight: pw.FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  pw.Widget _resultCard(ReportData data, PdfColor triageColor, String date) {
    return pw.Container(
      padding: const pw.EdgeInsets.all(16),
      decoration: pw.BoxDecoration(
        color: PdfColor.fromHex('#F4F7FB'),
        borderRadius: pw.BorderRadius.circular(10),
        border: pw.Border.all(color: triageColor, width: 1),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Text(
                'Resultado de la clasificación',
                style: const pw.TextStyle(fontSize: 11, color: PdfColors.grey700),
              ),
              pw.Container(
                padding:
                    const pw.EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: pw.BoxDecoration(
                  color: triageColor,
                  borderRadius: pw.BorderRadius.circular(20),
                ),
                child: pw.Text(
                  _triageLabel(data.triageLevel),
                  style: pw.TextStyle(
                    color: PdfColors.white,
                    fontSize: 9,
                    fontWeight: pw.FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          pw.SizedBox(height: 10),
          pw.Text(
            _displayClass(data.label),
            style: pw.TextStyle(
              fontSize: 22,
              fontWeight: pw.FontWeight.bold,
              color: triageColor,
            ),
          ),
          pw.SizedBox(height: 4),
          pw.Text(
            'Confianza: ${_percent(data.confidence)}   ·   Margen top-1/top-2: '
            '${(data.topTwoMargin * 100).toStringAsFixed(0)} pts',
            style: const pw.TextStyle(fontSize: 10, color: PdfColors.grey700),
          ),
          pw.SizedBox(height: 2),
          pw.Text(
            'Umbral mínimo para resultado concluyente: '
            '${_percent(data.confidenceThreshold)}   ·   Fecha: $date',
            style: const pw.TextStyle(fontSize: 10, color: PdfColors.grey700),
          ),
        ],
      ),
    );
  }

  pw.Widget _sectionTitle(String text) {
    return pw.Text(
      text,
      style: pw.TextStyle(
        fontSize: 12,
        fontWeight: pw.FontWeight.bold,
        color: PdfColor.fromHex('#0F4C81'),
      ),
    );
  }

  pw.Widget _probabilityTable(List<MapEntry<String, double>> sorted) {
    return pw.TableHelper.fromTextArray(
      headers: const ['Clase', 'Probabilidad'],
      data: sorted
          .map((entry) => [_displayClass(entry.key), _percent(entry.value)])
          .toList(),
      headerStyle: pw.TextStyle(
        fontWeight: pw.FontWeight.bold,
        color: PdfColors.white,
        fontSize: 10,
      ),
      headerDecoration: pw.BoxDecoration(color: PdfColor.fromHex('#0F4C81')),
      cellStyle: const pw.TextStyle(fontSize: 10),
      cellAlignments: {
        0: pw.Alignment.centerLeft,
        1: pw.Alignment.centerRight,
      },
      border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
    );
  }

  pw.Widget _traceabilityTable(ReportData data, String date) {
    return pw.TableHelper.fromTextArray(
      headers: const ['Campo', 'Valor'],
      data: [
        ['Modelo', data.modelVersion],
        ['Latencia de inferencia', '${data.inferenceMs.toStringAsFixed(1)} ms'],
        ['Origen', data.offline ? 'Modelo local (ONNX)' : 'Backend (API)'],
        ['Fecha del reporte', date],
        ['¿Resultado concluyente?', data.isConclusive ? 'Sí' : 'No'],
      ],
      headerStyle: pw.TextStyle(
        fontWeight: pw.FontWeight.bold,
        color: PdfColors.white,
        fontSize: 10,
      ),
      headerDecoration: pw.BoxDecoration(color: PdfColor.fromHex('#0F4C81')),
      cellStyle: const pw.TextStyle(fontSize: 10),
      border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
    );
  }

  pw.Widget _disclaimer() {
    return pw.Container(
      padding: const pw.EdgeInsets.all(10),
      decoration: pw.BoxDecoration(
        color: PdfColor.fromHex('#FFF5E6'),
        border: pw.Border.all(color: PdfColor.fromHex('#F0C98A')),
        borderRadius: pw.BorderRadius.circular(6),
      ),
      child: pw.Text(
        'Herramienta de apoyo académico. No es un dispositivo médico y no '
        'sustituye el criterio de un radiólogo. El resultado debe ser '
        'confirmado por un especialista en salud.',
        style: pw.TextStyle(
          fontSize: 9,
          color: PdfColor.fromHex('#B9770E'),
          lineSpacing: 2,
        ),
      ),
    );
  }

  PdfColor _triageColor(String level) {
    switch (level) {
      case 'bajo':
        return PdfColor.fromHex('#1E8449');
      case 'medio':
        return PdfColor.fromHex('#B9770E');
      case 'alto':
        return PdfColor.fromHex('#C0392B');
      default:
        return PdfColor.fromHex('#5B6B7C');
    }
  }

  String _triageLabel(String level) {
    switch (level) {
      case 'bajo':
        return 'RIESGO BAJO';
      case 'medio':
        return 'RIESGO MEDIO';
      case 'alto':
        return 'RIESGO ALTO';
      default:
        return 'NO CONCLUYENTE';
    }
  }

  String _displayClass(String code) {
    switch (code) {
      case 'glioma':
        return 'Glioma';
      case 'meningioma':
        return 'Meningioma';
      case 'pituitario':
        return 'Tumor pituitario';
      case 'no_tumor':
        return 'Sin tumor';
      default:
        return code;
    }
  }

  String _percent(double value) => '${(value * 100).toStringAsFixed(1)} %';

  String _formatDate(String? iso) {
    final parsed = iso != null ? DateTime.tryParse(iso) : null;
    final date = (parsed ?? DateTime.now()).toLocal();
    String two(int value) => value.toString().padLeft(2, '0');
    return '${date.year}-${two(date.month)}-${two(date.day)} '
        '${two(date.hour)}:${two(date.minute)}';
  }
}
