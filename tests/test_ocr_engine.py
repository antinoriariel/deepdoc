"""Tests para el patrón Strategy de motores OCR."""
import pytest
from unittest.mock import patch
from PIL import Image

from src.ocr_engine import _ENGINE_REGISTRY, OCREngine, TesseractEngine, get_engine


def _blank_image() -> Image.Image:
    return Image.new("RGB", (100, 50), color=(255, 255, 255))


def test_ocr_engine_es_abc():
    """TesseractEngine debe implementar el ABC OCREngine."""
    assert issubclass(TesseractEngine, OCREngine)


def test_registry_expone_los_tres_motores():
    """El registro Strategy contiene exactamente los motores soportados."""
    assert set(_ENGINE_REGISTRY) == {"paddle", "surya", "tesseract"}


def test_get_engine_invalido_lanza_value_error():
    with pytest.raises(ValueError, match="no soportado"):
        get_engine("motor_inventado")


def test_tesseract_engine_extrae_texto():
    with patch("pytesseract.image_to_string", return_value="texto extraído") as mock_tess:
        engine = TesseractEngine()
        result = engine.extract_text(_blank_image(), ["es"])
        assert result == "texto extraído"
        mock_tess.assert_called_once()


def test_tesseract_mapea_iso639_1_a_codigos_tesseract():
    """'es,en' de la CLI debe traducirse a 'spa+eng' para Tesseract."""
    with patch("pytesseract.image_to_string", return_value="") as mock_tess:
        engine = TesseractEngine()
        engine.extract_text(_blank_image(), ["es", "en"])
        _, kwargs = mock_tess.call_args
        assert kwargs.get("lang") == "spa+eng"


def test_tesseract_acepta_codigos_639_3_directos():
    """Códigos ya en formato Tesseract (639-3) pasan sin modificarse."""
    with patch("pytesseract.image_to_string", return_value="") as mock_tess:
        engine = TesseractEngine()
        engine.extract_text(_blank_image(), ["spa", "jpn"])
        _, kwargs = mock_tess.call_args
        assert kwargs.get("lang") == "spa+jpn"


def test_engine_strategy_intercambiable():
    """Diferentes motores exponen la misma interfaz."""
    with patch("pytesseract.image_to_string", return_value="salida"):
        engine = get_engine("tesseract")
        result = engine.extract_text(_blank_image(), ["en"])
        assert isinstance(result, str)
