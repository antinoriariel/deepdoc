"""Utilidades compartidas: logging, detección de tipos y helpers de rutas."""
import re
import sys
from pathlib import Path

from loguru import logger


def setup_logging(verbose: bool = False) -> None:
    """Configura loguru para consola y archivo."""
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | {message}",
        colorize=True,
    )
    logger.add(
        "extract.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )


def detect_file_type(path: Path) -> str:
    """Detecta el tipo de archivo por extensión; lanza ValueError si no es soportado."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in (".pptx", ".ppt"):
        return "pptx"
    raise ValueError(f"Tipo de archivo no soportado: {suffix!r}")


def sanitize_filename(name: str) -> str:
    """Elimina caracteres inválidos de un nombre de archivo."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip(". ")


def get_output_path(input_path: Path, output_dir: Path) -> Path:
    """Calcula la ruta del archivo Markdown de salida."""
    stem = sanitize_filename(input_path.stem)
    return output_dir / f"{stem}.md"


def collect_files(root: Path, recursive: bool = False) -> list[Path]:
    """Devuelve todos los PDF y PPTX dentro de un directorio."""
    glob = "**/*" if recursive else "*"
    files: list[Path] = []
    for ext in ("*.pdf", "*.pptx", "*.ppt"):
        pattern = f"**/{ext}" if recursive else ext
        files.extend(root.glob(pattern))
    return sorted(set(files))
