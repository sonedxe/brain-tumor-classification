/// Utilidades de presentacion (nombre de clase y fecha).
///
/// Viven en `core` para que las vistas no dupliquen logica de formato.
library;

/// Nombre legible de una clase del modelo.
String className(String value) {
  switch (value) {
    case 'glioma':
      return 'Glioma';
    case 'meningioma':
      return 'Meningioma';
    case 'pituitario':
      return 'Tumor pituitario';
    case 'no_tumor':
      return 'Sin tumor';
    default:
      return value;
  }
}

const _months = [
  'ene', 'feb', 'mar', 'abr', 'may', 'jun',
  'jul', 'ago', 'sep', 'oct', 'nov', 'dic',
];

/// Formatea un timestamp ISO del backend a `dd mmm yyyy, HH:mm`.
///
/// Si no se puede interpretar, devuelve el valor original para no ocultar
/// informacion util.
String formatTimestamp(String raw) {
  final parsed = DateTime.tryParse(raw);
  if (parsed == null) {
    return raw;
  }
  final local = parsed.toLocal();
  final day = local.day.toString().padLeft(2, '0');
  final month = _months[local.month - 1];
  final hour = local.hour.toString().padLeft(2, '0');
  final minute = local.minute.toString().padLeft(2, '0');
  return '$day $month ${local.year}, $hour:$minute';
}
