# Metodologia de desarrollo: Scrum

Registro de la aplicacion de Scrum al proyecto de clasificacion de tumores
cerebrales. Sirve como evidencia del punto "aplicacion de una metodologia de
desarrollo de software" de la rubrica del examen parcial.

## 1. Por que Scrum y no cascada

El proyecto tiene dos incertidumbres grandes: **que modelo CNN resulta mejor**
(OE2) y **si el dataset alcanza** para una comparacion justa (OE1). Ambas solo
se responden experimentando, no planificando. Cascada obligaria a fijar la
arquitectura y el modelo antes de saberlo; Scrum permite entregar valor cada
semana (primero la app con inferencia simulada, luego el modelo real) sin
bloquear al resto del equipo.

La decision clave que habilita todo esto es `MOCK_INFERENCE=true`: el backend
responde con una prediccion ficticia determinista mientras el modelo se
entrena, de modo que frontend, API y entrenamiento avanzan **en paralelo**.

## 2. Roles

| Rol | Responsable | Responsabilidad principal |
| --- | --- | --- |
| Product Owner (PO) | Docente del curso | Define y prioriza el Product Backlog, acepta incrementos |
| Scrum Master (SM) | Un integrante rotativo | Facilita ceremonias, elimina impedimentos, cuida el tablero |
| Development Team | Resto del equipo | Disena, codifica, entrena y valida; equipo auto-organizado |

El equipo es pequeno (2-4 personas). Los roles de frontend, API y ML se
reparten, pero **cada integrante puede tocar cualquier capa**; la especialidad
no es una barrera.

## 3. Ceremonias

| Ceremonia | Cuando | Duracion | Salida |
| --- | --- | --- | --- |
| Sprint Planning | Inicio de semana | 30 min | Sprint Goal + items comprometidos |
| Daily / avance | Inicio de sesion de trabajo | 5-10 min | Impedimentos y plan del dia |
| Sprint Review | Sabado (sesion remota) | 15 min | Incremento demostrado al PO |
| Retrospectiva | Cierre del sprint | 15 min | 1 mejora concreta para el proximo sprint |

## 4. Artefactos

| Artefacto | Documento | Descripcion |
| --- | --- | --- |
| Product Backlog | `product-backlog.md` | Historias de usuario priorizadas |
| Sprint Backlog | `sprints.md` | Items e incremento de cada sprint |
| Incremento | repositorio | Codigo, pesos y documentos "Done" |
| Definition of Done | `definition-of-done.md` | Criterio comun de terminado |

## 5. Cadencia

El curso opera por semanas; **una semana = un sprint**. La sesion del sabado es
el hito sincrono (Sprint Review). Al cierre de cada sprint el incremento debe
seguir en verde: `pytest` del backend, `flutter test` y `flutter analyze` sin
errores, y el smoke test de ML (`python ml/smoke_test.py`).

## 6. Relacion con las fases tecnicas

Scrum da el **como** (iteraciones, backlog, incremento); `docs/flujograma.md`
da el **que** (cinco fases tecnicas y su correspondencia con los OE1-OE4). Los
sprints de `sprints.md` mapean a esas fases.
