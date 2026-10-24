/// Contrato del modelo compartido entre backend y app offline.
///
/// Espejo de `ml/configs/labels.json` y del `metadata.json` del checkpoint
/// activo. Si cambia el modelo desplegado, se regenera el `.onnx` y se
/// actualizan estas constantes en el mismo cambio.
library;

class ModelContract {
  const ModelContract._();

  /// Orden canonico de salida del modelo (0..3).
  static const List<String> classes = [
    'glioma',
    'meningioma',
    'pituitario',
    'no_tumor',
  ];

  static const int inputSize = 224;
  static const List<double> mean = [0.485, 0.456, 0.406];
  static const List<double> std = [0.229, 0.224, 0.225];

  /// Ruta del asset ONNX (mismo `best.pt` que usa `MODEL_PATH` en el backend).
  static const String onnxAsset = 'assets/models/model.onnx';

  /// Version visible para el usuario cuando la inferencia es local.
  static const String offlineModelVersion = 'mobilenetv3-onnx';
}
