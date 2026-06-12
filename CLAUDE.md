# DeepDoc — Claude Code Context

## Descripción del proyecto

Herramienta CLI en Python para convertir PDF y PPTX a Markdown mediante
MarkItDown (Microsoft) + OCR avanzado (PaddleOCR / Surya / Tesseract).

## Estructura clave

- `extract.py` — Entrypoint CLI (Typer + Rich)
- `src/markitdown_processor.py` — Wrapper MarkItDown (pipeline rápido)
- `src/ocr_engine.py` — Strategy pattern para motores OCR
- `src/pdf_processor.py` — Extracción de PDF (texto embebido + escaneado)
- `src/pptx_processor.py` — Extracción de PPTX
- `src/markdown_formatter.py` — Normalización y limpieza de Markdown
- `src/image_extractor.py` — Extracción de imágenes a `output/images/`
- `src/table_detector.py` — Tablas via Camelot → Tabula fallback
- `src/utils.py` — Logging, detección de tipos, helpers de rutas

## Pipeline principal

```
Entrada → MarkItDown (intento rápido) → ¿OK? → Markdown
                                           ↓ NO
                              PDF con texto? → PyMuPDF → Markdown
                              PDF escaneado? → pdf2image → OCR → Markdown
                              PPTX?          → python-pptx → OCR sobre imágenes → Markdown
```

## Convenciones del código

- Python 3.11+ con type hints en todas las funciones públicas
- Docstrings en español para funciones públicas
- PEP8; linting con `ruff check src/`
- Logging con `loguru`; nunca `print()` para mensajes del sistema
- Excepciones específicas con re-log; nunca `except Exception` silencioso
- Tests en `tests/` con pytest

## Reglas para Claude Code

- NO modificar `requirements.txt` sin avisar al usuario
- NO romper la interfaz pública de `OCREngine` (ABC con `extract_text`)
- Agregar tests unitarios para cada función nueva en `src/`
- Usar el patrón Strategy existente al agregar nuevos motores OCR
- Los procesadores (`pdf_processor`, `pptx_processor`) siempre retornan `list[str]`

## Comandos frecuentes

```bash
python extract.py archivo.pdf --verbose
python extract.py presentacion.pptx --extract-images
python extract.py carpeta/ --workers 4
# Engine default: tesseract (funciona en cualquier Python)
# Para PaddleOCR (requiere Python <=3.11): pip install -r requirements-paddle.txt
# Para Surya     (requiere Python <=3.12): pip install -r requirements-surya.txt
pytest tests/ -v --cov=src --cov-report=term-missing
ruff check src/
```
