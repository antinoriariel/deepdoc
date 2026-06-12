---
description: >
  Contexto del proyecto DeepDoc OCR-to-Markdown. Aplicar cuando el usuario trabaje
  con extract.py, src/, tests/ o pida agregar soporte para nuevos formatos
  o motores OCR.
---

## Stack técnico

- Python 3.11+, Typer, Rich, loguru
- MarkItDown (Microsoft) como pipeline rápido
- PaddleOCR / Surya / Tesseract como motores OCR (patrón Strategy)
- PyMuPDF para PDF con texto, pdf2image para PDF escaneados
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
3. PDF escaneado: pdf2image → OCR engine configurado
4. PPTX: python-pptx → shapes ordenados top/left → OCR solo sobre imágenes embebidas

## Estilo esperado del Markdown generado

- YAML front matter con metadatos al inicio
- `## Página N` / `## Diapositiva N` por unidad
- `### Sección` para títulos detectados
- Tablas Markdown bien formateadas con `|---|---|`
- Referencias a imágenes: `![Figura N](images/image_NNN.png)`
- Avisos inline: `> ⚠️ Página N: no procesada`
