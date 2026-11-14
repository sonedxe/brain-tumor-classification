import 'dart:typed_data';

/// Almacenamiento de las imagenes pendientes del modo offline.
///
/// La implementacion nativa usa `dart:io` + `path_provider` y la web usa un
/// mapa en memoria, porque `dart:io` no compila a JavaScript.
abstract class ImageStore {
  Future<void> init(Object? rootDir);

  Future<void> writeImage(String localId, Uint8List bytes);

  Future<Uint8List?> readImage(String localId);

  Future<void> deleteImage(String localId);
}
