import 'package:flutter/material.dart';
import 'package:printing/printing.dart';

import '../core/theme.dart';
import '../data/services/report_service.dart';

/// Botón para generar y compartir el reporte PDF del resultado.
///
/// Descarga el Grad-CAM (si está disponible), construye el PDF y abre la hoja
/// de compartir/guardar del sistema. La app sigue funcionando si la imagen no
/// se puede descargar: el reporte se genera sin ella.
class ExportReportButton extends StatefulWidget {
  const ExportReportButton({
    super.key,
    required this.report,
    this.gradcamUrl,
    this.filename = 'reporte-clasificacion.pdf',
    this.compact = false,
  });

  final ReportData report;
  final Uri? gradcamUrl;
  final String filename;

  /// Si es `true`, se muestra como icono (por ejemplo en el AppBar).
  final bool compact;

  @override
  State<ExportReportButton> createState() => _ExportReportButtonState();
}

class _ExportReportButtonState extends State<ExportReportButton> {
  bool _busy = false;

  Future<void> _export() async {
    setState(() => _busy = true);
    try {
      final bytes = await ReportService().buildReport(
        data: widget.report,
        gradcamUrl: widget.gradcamUrl,
      );
      await Printing.sharePdf(bytes: bytes, filename: widget.filename);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Reporte PDF generado.')),
        );
      }
    } on Exception catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('No se pudo generar el PDF: $error')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.compact) {
      return IconButton(
        onPressed: _busy ? null : _export,
        tooltip: 'Exportar reporte PDF',
        icon: _busy
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : const Icon(Icons.picture_as_pdf_outlined),
      );
    }

    return ElevatedButton.icon(
      onPressed: _busy ? null : _export,
      icon: _busy
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Colors.white,
              ),
            )
          : const Icon(Icons.picture_as_pdf_outlined),
      label: Text(_busy ? 'Generando PDF…' : 'Exportar reporte PDF'),
      style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryDark),
    );
  }
}
