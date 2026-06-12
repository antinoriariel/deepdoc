"""Procesamiento de archivos de imagen (PNG, JPG, WEBP, etc.) con OCR."""
from pathlib import Path
from typing import Optional

from PIL import Image
from loguru import logger

from .image_extractor import ImageExtractor
from .ocr_engine import OCREngine


class ImageProcessor:
    def __init__(
        self,
        ocr_engine: OCREngine,
        image_extractor: Optional[ImageExtractor] = None,
        extract_images: bool = False,
        lang: Optional[list[str]] = None,
    ) -> None:
        self.ocr_engine = ocr_engine
        self.image_extractor = image_extractor
        self.extract_images = extract_images
        self.lang = lang or ["es", "en"]

    def process(self, image_path: Path) -> list[str]:
        """Carga la imagen, aplica OCR y retorna bloques de texto Markdown."""
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as exc:
            logger.error(f"Error abriendo imagen {image_path.name}: {exc}")
            return []

        blocks: list[str] = []

        try:
            text = self.ocr_engine.extract_text(image, self.lang)
            if text.strip():
                blocks.append(text)
            else:
                blocks.append(f"\n> ⚠️ OCR no produjo resultado para {image_path.name}.\n")
        except Exception as exc:
            logger.error(f"Error OCR en {image_path.name}: {exc}")
            blocks.append(f"\n> ⚠️ Error al aplicar OCR: {exc}\n")

        if self.extract_images and self.image_extractor:
            path = self.image_extractor.save_image(image)
            if path:
                blocks.append(f"\n![{image_path.stem}](images/{path.name})\n")

        return blocks
