// Import condicional: en nativo (dart:ffi disponible) usa la
// implementacion real con package:onnxruntime; en web usa el stub sin ffi
// para que `flutter run -d chrome` compile.
export 'onnx_predictor_web.dart'
    if (dart.library.ffi) 'onnx_predictor_io.dart';
