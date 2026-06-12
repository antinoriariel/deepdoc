---
description: >
  Contexto del proyecto DeepDoc OCR-to-Markdown. Aplicar cuando el usuario trabaje
  con extract.py, src/, tests/ o pida agregar soporte para nuevos formatos
  o motores OCR.
---

## Stack técnico

- Python 3.10–3.14, Typer, Rich, loguru
- MarkItDown (Microsoft, extras pdf/pptx) como pipeline rápido
- Tesseract (default) / PaddleOCR / Surya como motores OCR (patrón Strategy)
- PyMuPDF para PDF: texto embebido Y rasterización de escaneados (sin Poppler)
- python-pptx para PPTX
- pytest para tests

## Patrones clave

- `OCREngine` es un ABC; todos los motores implementan `extract_text(image, lang) -> str`
- `MarkItDownProcessor.convert()` retorna `None` si el resultado es insuficiente
- Los procesadores (`PDFProcessor`, `PPTXProcessor`) retornan siempre `list[str]`
  (bloques de texto en orden) para que `MarkdownFormatter` los consuma
- `_ENGINE_REGISTRY` en `ocr_engine.py` mapea strings a clases; agregar ahí nuevos motores
- Errores por página/diapositiva: loggear con loguru, insertar aviso en el `.md`, continuar

## Flujo de decisión OCR

1. Intentar MarkItDown → si suficiente (`len > 200` y `newlines > 5`), retornar
2. PDF con texto: PyMuPDF → bloques ordenados por coordenadas (y redondeada / x)
3. PDF escaneado: PyMuPDF `get_pixmap(dpi=300)` página a página (generador) → OCR engine
4. PPTX: python-pptx → shapes ordenados top/left → OCR solo sobre imágenes embebidas

El motor OCR se instancia de forma diferida en extract.py (solo si hay fallback).
TesseractEngine mapea ISO 639-1 → 639-3 (`es` → `spa`) automáticamente.

## Estilo esperado del Markdown generado

- YAML front matter con metadatos al inicio
- `## Página N` / `## Diapositiva N` por unidad
- `### Sección` para títulos detectados
- Tablas Markdown bien formateadas con `|---|---|`
- Referencias a imágenes: `![Figura N](images/image_NNN.png)`
- Avisos inline: `> ⚠️ Página N: no procesada`
