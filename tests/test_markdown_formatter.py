"""Tests para MarkdownFormatter."""
import pytest
from pathlib import Path

from src.markdown_formatter import MarkdownFormatter


@pytest.fixture
def fmt():
    return MarkdownFormatter()


def _body(result: str) -> str:
    """Retorna solo el cuerpo después del front matter."""
    parts = result.split("---\n\n", 1)
    return parts[1] if len(parts) > 1 else result


def test_front_matter_incluye_metadatos(fmt):
    result = fmt.format([], Path("documento.pdf"), pages=5, ocr_engine="paddle")
    assert "source: documento.pdf" in result
    assert "pages: 5" in result
    assert "ocr_engine: paddle" in result
    assert "generated_at:" in result


def test_markitdown_used_aparece_en_front_matter(fmt):
    result = fmt.format([], Path("doc.pdf"), markitdown_used=True)
    assert "markitdown_used: true" in result


def test_elimina_espacios_duplicados(fmt):
    result = fmt.format(["texto  con  doble  espacio"], Path("a.pdf"))
    body = _body(result)
    assert "  " not in body


def test_normaliza_headers_duplicados(fmt):
    result = fmt.format(["## ## Header doble"], Path("a.pdf"))
    assert "## ## " not in result
    assert "## Header doble" in result


def test_normaliza_listas_a_guion(fmt):
    result = fmt.format(["• bullet uno\n• bullet dos"], Path("a.pdf"))
    assert "• " not in result
    assert "- bullet" in result


def test_limit_lineas_en_blanco(fmt):
    blocks = ["párrafo uno\n\n\n\n\npárrafo dos"]
    result = fmt.format(blocks, Path("a.pdf"))
    assert "\n\n\n" not in result


def test_formatea_tabla_markdown(fmt):
    table = "| A | B |\n|---|---|\n| 1 | 2 |"
    result = fmt.format([table], Path("a.pdf"))
    assert "| A | B |" in result
    assert "|---|---|" in result


def test_elimina_caracteres_de_control(fmt):
    result = fmt.format(["texto\x00nulo\x01control"], Path("a.pdf"))
    assert "\x00" not in result
    assert "\x01" not in result


def test_languages_en_front_matter(fmt):
    result = fmt.format([], Path("a.pdf"), languages=["fr", "de"])
    assert "languages: [fr, de]" in result


def test_bloques_vacios_se_omiten(fmt):
    result = fmt.format(["", "  ", "contenido real"], Path("a.pdf"))
    body = _body(result)
    assert body.strip() == "contenido real"
