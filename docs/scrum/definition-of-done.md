# Definition of Done (DoD)

Una historia se considera **Done** solo si cumple **todos** los criterios que le
apliquen. El DoD es comun a todo el equipo y no se negocia sprint a sprint.

## Para codigo (backend, frontend, ML)

1. Implementado y mergeado en `main` (o listo para merge sin conflictos).
2. Sin marcadores `TODO` funcionales pendientes sin justificar.
3. Documentado: docstrings / comentarios de cabecera que explican el **por que**,
   no el que.
4. Estilo y lint en verde:
   - Backend: `python -m pytest` (todas las pruebas pasan).
   - Frontend: `flutter analyze` sin issues y `flutter test` en verde.
   - ML: `python ml/smoke_test.py` termina 7/7 OK.
5. Cubierto por al menos una prueba automatizada cuando aporta valor
   (contrato de API, regla de ViewModel, parseo de DTO).
6. Respeta las decisiones transversales:
   - Las clases salen solo de `ml/configs/labels.json`.
   - No se persisten datos identificables del paciente.
   - El frontend no conoce la URL fuera de `ApiService`/`AppConfig`.

## Para MVVM (frontend)

7. La vista no hace HTTP, no parsea JSON y no lee archivos: solo observa el
   ViewModel y emite intents.
8. El estado y las reglas viven en el ViewModel; el acceso a red, en un
   repository/service inyectable.
9. La capa que hace la peticion es sustituible por un fake en pruebas.

## Para las historias de ML

10. El experimento es reproducible: mismas semillas, mismo split y comando
    documentado.
11. Los resultados quedan en `ml/evaluation/reports/` (JSON) y, si aplica, en
    `docs/tabla-comparativa.md`.
12. Cualquier desviacion respecto al paper se anota en
    `docs/notas-correccion-paper.md`.

## Para las historias de documentacion

13. El documento esta en español, sin acentos en identificadores de codigo y en
    Markdown dentro de `docs/`.
14. Explica decisiones y las conecta con los objetivos OE1-OE4 o con la rubrica.
15. No duplica: referencia el documento fuente en lugar de copiarlo.
