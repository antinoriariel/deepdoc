---
description: Agrega un nuevo motor OCR al sistema siguiendo el patrón Strategy.
allowed-tools: Read, Write, Bash
---

El usuario quiere agregar el motor: $ARGUMENTS

1. Leer `src/ocr_engine.py` para entender la interfaz `OCREngine`
2. Crear la nueva clase que implemente `extract_text(image, lang) -> str`
3. Registrarla en `_ENGINE_REGISTRY` con su clave string
4. Agregar la dependencia a `requirements.txt` si aplica
5. Crear test básico en `tests/test_ocr_engine.py`
6. Actualizar `CLAUDE.md` si el motor requiere setup especial
