import 'package:flutter/material.dart';

import '../core/theme.dart';
import '../data/services/api_service.dart';
import '../data/services/report_service.dart';

/// Boton "Exportar Informe PDF" con indicador de carga.
///
/// [compact] lo muestra como boton de icono (acciones rapidas del historial).
class ExportPdfButton extends StatefulWidget {
  const ExportPdfButton({
    super.key,
    required this.predictionId,
    this.compact = false,
  });

  final int predictionId;
  final bool compact;

  @override
  State<ExportPdfButton> createState() => _ExportPdfButtonState();
}

class _ExportPdfButtonState extends State<ExportPdfButton> {
  bool _busy = false;

  Future<void> _export() async {
    if (_busy) {
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _busy = true);
    final service = ReportService();
    try {
      await service.exportReport(widget.predictionId);
    } on ApiException catch (error) {
      messenger.showSnackBar(SnackBar(content: Text(error.message)));
    } on Exception catch (error) {
      messenger.showSnackBar(
        SnackBar(content: Text('No se pudo exportar el informe: $error')),
      );
    } finally {
      service.dispose();
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final spinner = SizedBox(
      width: 18,
      height: 18,
      child: CircularProgressIndicator(
        strokeWidth: 2.2,
        color: widget.compact ? AppTheme.primary : Colors.white,
      ),
    );

    if (widget.compact) {
      return IconButton.outlined(
        tooltip: 'Exportar informe PDF',
        onPressed: _busy ? null : _export,
        icon: _busy ? spinner : const Icon(Icons.picture_as_pdf_outlined),
      );
    }

    return FilledButton.icon(
      onPressed: _busy ? null : _export,
      icon: _busy ? spinner : const Icon(Icons.picture_as_pdf_outlined),
      label: Text(_busy ? 'Generando informe…' : 'Exportar Informe PDF'),
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
      ),
    );
  }
}
