"""Wrapper sobre MarkItDown de Microsoft para conversión rápida a Markdown."""
from pathlib import Path
from typing import Optional

from loguru import logger


class MarkItDownProcessor:
    def __init__(self) -> None:
        try:
            from markitdown import MarkItDown
            self._md = MarkItDown()
        except ImportError as exc:
            raise ImportError(f"markitdown no está instalado: {exc}") from exc

    def convert(self, path: Path) -> Optional[str]:
        """Intenta conversión rápida. Retorna None si el resultado es insuficiente."""
        try:
            result = self._md.convert(str(path))
            text = result.text_content
            if self._is_sufficient(text):
                logger.debug(f"MarkItDown: resultado suficiente para {path.name}")
                return text
            logger.debug(f"MarkItDown: resultado insuficiente para {path.name}, activando fallback OCR")
            return None
        except Exception as exc:
            logger.warning(f"MarkItDown falló para {path.name}: {exc}")
            return None

    def _is_sufficient(self, text: str) -> bool:
        """Evalúa si el Markdown generado tiene contenido real."""
        stripped = text.strip()
        return len(stripped) > 200 and stripped.count("\n") > 5
