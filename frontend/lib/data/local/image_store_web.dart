import 'dart:typed_data';

import 'image_store_interface.dart';

/// Implementacion web: `dart:io` no existe en JavaScript, asi que las
/// imagenes pendientes se guardan en memoria durante la sesion. Los
/// metadatos siguen en `SharedPreferences` (con soporte web).
class PlatformImageStore implements ImageStore {
  final Map<String, Uint8List> _memory = {};

  @override
  Future<void> init(Object? rootDir) async {}

  @override
  Future<void> writeImage(String localId, Uint8List bytes) async {
    _memory[localId] = bytes;
  }

  @override
  Future<Uint8List?> readImage(String localId) async => _memory[localId];

  @override
  Future<void> deleteImage(String localId) async {
    _memory.remove(localId);
  }
}

ImageStore createImageStore() => PlatformImageStore();
