"""Tests para el patrón Strategy de motores OCR."""
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image

from src.ocr_engine import OCREngine, TesseractEngine, get_engine


def _blank_image() -> Image.Image:
    return Image.new("RGB", (100, 50), color=(255, 255, 255))


def test_ocr_engine_es_abc():
    """TesseractEngine debe implementar el ABC OCREngine."""
    assert issubclass(TesseractEngine, OCREngine)


def test_get_engine_invalido_lanza_value_error():
    with pytest.raises(ValueError, match="no soportado"):
        get_engine("motor_inventado")


def test_tesseract_engine_extrae_texto():
    with patch("pytesseract.image_to_string", return_value="texto extraído") as mock_tess:
        engine = TesseractEngine()
        result = engine.extract_text(_blank_image(), ["es"])
        assert result == "texto extraído"
        mock_tess.assert_called_once()


def test_tesseract_engine_concatena_idiomas():
    with patch("pytesseract.image_to_string", return_value="") as mock_tess:
        engine = TesseractEngine()
        engine.extract_text(_blank_image(), ["es", "en"])
        _, kwargs = mock_tess.call_args
        assert kwargs.get("lang") == "es+en"


def test_engine_strategy_intercambiable():
    """Diferentes motores exponen la misma interfaz."""
    with patch("pytesseract.image_to_string", return_value="salida"):
        engine = get_engine("tesseract")
        assert callable(getattr(engine, "extract_text", None))
        result = engine.extract_text(_blank_image(), ["en"])
        assert isinstance(result, str)


def test_paddle_engine_falla_sin_paddleocr():
    with patch.dict("sys.modules", {"paddleocr": None}):
        from importlib import reload
        import src.ocr_engine as ocr_module
        with pytest.raises((ImportError, Exception)):
            from src.ocr_engine import PaddleOCREngine
            PaddleOCREngine()


def test_surya_engine_falla_sin_surya():
    with pytest.raises((ImportError, Exception)):
        # Surya no está instalado en el entorno de test típico
        from src.ocr_engine import SuryaOCREngine
        SuryaOCREngine()
