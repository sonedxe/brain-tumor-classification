#!/usr/bin/env bash
# Genera los PDF de docs/ a partir de los Markdown y las portadas de docs/_pdf.
#
# Requisitos:
#   - pandoc >= 3.x
#   - WeasyPrint >= 60 (con Pango/Cairo instalados)
#
# En macOS:
#   brew install pandoc pango cairo gdk-pixbuf libffi
#   python3 -m venv .venv-pdf
#   .venv-pdf/bin/pip install weasyprint
#   DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib .venv-pdf/bin/weasyprint --version
#
# Uso:
#   ./docs/_pdf/build.sh
#   WEASYPRINT=/ruta/a/weasyprint ./docs/_pdf/build.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/docs/_pdf"
WEASY="${WEASYPRINT:-weasyprint}"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "Falta pandoc. Instálalo con: brew install pandoc" >&2
  exit 1
fi

if ! command -v "$WEASY" >/dev/null 2>&1; then
  echo "Falta weasyprint. Instálalo en un venv y exporta WEASYPRINT." >&2
  echo "Ver docs/_pdf/README.md" >&2
  exit 1
fi

export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"

build() {
  local doc="$1"
  local title="$2"
  local cover="$3"

  echo "→ $doc.md"
  pandoc "$ROOT/docs/$doc.md" \
    -f gfm \
    -t html5 \
    --standalone \
    --toc \
    --toc-depth=2 \
    --metadata pagetitle="$title" \
    --metadata lang=es-ES \
    --metadata toc-title="Contenido" \
    --css=style.css \
    --include-before-body="$OUT/$cover" \
    -o "$OUT/$doc.html"

  "$WEASY" "$OUT/$doc.html" "$ROOT/docs/$doc.pdf"
  echo "✓ docs/$doc.pdf"
}

build "arquitectura-cloud" \
  "Arquitectura cloud propuesta — Clasificación de tumores cerebrales" \
  "cover-arquitectura-cloud.html"

build "pruebas-software" \
  "Plan y documento de pruebas de software — Clasificación de tumores cerebrales" \
  "cover-pruebas-software.html"

echo "Listo."
