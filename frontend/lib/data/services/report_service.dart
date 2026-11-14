import 'dart:io' show File;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import 'api_service.dart';

/// Descarga el informe PDF de una prediccion y abre el dialogo nativo para
/// guardarlo o compartirlo (WhatsApp, Drive, correo, "Guardar en archivos"…).
class ReportService {
  ReportService({ApiService? apiService})
      : _api = apiService ?? ApiService(),
        _ownsApi = apiService == null;

  final ApiService _api;
  final bool _ownsApi;

  /// Lanza [ApiException] con un mensaje listo para mostrar al usuario.
  Future<void> exportReport(int predictionId) async {
    final bytes = await _api.fetchReportPdf(predictionId);
    final name = 'informe-$predictionId.pdf';

    final XFile file;
    if (kIsWeb) {
      file = XFile.fromData(bytes, name: name, mimeType: 'application/pdf');
    } else {
      final dir = await getTemporaryDirectory();
      final path = '${dir.path}/$name';
      await File(path).writeAsBytes(bytes, flush: true);
      file = XFile(path, mimeType: 'application/pdf', name: name);
    }

    await Share.shareXFiles(
      [file],
      subject: 'Informe clinico #$predictionId',
      text: 'Informe de apoyo al diagnostico (no reemplaza criterio medico).',
    );
  }

  void dispose() {
    if (_ownsApi) {
      _api.dispose();
    }
  }
}
