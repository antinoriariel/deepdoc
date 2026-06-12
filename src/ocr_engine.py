"""Patrón Strategy para motores OCR intercambiables."""
from abc import ABC, abstractmethod

from PIL import Image
from loguru import logger


class OCREngine(ABC):
    @abstractmethod
    def extract_text(self, image: Image.Image, lang: list[str]) -> str:
        """Extrae texto de una imagen PIL."""
        ...


class PaddleOCREngine(OCREngine):
    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except ImportError as exc:
            raise ImportError(f"PaddleOCR no está instalado: {exc}") from exc

    def extract_text(self, image: Image.Image, lang: list[str]) -> str:
        """Extrae texto con PaddleOCR."""
        import numpy as np

        img_array = np.array(image)
        result = self._ocr.ocr(img_array, cls=True)
        if not result or not result[0]:
            return ""
        lines: list[str] = []
        for line in result[0]:
            if line and len(line) >= 2:
                text, confidence = line[1]
                if confidence > 0.5:
                    lines.append(text)
        return "\n".join(lines)


class SuryaOCREngine(OCREngine):
    def __init__(self) -> None:
        try:
            from surya.ocr import run_ocr
            from surya.model.detection.model import load_model as load_det_model
            from surya.model.detection.processor import load_processor as load_det_processor
            from surya.model.recognition.model import load_model as load_rec_model
            from surya.model.recognition.processor import load_processor as load_rec_processor

            self._run_ocr = run_ocr
            self._det_model = load_det_model()
            self._det_processor = load_det_processor()
            self._rec_model = load_rec_model()
            self._rec_processor = load_rec_processor()
        except ImportError as exc:
            raise ImportError(f"surya-ocr no está instalado: {exc}") from exc

    def extract_text(self, image: Image.Image, lang: list[str]) -> str:
        """Extrae texto con Surya OCR."""
        predictions = self._run_ocr(
            [image],
            [lang],
            self._det_model,
            self._det_processor,
            self._rec_model,
            self._rec_processor,
        )
        if not predictions:
            return ""
        return "\n".join(line.text for line in predictions[0].text_lines)


class TesseractEngine(OCREngine):
    def __init__(self) -> None:
        try:
            import pytesseract
            self._pytesseract = pytesseract
        except ImportError as exc:
            raise ImportError(f"pytesseract no está instalado: {exc}") from exc

    def extract_text(self, image: Image.Image, lang: list[str]) -> str:
        """Extrae texto con Tesseract."""
        lang_str = "+".join(lang)
        return self._pytesseract.image_to_string(image, lang=lang_str)


_ENGINE_REGISTRY: dict[str, type[OCREngine]] = {
    "paddle": PaddleOCREngine,
    "surya": SuryaOCREngine,
    "tesseract": TesseractEngine,
}


def get_engine(name: str) -> OCREngine:
    """Instancia y retorna el motor OCR solicitado."""
    if name not in _ENGINE_REGISTRY:
        raise ValueError(
            f"Motor OCR no soportado: {name!r}. Opciones: {list(_ENGINE_REGISTRY)}"
        )
    return _ENGINE_REGISTRY[name]()
