"""Normalización y construcción del documento Markdown final."""
import re
from datetime import date
from pathlib import Path


class MarkdownFormatter:
    def format(
        self,
        blocks: list[str],
        source: Path,
        pages: int = 0,
        ocr_engine: str = "none",
        markitdown_used: bool = False,
        languages: list[str] | None = None,
    ) -> str:
        """Genera el Markdown final con front matter y contenido limpio."""
        languages = languages or ["es", "en"]
        front_matter = self._build_front_matter(source, pages, ocr_engine, markitdown_used, languages)
        body = "\n\n".join(b for b in blocks if b.strip())
        body = self._clean(body)
        return f"{front_matter}\n\n{body}\n"

    # ------------------------------------------------------------------
    # Front matter
    # ------------------------------------------------------------------

    def _build_front_matter(
        self,
        source: Path,
        pages: int,
        ocr_engine: str,
        markitdown_used: bool,
        languages: list[str],
    ) -> str:
        today = date.today().isoformat()
        langs = "[" + ", ".join(languages) + "]"
        return (
            f"---\n"
            f"source: {source.name}\n"
            f"pages: {pages}\n"
            f"generated_at: {today}\n"
            f"ocr_engine: {ocr_engine}\n"
            f"markitdown_used: {str(markitdown_used).lower()}\n"
            f"languages: {langs}\n"
            f"---"
        )

    # ------------------------------------------------------------------
    # Limpieza
    # ------------------------------------------------------------------

    def _clean(self, text: str) -> str:
        text = self._remove_control_chars(text)
        text = self._normalize_headers(text)
        text = self._normalize_lists(text)
        text = self._remove_duplicate_spaces(text)
        text = self._limit_blank_lines(text)
        return text.strip()

    def _remove_control_chars(self, text: str) -> str:
        """Elimina caracteres de control y artefactos NUL."""
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    def _normalize_headers(self, text: str) -> str:
        """Colapsa hashes duplicados en encabezados (e.g. '## ## Título' → '## Título')."""
        return re.sub(r"^(#{1,6})\s*#+\s*", r"\1 ", text, flags=re.MULTILINE)

    def _normalize_lists(self, text: str) -> str:
        """Normaliza viñetas a guión (-)."""
        text = re.sub(r"^\s*[•·▪▸→]\s+", "- ", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\*\s+", "- ", text, flags=re.MULTILINE)
        return text

    def _remove_duplicate_spaces(self, text: str) -> str:
        """Colapsa múltiples espacios dentro de líneas que no sean tablas."""
        lines: list[str] = []
        for line in text.split("\n"):
            if not line.startswith("|"):
                line = re.sub(r"  +", " ", line)
            lines.append(line)
        return "\n".join(lines)

    def _limit_blank_lines(self, text: str) -> str:
        """Limita a máximo dos líneas en blanco consecutivas."""
        return re.sub(r"\n{3,}", "\n\n", text)
