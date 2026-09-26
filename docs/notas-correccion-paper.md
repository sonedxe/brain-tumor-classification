# Notas de correccion entre el repositorio y el manuscripto

Registro de las desviaciones entre lo que dice el paper (LEIRD 2025) y lo que
realmente hace el codigo. Sirve para actualizar el manuscripto antes del envio
y para responder en sustentacion si alguien lo pregunta.

## 1. ImageDataGenerator -> transforms de torchvision

**Donde aparece en el paper:** seccion de preprocesamiento, donde se describe
`ImageDataGenerator` con rotacion, zoom y flip.

**Que hace el codigo:** `ml/dataset/augmentation.py` usa
`torchvision.transforms`, concretamente `timm.data.create_transform` a partir de
`resolve_data_config()` del modelo.

**Por que:** `keras.applications` no incluye **ResNet18** ni **ShuffleNetV2**,
que son respectivamente el modelo de referencia y uno de los tres candidatos
principales. Sin esos pesos ImageNet, ambos habrian que entrenarse desde cero
con 3.264 imagenes, lo que invalida la premisa de transfer learning del
trabajo y hace incomparable la tabla. `timm` si provee los cinco modelos con
pesos ImageNet y una API uniforme, que es la garantia de que la comparacion sea
homogenea.

**Como actualizarlo:** sustituir la mencion de `ImageDataGenerator` por
"data augmentation" o por `torchvision.transforms`. La lista de transformaciones
(rotation, zoom, horizontal flip) se mantiene igual.

## 2. Normalizacion distinta por modelo

**Donde aparece en el paper:** seccion de preprocesamiento, donde se indica
normalizacion en el rango -1 a 1.

**Realidad:** ese rango solo es valido para 3 de los 5 modelos.

| Modelo | Normalizacion | Es -1 a 1 |
| --- | --- | --- |
| MobileNetV3 | `mean=std=0.5` | si |
| EfficientNetB0 | `mean=std=0.5` | si |
| ShuffleNetV2 | `mean=std=0.5` | si |
| DenseNet121 | `mean=std=0.5` | si |
| ResNet18 | medias y desviaciones de ImageNet | **no** |

Ademas el paper menciona la entrada como `256x256x3` (formato TensorFlow). El
formato real de PyTorch es `NCHOS` -> `3x256x256`, donde `N` es el batch size.

**Como actualizarlo:** indicar que la normalizacion se define por modelo desde
`ml/configs/<modelo>.yaml` y que el tensor de entrada es `3x256x256`.

**Por que importa:** usar una sola normalizacion para los cinco modelos hace que
ResNet18 entrene sin converger, sin dar error visible. Es un fallo silencioso.

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

La capa objetivo de Grad-CAM no es la misma en las cinco arquitecturas, y
equivocarse produce un mapa de calor vacio o ruido. El valor esta en
`gradcam_target_layer` dentro de cada YAML de `ml/configs/`, y
`ml/evaluation/gradcam.py` incluye un resolver que busca la ultima capa
convolucional cuando el valor no se especifica.

| Modelo | Capa objetivo |
| --- | --- |
| MobileNetV3 | `features[-1]` |
| EfficientNetB0 | `features[-1]` |
| ShuffleNetV2 | `features[-1]` |
| DenseNet121 | `features[-1]` |
| ResNet18 | `layer4[-1]` |

## 5. Base de datos SQLite

El paper no especifica tecnologia de persistencia. El repositorio usa SQLite
mediante SQLAlchemy, y la tabla `prediction_logs` registra
`image_hash, label, confidence, model_version, inference_ms, created_at`.

El campo `model_version` no es decorativo: permite reconstruir que modelo
produjo cada resultado, que es un requisito de reproducibilidad y no solo de
trazabilidad de la app.

## 6. Que NO se guarda

Por tratarse de datos medicos, la app no persiste informacion identificable del
paciente: ni nombre, ni fecha de nacimiento, ni los tags DICOM de la imagen, ni
el nombre original del archivo. Solo el hash SHA-256, que permite detectar
imagenes repetidas sin revelar contenido clinico. Conviene mencionarlo
explicitamente en la sustentacion.
