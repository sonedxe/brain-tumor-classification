import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';

import '../data/models/prediction_model.dart';
import '../data/repositories/prediction_repository.dart';
import '../data/services/api_service.dart';
import '../data/services/connectivity_service.dart';
import '../data/services/offline_service.dart';

enum PredictionStatus { idle, loading, success, error }

/// ViewModel de MVVM: mantiene el estado y las reglas, sin saber de widgets.
///
/// Las vistas observan este objeto con `Consumer` o `context.watch` y se
/// redibujan. Ninguna vista hace HTTP ni decide que hacer tras un error.
/// Trabaja con `XFile` para ser compatible con movil y web.
///
/// Si no hay conexión (o el backend no responde), clasifica con el modelo
/// ONNX local y deja la predicción en cola para sincronizarla.
class PredictionViewModel extends ChangeNotifier {
  PredictionViewModel({
    PredictionRepository? repository,
    OfflineService? offlineService,
    ConnectivityService? connectivity,
  })  : _repository = repository ?? PredictionRepository(),
        _offlineService = offlineService,
        _connectivity = connectivity ?? ConnectivityService.instance {
    _connectivity.addListener(notifyListeners);
  }

  final PredictionRepository _repository;
  final OfflineService? _offlineService;
  final ConnectivityService _connectivity;
  final ImagePicker _picker = ImagePicker();

  PredictionStatus _status = PredictionStatus.idle;
  PredictionModel? _prediction;
  XFile? _selectedImage;
  String? _errorMessage;
  bool _usedOffline = false;

  PredictionStatus get status => _status;
  PredictionModel? get prediction => _prediction;
  XFile? get selectedImage => _selectedImage;
  String? get errorMessage => _errorMessage;
  bool get isBusy => _status == PredictionStatus.loading;
  bool get hasResult => _status == PredictionStatus.success;
  bool get isOffline => _connectivity.isOffline;
  bool get usedOffline => _usedOffline;
  bool get canClassify =>
      _selectedImage != null && _status != PredictionStatus.loading;

  Uri? get gradcamUrl {
    final path = _prediction?.gradcamPath;
    if (path == null || path.isEmpty) {
      return null;
    }
    return _repository.resolveStaticPath(path);
  }

  void selectImage(XFile file) {
    _selectedImage = file;
    _prediction = null;
    _errorMessage = null;
    _usedOffline = false;
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
      selectImage(picked);
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
      selectImage(picked);
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

    if (_connectivity.isOffline) {
      await _classifyOffline(image);
      return;
    }

    try {
      _prediction = await _repository.classify(image);
      _usedOffline = false;
      _status = PredictionStatus.success;
    } on ApiException catch (error) {
      if (error.isNetwork && _offlineService != null) {
        await _classifyOffline(image);
        return;
      }
      _fail(error.message);
    } on Exception catch (error) {
      _fail('Ocurrio un error inesperado: $error');
    }
    notifyListeners();
  }

  Future<void> _classifyOffline(XFile image) async {
    if (_offlineService == null) {
      _fail('El modo sin conexión no está disponible en este dispositivo.');
      return;
    }
    try {
      _prediction = await _offlineService.classify(image);
      _usedOffline = true;
      _status = PredictionStatus.success;
    } on OfflineException catch (error) {
      _fail(error.message);
    } on UnsupportedError catch (error) {
      _fail(error.message ?? 'Inferencia offline no soportada');
    } on Exception catch (error) {
      _fail('No se pudo clasificar sin conexión: $error');
    }
    notifyListeners();
  }

  void clear() {
    _status = PredictionStatus.idle;
    _prediction = null;
    _selectedImage = null;
    _errorMessage = null;
    _usedOffline = false;
    notifyListeners();
  }

  void _fail(String message) {
    _errorMessage = message;
    _status = PredictionStatus.error;
    notifyListeners();
  }

  @override
  void dispose() {
    _connectivity.removeListener(notifyListeners);
    _repository.dispose();
    _offlineService?.dispose();
    super.dispose();
  }
}
