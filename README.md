# DeepDoc

Convierte archivos PDF y PowerPoint (PPTX) a Markdown estructurado mediante un pipeline híbrido: **MarkItDown** (Microsoft) como conversión rápida y **OCR avanzado** (PaddleOCR / Surya / Tesseract) como fallback.

## Instalación

```bash
pip install -r requirements.txt
```

> Tesseract requiere instalación del binario del sistema. En Windows: [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
> pdf2image requiere Poppler. En Windows: [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows).

## Uso básico

```bash
# Un archivo PDF
python extract.py documento.pdf

# Una presentación PPTX
python extract.py presentacion.pptx

# Carpeta completa en paralelo
python extract.py carpeta/ --workers 8

# Con extracción de imágenes y OCR Tesseract
python extract.py archivo.pdf --extract-images --ocr tesseract

# Saltar MarkItDown e ir directo a OCR
python extract.py archivo.pdf --no-markitdown --verbose
```

## Opciones CLI

| Opción | Default | Descripción |
|---|---|---|
| `--output` | `output/` | Carpeta de salida |
| `--lang` | `es,en` | Idiomas para OCR |
| `--ocr` | `paddle` | Motor: `paddle`, `surya`, `tesseract` |
| `--extract-images` | off | Extraer imágenes a `output/images/` |
| `--workers` | 4 | Hilos paralelos para batch |
| `--verbose` | off | Logging detallado |
| `--no-markitdown` | off | Saltar MarkItDown, ir directo a OCR |
| `--recursive` | off | Buscar archivos en subcarpetas |

## Pipeline

```
Entrada → MarkItDown → ¿OK? → Markdown
                         ↓ NO
              PDF con texto → PyMuPDF → Markdown
              PDF escaneado → pdf2image → OCR → Markdown
              PPTX          → python-pptx → OCR sobre imágenes → Markdown
```

## Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Linting

```bash
ruff check src/
```
