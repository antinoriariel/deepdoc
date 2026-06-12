"""Procesamiento de archivos PDF con texto embebido y escaneados."""
import io
from pathlib import Path
from typing import Optional

from PIL import Image
from loguru import logger

from .ocr_engine import OCREngine
from .image_extractor import ImageExtractor
from .table_detector import TableDetector


class PDFProcessor:
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
        self.table_detector = TableDetector()

    def process(self, pdf_path: Path) -> list[str]:
        """Procesa el PDF y retorna bloques de texto ordenados."""
        try:
            import fitz

            doc = fitz.open(str(pdf_path))
            has_text = self._has_embedded_text(doc)
            doc.close()
        except Exception as exc:
            logger.error(f"Error abriendo {pdf_path.name}: {exc}")
            return []

        if has_text:
            logger.info(f"PDF con texto embebido: {pdf_path.name}")
            return self._process_text_pdf(pdf_path)

        logger.info(f"PDF escaneado detectado, usando OCR: {pdf_path.name}")
        return self._process_scanned_pdf(pdf_path)

    def get_page_count(self, pdf_path: Path) -> int:
        """Retorna el número de páginas del PDF."""
        try:
            import fitz

            doc = fitz.open(str(pdf_path))
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _has_embedded_text(self, doc) -> bool:
        """Verifica si las primeras páginas contienen texto embebido."""
        pages_to_check = min(3, len(doc))
        total = "".join(doc[i].get_text() for i in range(pages_to_check))
        return len(total.strip()) > 50

    def _process_text_pdf(self, pdf_path: Path) -> list[str]:
        """Extrae texto de un PDF con texto embebido usando PyMuPDF."""
        blocks: list[str] = []
        try:
            import fitz

            doc = fitz.open(str(pdf_path))
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks.append(f"\n## Página {page_num + 1}\n")
                blocks.extend(self._extract_page_blocks(page, page_num, pdf_path))

                if self.extract_images and self.image_extractor:
                    for img_ref in page.get_images(full=True):
                        xref = img_ref[0]
                        try:
                            base = doc.extract_image(xref)
                            img = Image.open(io.BytesIO(base["image"])).convert("RGB")
                            path = self.image_extractor.save_image(img)
                            if path:
                                blocks.append(f"\n![Figura](images/{path.name})\n")
                        except Exception as exc:
                            logger.debug(f"Imagen xref={xref} página {page_num + 1}: {exc}")
            doc.close()
        except Exception as exc:
            logger.error(f"Error procesando PDF con texto {pdf_path.name}: {exc}")
        return blocks

    def _extract_page_blocks(self, page, page_num: int, pdf_path: Path) -> list[str]:
        """Extrae bloques de texto de una página en orden de lectura."""
        result: list[str] = []
        try:
            raw = page.get_text("blocks")
            # Ordenar: fila (y0 redondeada a 20px) luego columna (x0)
            raw.sort(key=lambda b: (round(b[1] / 20) * 20, b[0]))
            for block in raw:
                if block[6] == 0:  # tipo texto
                    text = block[4].strip()
                    if text:
                        result.append(text)

            tables = self.table_detector.extract_from_pdf_page(pdf_path, page_num)
            result.extend(tables)
        except Exception as exc:
            logger.warning(f"Error en bloques de página {page_num + 1}: {exc}")
            result.append(f"\n> ⚠️ Página {page_num + 1}: error parcial al extraer bloques.\n")
        return result

    def _process_scanned_pdf(self, pdf_path: Path) -> list[str]:
        """Convierte páginas a imágenes con pdf2image y aplica OCR."""
        blocks: list[str] = []
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(str(pdf_path), dpi=300)
            for page_num, image in enumerate(images):
                blocks.append(f"\n## Página {page_num + 1}\n")
                try:
                    text = self.ocr_engine.extract_text(image, self.lang)
                    if text.strip():
                        blocks.append(text)
                    else:
                        blocks.append(f"\n> ⚠️ Página {page_num + 1}: OCR no produjo resultado.\n")
                    if self.extract_images and self.image_extractor:
                        path = self.image_extractor.save_image(image)
                        if path:
                            blocks.append(f"\n![Página {page_num + 1}](images/{path.name})\n")
                except Exception as exc:
                    logger.warning(f"Error OCR página {page_num + 1}: {exc}")
                    blocks.append(
                        f"\n> ⚠️ Página {page_num + 1}: no pudo procesarse (error OCR). Contenido omitido.\n"
                    )
        except Exception as exc:
            logger.error(f"Error convirtiendo PDF escaneado {pdf_path.name}: {exc}")
        return blocks
