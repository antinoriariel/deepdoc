"""Tests para PDFProcessor."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

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


def test_pdf_escaneado_activa_ocr(mock_engine, tmp_path):
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
    mock_doc.__iter__ = lambda self: iter([mock_page])
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
    """Un PDF sin texto embebido debe pasar por convert_from_path y OCR."""
    from PIL import Image

    processor = PDFProcessor(mock_engine)
    blank = Image.new("RGB", (100, 100))

    mock_page = MagicMock()
    mock_page.get_text.return_value = ""  # sin texto embebido
    mock_page.get_images.return_value = []

    mock_doc = MagicMock()
    mock_doc.__len__ = lambda self: 1
    mock_doc.__iter__ = lambda self: iter([mock_page])
    mock_doc.__getitem__ = lambda self, i: mock_page

    with patch("fitz.open", return_value=mock_doc):
        with patch("pdf2image.convert_from_path", return_value=[blank]):
            processor._process_scanned_pdf(tmp_path / "scan.pdf")

    mock_engine.extract_text.assert_called_once()
