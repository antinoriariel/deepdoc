"""Tests para ImageProcessor."""
import pytest
from unittest.mock import MagicMock, patch

from PIL import Image

from src.image_processor import ImageProcessor
from src.ocr_engine import OCREngine


@pytest.fixture
def mock_engine():
    engine = MagicMock(spec=OCREngine)
    engine.extract_text.return_value = "texto OCR de imagen"
    return engine


@pytest.fixture
def small_image(tmp_path):
    path = tmp_path / "test.png"
    Image.new("RGB", (10, 10), color=(255, 255, 255)).save(path)
    return path


def test_imagen_inexistente_retorna_lista_vacia(mock_engine, tmp_path):
    processor = ImageProcessor(mock_engine)
    result = processor.process(tmp_path / "no_existe.png")
    assert result == []
    mock_engine.extract_text.assert_not_called()


def test_imagen_valida_invoca_ocr(mock_engine, small_image):
    processor = ImageProcessor(mock_engine)
    blocks = processor.process(small_image)
    mock_engine.extract_text.assert_called_once()
    assert any("texto OCR de imagen" in b for b in blocks)


def test_ocr_vacio_produce_aviso(mock_engine, small_image):
    mock_engine.extract_text.return_value = "   "
    processor = ImageProcessor(mock_engine)
    blocks = processor.process(small_image)
    assert any("⚠️" in b for b in blocks)


def test_ocr_error_produce_aviso(mock_engine, small_image):
    mock_engine.extract_text.side_effect = RuntimeError("fallo OCR")
    processor = ImageProcessor(mock_engine)
    blocks = processor.process(small_image)
    assert any("Error al aplicar OCR" in b for b in blocks)


def test_extract_images_guarda_copia(mock_engine, small_image, tmp_path):
    from src.image_extractor import ImageExtractor

    extractor = MagicMock(spec=ImageExtractor)
    saved_path = tmp_path / "images" / "test_0001.png"
    extractor.save_image.return_value = saved_path

    processor = ImageProcessor(mock_engine, image_extractor=extractor, extract_images=True)
    blocks = processor.process(small_image)

    extractor.save_image.assert_called_once()
    assert any("images/" in b for b in blocks)


def test_sin_extract_images_no_llama_extractor(mock_engine, small_image, tmp_path):
    from src.image_extractor import ImageExtractor

    extractor = MagicMock(spec=ImageExtractor)
    processor = ImageProcessor(mock_engine, image_extractor=extractor, extract_images=False)
    processor.process(small_image)

    extractor.save_image.assert_not_called()
