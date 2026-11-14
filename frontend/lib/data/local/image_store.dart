// Import condicional: en nativo usa dart:io + path_provider, en web un mapa
// en memoria para que `flutter build web` no intente compilar dart:io.
export 'image_store_interface.dart';
export 'image_store_web.dart' if (dart.library.ffi) 'image_store_io.dart';
