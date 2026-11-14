import 'dart:io';
import 'dart:typed_data';

import 'package:path_provider/path_provider.dart';

import 'image_store_interface.dart';

/// Implementacion nativa: guarda cada imagen como `<localId>.img` en
/// `<docs>/offline_images`. `rootDir` es inyectable en tests (un `Directory`
/// temporal pasado como `Object?` para no exponer `dart:io` en la API comun).
class PlatformImageStore implements ImageStore {
  Directory? _dir;

  @override
  Future<void> init(Object? rootDir) async {
    if (_dir != null) {
      return;
    }
    final Directory root;
    if (rootDir is Directory) {
      root = rootDir;
    } else {
      root = await getApplicationDocumentsDirectory();
    }
    _dir = Directory('${root.path}/offline_images');
    if (!_dir!.existsSync()) {
      await _dir!.create(recursive: true);
    }
  }

  Future<Directory> _images(Object? rootDir) async {
    await init(rootDir);
    return _dir!;
  }

  @override
  Future<void> writeImage(String localId, Uint8List bytes) async {
    // init ya se llamo desde LocalDB.init; este metodo no recibe rootDir.
    final dir = _dir;
    if (dir == null) {
      throw StateError('ImageStore no inicializado');
    }
    final file = File('${dir.path}/$localId.img');
    await file.writeAsBytes(bytes, flush: true);
  }

  @override
  Future<Uint8List?> readImage(String localId) async {
    final dir = _dir;
    if (dir == null) {
      return null;
    }
    final file = File('${dir.path}/$localId.img');
    if (!file.existsSync()) {
      return null;
    }
    return file.readAsBytes();
  }

  @override
  Future<void> deleteImage(String localId) async {
    final dir = _dir;
    if (dir == null) {
      return;
    }
    final file = File('${dir.path}/$localId.img');
    if (file.existsSync()) {
      await file.delete();
    }
  }

  // Solo para uso interno de LocalDB en nativo.
  Future<Directory> imagesForRoot(Object? rootDir) => _images(rootDir);
}

ImageStore createImageStore() => PlatformImageStore();
