import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';

import '../data/models/prediction_model.dart';
import '../data/repositories/prediction_repository.dart';
import '../data/services/api_service.dart';

enum PredictionStatus { idle, loading, success, error }

/// ViewModel de MVVM: mantiene el estado y las reglas, sin saber de widgets.
///
/// Las vistas observan este objeto con `Consumer` o `context.watch` y se
/// redibujan. Ninguna vista hace HTTP ni decide que hacer tras un error.
class PredictionViewModel extends ChangeNotifier {
  PredictionViewModel({PredictionRepository? repository})
      : _repository = repository ?? PredictionRepository();

  final PredictionRepository _repository;
  final ImagePicker _picker = ImagePicker();

  PredictionStatus _status = PredictionStatus.idle;
  PredictionModel? _prediction;
  File? _selectedImage;
  String? _errorMessage;

  PredictionStatus get status => _status;
  PredictionModel? get prediction => _prediction;
  File? get selectedImage => _selectedImage;
  String? get errorMessage => _errorMessage;
  bool get isBusy => _status == PredictionStatus.loading;
  bool get hasResult => _status == PredictionStatus.success;
  bool get canClassify =>
      _selectedImage != null && _status != PredictionStatus.loading;

  Uri? get gradcamUrl {
    final path = _prediction?.gradcamPath;
    if (path == null || path.isEmpty) {
      return null;
    }
    return _repository.resolveStaticPath(path);
  }

  void selectImage(File file) {
    _selectedImage = file;
    _prediction = null;
    _errorMessage = null;
    _status = PredictionStatus.idle;
    notifyListeners();
  }

  Future<void> pickFromGallery() async {
    try {
      final picked = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1024,
        maxHeight: 1024,
      );
      if (picked == null) {
        return;
      }
      selectImage(File(picked.path));
    } on Exception catch (error) {
      _fail('No se pudo abrir la galeria: $error');
    }
  }

  Future<void> pickFromCamera() async {
    try {
      final picked = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1024,
        maxHeight: 1024,
      );
      if (picked == null) {
        return;
      }
      selectImage(File(picked.path));
    } on Exception catch (error) {
      _fail('No se pudo usar la camara: $error');
    }
  }

  Future<void> classify() async {
    final image = _selectedImage;
    if (image == null) {
      _fail('Selecciona una imagen primero');
      return;
    }

    _status = PredictionStatus.loading;
    _errorMessage = null;
    notifyListeners();

    try {
      _prediction = await _repository.classify(image);
      _status = PredictionStatus.success;
    } on ApiException catch (error) {
      _fail(error.message);
    } on Exception catch (error) {
      _fail('Ocurrio un error inesperado: $error');
    }
    notifyListeners();
  }

  void clear() {
    _status = PredictionStatus.idle;
    _prediction = null;
    _selectedImage = null;
    _errorMessage = null;
    notifyListeners();
  }

  void _fail(String message) {
    _errorMessage = message;
    _status = PredictionStatus.error;
    notifyListeners();
  }

  @override
  void dispose() {
    _repository.dispose();
    super.dispose();
  }
}
