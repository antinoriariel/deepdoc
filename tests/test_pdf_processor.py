"""Tests para PDFProcessor."""
import pytest
from unittest.mock import MagicMock, patch

from src.pdf_processor import PDFProcessor
from src.ocr_engine import OCREngine


@pytest.fixture
def mock_engine():
    engine = MagicMock(spec=OCREngine)
    engine.extract_text.return_value = "texto OCR"
    return engine


def test_pdf_vacio_retorna_lista(mock_engine, tmp_path):
    """Un path inexistente retorna lista vacía sin lanzar excepción."""
    processor = PDFProcessor(mock_engine)
    result = processor.process(tmp_path / "inexistente.pdf")
    assert isinstance(result, list)
    assert result == []


def test_pdf_escaneado_activa_ocr(mock_engine):
    """Verifica que el motor OCR es el configurado."""
    processor = PDFProcessor(mock_engine)
    assert processor.ocr_engine is mock_engine


def test_pdf_con_texto_no_usa_ocr(mock_engine, tmp_path):
    """Un PDF con texto embebido no debe invocar el motor OCR."""
    processor = PDFProcessor(mock_engine)

    mock_page = MagicMock()
    mock_page.get_text.side_effect = lambda fmt=None: (
        "texto embebido suficiente " * 10 if fmt is None else [
            (0, 0, 200, 20, "Bloque de texto largo embebido en el PDF", 0, 0)
        ]
    )
    mock_page.get_images.return_value = []

    mock_doc = MagicMock()
    mock_doc.__len__ = lambda self: 1
    mock_doc.__getitem__ = lambda self, i: mock_page

    with patch("fitz.open", return_value=mock_doc):
        with patch.object(processor.table_detector, "extract_from_pdf_page", return_value=[]):
            processor.process(tmp_path / "fake.pdf")

    mock_engine.extract_text.assert_not_called()


def test_get_page_count_retorna_cero_si_falla(mock_engine, tmp_path):
    processor = PDFProcessor(mock_engine)
    count = processor.get_page_count(tmp_path / "no_existe.pdf")
    assert count == 0


def test_process_scanned_invoca_ocr(mock_engine, tmp_path):
    """Un PDF escaneado rasteriza con PyMuPDF e invoca el motor OCR."""
    processor = PDFProcessor(mock_engine)

    mock_pix = MagicMock()
    mock_pix.width = 4
    mock_pix.height = 4
    mock_pix.samples = b"\xff" * (4 * 4 * 3)

    mock_page = MagicMock()
    mock_page.get_pixmap.return_value = mock_pix

    mock_doc = MagicMock()
    mock_doc.__len__ = lambda self: 1
    mock_doc.__getitem__ = lambda self, i: mock_page

    with patch("fitz.open", return_value=mock_doc):
        blocks = processor._process_scanned_pdf(tmp_path / "scan.pdf")

    mock_engine.extract_text.assert_called_once()
    assert any("Página 1" in b for b in blocks)


def test_render_pages_pagina_corrupta_no_aborta(mock_engine, tmp_path):
    """Una página que falla al rasterizar produce None y el resto continúa."""
    processor = PDFProcessor(mock_engine)

    mock_pix = MagicMock()
    mock_pix.width = 4
    mock_pix.height = 4
    mock_pix.samples = b"\xff" * (4 * 4 * 3)

    ok_page = MagicMock()
    ok_page.get_pixmap.return_value = mock_pix

    bad_page = MagicMock()
    bad_page.get_pixmap.side_effect = RuntimeError("página corrupta")

    pages = [bad_page, ok_page]
    mock_doc = MagicMock()
    mock_doc.__len__ = lambda self: 2
    mock_doc.__getitem__ = lambda self, i: pages[i]

    with patch("fitz.open", return_value=mock_doc):
        rendered = list(processor._render_pages(tmp_path / "scan.pdf"))

    assert rendered[0][1] is None
    assert rendered[1][1] is not None
