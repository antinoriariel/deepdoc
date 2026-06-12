# DeepDoc

Convierte archivos PDF y PowerPoint (PPTX) a Markdown estructurado mediante un pipeline híbrido: **MarkItDown** (Microsoft) como conversión rápida y **OCR** (Tesseract / PaddleOCR / Surya) como fallback para documentos escaneados.

## Requisitos

- **Python 3.10 – 3.14** para el núcleo (`requirements.txt`).
- **Tesseract OCR** (binario del sistema) — necesario solo para documentos escaneados.
  En Windows: [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki); marcar el paquete de idioma *Spanish* durante la instalación para usar `--lang es`.
- **Java** (opcional) — solo para el fallback de tablas con Tabula; Camelot se intenta primero y no lo necesita.

> No se requiere Poppler ni Ghostscript: las páginas escaneadas se rasterizan con PyMuPDF y Camelot ≥ 1.0 usa `pypdfium2`.

## Instalación

```bash
pip install -r requirements.txt
```

Motores OCR avanzados (opcionales, limitados por versión de Python):

```bash
pip install -r requirements-paddle.txt   # PaddleOCR — Python <= 3.11
pip install -r requirements-surya.txt    # Surya OCR — Python <= 3.12
```

**Nota sobre MarkItDown:** se instala con los extras `pdf,pptx` únicamente. El extra `[all]` arrastra dependencias (`youtube-transcript-api`, `onnxruntime<=1.20.1`) que no tienen wheels para Python 3.13+ y rompen la resolución de pip.

## Uso

```bash
# Un archivo PDF
python extract.py documento.pdf

# Una presentación PPTX
python extract.py presentacion.pptx

# Carpeta completa en paralelo
python extract.py carpeta/ --workers 8

# Con extracción de imágenes
python extract.py archivo.pdf --extract-images

# Saltar MarkItDown e ir directo a OCR
python extract.py archivo.pdf --no-markitdown --verbose
```

## Opciones CLI

| Opción | Default | Descripción |
|---|---|---|
| `--output` | `output/` | Carpeta de salida |
| `--lang` | `es,en` | Idiomas para OCR (códigos ISO 639-1) |
| `--ocr` | `tesseract` | Motor: `tesseract`, `paddle`, `surya` |
| `--extract-images` | off | Extraer imágenes a `output/images/` |
| `--workers` | 4 | Hilos paralelos para batch |
| `--verbose` | off | Logging detallado |
| `--no-markitdown` | off | Saltar MarkItDown, ir directo a OCR |
| `--recursive` | off | Buscar archivos en subcarpetas |

## Pipeline

```
Entrada → MarkItDown → ¿OK? → Markdown
                         ↓ NO
              PDF con texto → PyMuPDF (bloques ordenados) → Markdown
              PDF escaneado → PyMuPDF (render 300 DPI)    → OCR → Markdown
              PPTX          → python-pptx → OCR sobre imágenes → Markdown
```

El motor OCR se inicializa solo cuando el fallback es necesario: si MarkItDown produce un resultado suficiente, no se carga ningún modelo de reconocimiento.

## Idiomas

`--lang` acepta códigos ISO 639-1 (`es,en`). Para Tesseract se traducen automáticamente a códigos 639-3 (`spa+eng`); el paquete de idioma correspondiente debe estar instalado junto al binario.

## Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Linting

```bash
ruff check src/ extract.py tests/
```
