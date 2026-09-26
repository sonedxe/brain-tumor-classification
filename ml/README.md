# Datasets

Este trabajo usa MRI de cerebro de dos fuentes publicas, ambas de Kaggle. El
directorio `raw/` y `processed/` estan en `.gitignore`: las imagenes no se
versionan por su tamano, se descargan con `download.py`.

## Fuente 1 - 3.264 imagenes, 4 clases

Saeedi et al., *A novel deep learning-based approach for classification of
brain tumors*, Springerplus (2023).

Clases: `glioma`, `meningioma`, `pituitario`, `no_tumor`.

## Fuente 2 - 7.023 imagenes

Masoud Nickparvar, *Brain Tumor MRI Dataset*, Kaggle.

Incluye las cuatro clases anteriores mas subcategorias de glioma
(`glioma_tumor`, `glioma_A`, `glioma_B`, `glioma_C`, `glioma_D`, `glioma_E`),
que se colapsan en `glioma` para las cuatro salidas del modelo.

## Licencia y atribucion

Ambas fuentes requieren atribucion. Mantener esta seccion actualizada y citar
el origen en el manuscripto. Antes de publicar los resultados, confirmar los
terminos vigentes de Kaggle, que cambian entre versiones del dataset.

## Uso responsable

Las imagenes son datos medicos. No redistribuirlas en este repositorio ni
identificar a los sujetos de las muestras. El modelo se evaluara sobre
conjuntos de prueba y reportara metricas agregadas, nunca predicciones
vinculadas a un paciente.
