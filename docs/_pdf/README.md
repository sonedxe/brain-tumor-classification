# Generación de PDF

Los documentos se escriben en Markdown (GitHub-flavored) y se convierten a PDF
con **Pandoc + WeasyPrint**. Las portadas y el estilo viven en esta carpeta.

## Requisitos

- `pandoc` (probado con 3.x)
- `weasyprint` 70+ con Pango/Cairo

En macOS:

```bash
brew install pandoc pango cairo gdk-pixbuf libffi
python3 -m venv .venv-pdf
.venv-pdf/bin/pip install weasyprint
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib .venv-pdf/bin/weasyprint --version
```

## Generar

```bash
WEASYPRINT="$(pwd)/.venv-pdf/bin/weasyprint" ./docs/_pdf/build.sh
```

Salidas:

- `docs/arquitectura-cloud.pdf`
- `docs/pruebas-software.pdf`

## Estructura

| Archivo | Uso |
| --- | --- |
| `style.css` | Estilo de página, tablas, código, portada y TOC |
| `cover-arquitectura-cloud.html` | Portada del documento de arquitectura |
| `cover-pruebas-software.html` | Portada del documento de pruebas |
| `build.sh` | Convierte ambos Markdown a PDF |

## Notas

- WeasyPrint usa `target-counter()` para numerar las entradas del TOC y
  `counter(pages)` para el total de páginas.
- Si se edita el Markdown, volver a ejecutar `build.sh`.
- Si se cambia el título de la portada, actualizar también el `<title>` en
  `build.sh`.
- Los PDF no reemplazan al Markdown: el Markdown es la fuente de verdad.
