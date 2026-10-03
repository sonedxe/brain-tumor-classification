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
`gradcam.target_layer` dentro de cada YAML de `ml/configs/`,
`ml/evaluation/gradcam.py` resuelve `nombre`, `nombre[indice]` e indices
sueltos, y busca la ultima capa convolucional cuando el valor no se especifica.

| Modelo | Capa objetivo | Nota |
| --- | --- | --- |
| MobileNetV3 | `conv_head` | timm no expone `features` en esta arquitectura |
| EfficientNetB0 | `conv_head` | idem |
| ShuffleNetV2 | `conv5` | modulo torchvision (ver seccion 7) |
| DenseNet121 | `features.denseblock4` | `features[-1]` seria norm5, que no convoluciona |
| ResNet18 | `layer4[-1]` | ultimo bloque residual |

## 5. ShuffleNetV2 se construye con torchvision, no con timm

**Estado:** timm 1.x no incluye ningun modelo ShuffleNet (verificado en 0.9.16 y
1.0.9: cero coincidencias en el registro). El `timm_name: shufflenet_v2_x1_0` del
YAML habria abortado el entrenamiento con `Unknown model`.

**Decision tomada:** `ml/configs/shufflenetv2.yaml` declara `source: torchvision`
y `ml/training/train.py::build_model` lo construye con
`torchvision.models.shufflenet_v2_x1_0(weights=IMAGENET1K_V1)`, reemplazando su
`fc` por `Dropout(0.3) + Linear(..., 4)`. Esquema freeze hasta la epoca 15 y
fine-tuning posterior identicos a los otros cuatro. La premisa de transfer
learning con pesos ImageNet se mantiene.

**Acciones sobre el manuscripto:**

- Donde diga "los cinco modelos usan timm", precisar que ShuffleNetV2 usa
  torchvision con pesos ImageNet equivalentes.
- Mantener la fila de ShuffleNetV2 en todas las tablas: la comparacion sigue
  siendo homogenea (mismos splits, mismo head de 4 clases, mismo protocolo).

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
