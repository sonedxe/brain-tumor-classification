# Notas de correccion entre el repositorio y el manuscripto

Registro de las desviaciones entre lo que dice el paper (LEIRD 2025) y lo que
realmente hace el codigo. Sirve para actualizar el manuscripto antes del envio
y para responder en sustentacion si alguien lo pregunta.

## 1. Transformaciones de entrenamiento

Las cinco arquitecturas se entrenan mediante `torchvision.transforms`.
Entrenamiento: `Resize((224, 224))`, `RandomHorizontalFlip()`,
`RandomRotation(10)`, `ToTensor()` y normalizacion ImageNet. Validacion/test
usan Resize, ToTensor y la misma normalizacion, sin aumentos aleatorios.

## 2. Normalizacion ImageNet y tamano de entrada

Los cinco modelos usan media `[0.485, 0.456, 0.406]` y desviacion
`[0.229, 0.224, 0.225]`. El tensor PyTorch es `N x 3 x 224 x 224`.
La configuracion se encuentra en `ml/configs/<modelo>.yaml`.

## 3. DenseNet121 como quinto modelo

**Estado:** `ml/models/densenet121/` existe en el repositorio, pero DenseNet121
no aparece en la comparacion del manuscripto actual, que describe tres modelos
optimizados contra ResNet18 como referencia.

**Decision tomada:** se incorpora como quinto candidato, de modo que la
comparacion queda con cuatro modelos optimizados y una referencia.

**Acciones sobre el manuscripto:**
- Agregar DenseNet121 a la lista de modelos del OE1.
- Agregar una fila a la tabla de la seccion III.
- Agregar su linea a la tabla de resultados del OE2.

## 4. Grad-CAM en la capa correcta

La capa objetivo de Grad-CAM es especifica de cada arquitectura y se declara
por YAML. `ml/evaluation/gradcam.py` resuelve atributos e indices:

| Modelo | Capa objetivo |
| --- | --- |
| MobileNetV3 | `features[-1]` |
| EfficientNetB0 | `features[-1]` |
| ShuffleNetV2 | `conv5` |
| DenseNet121 | `features.denseblock4` |
| ResNet18 | `layer4[-1]` |

## 5. Las cinco arquitecturas usan torchvision

`ml/training/model_factory.py` usa las cinco implementaciones torchvision y
sus pesos ImageNet. Reemplaza la capa final especifica: `classifier[-1]` para
MobileNetV3 y EfficientNetB0, `fc` para ShuffleNetV2 y ResNet18, y
`classifier` para DenseNet121. El entrenamiento congela los parametros
preentrenados y optimiza solo la capa de salida nueva.

## 6. Base de datos SQLite

El paper no especifica tecnologia de persistencia. El repositorio usa SQLite
mediante SQLAlchemy, y la tabla `prediction_logs` registra
`image_hash, label, confidence, model_version, inference_ms, created_at`.

El campo `model_version` no es decorativo: permite reconstruir que modelo
produjo cada resultado, que es un requisito de reproducibilidad y no solo de
trazabilidad de la app.

## 7. Que NO se guarda

Por tratarse de datos medicos, la app no persiste informacion identificable del
paciente: ni nombre, ni fecha de nacimiento, ni los tags DICOM de la imagen, ni
el nombre original del archivo. Solo el hash SHA-256, que permite detectar
imagenes repetidas sin revelar contenido clinico. Conviene mencionarlo
explicitamente en la sustentacion.
