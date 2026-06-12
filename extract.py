"""DeepDoc — CLI para convertir PDF y PPTX a Markdown con OCR avanzado.

Pipeline híbrido: MarkItDown como intento rápido y, si el resultado es
insuficiente, extracción nativa (PyMuPDF / python-pptx) con OCR de respaldo.
El motor OCR se inicializa de forma diferida: si MarkItDown alcanza, nunca
se paga el costo de cargar modelos de reconocimiento.
"""
import concurrent.futures
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    help="DeepDoc: convierte PDF y PPTX a Markdown mediante MarkItDown + OCR avanzado.",
    add_completion=False,
)
console = Console()


def _process_file(
    input_path: Path,
    output_dir: Path,
    lang: list[str],
    ocr_name: str,
    extract_images: bool,
    use_markitdown: bool,
) -> dict:
    """Procesa un único archivo y retorna métricas del resultado."""
    from loguru import logger

    from src.image_extractor import ImageExtractor
    from src.markdown_formatter import MarkdownFormatter
    from src.markitdown_processor import MarkItDownProcessor
    from src.ocr_engine import get_engine
    from src.pdf_processor import PDFProcessor
    from src.pptx_processor import PPTXProcessor
    from src.utils import (
        count_pdf_pages,
        count_pptx_slides,
        detect_file_type,
        get_output_path,
        sanitize_filename,
    )

    result: dict = {
        "file": input_path.name,
        "engine": "none",
        "pages": 0,
        "status": "ok",
        "output": None,
    }

    try:
        output_path = get_output_path(input_path, output_dir)
        file_type = detect_file_type(input_path)
        formatter = MarkdownFormatter()
        img_prefix = sanitize_filename(input_path.stem)
        markitdown_used = False
        blocks: list[str] = []

        # Etapa 1 — intento rápido con MarkItDown, sin tocar los motores OCR.
        if use_markitdown:
            try:
                quick = MarkItDownProcessor().convert(input_path)
            except ImportError as exc:
                logger.warning(f"MarkItDown no disponible ({exc}); se usa el pipeline OCR")
                quick = None
            if quick:
                markitdown_used = True
                result["engine"] = "markitdown"
                blocks = [quick]

        # Etapa 2 — pipeline completo; el motor OCR se construye solo aquí.
        if not blocks:
            ocr_engine = get_engine(ocr_name)
            image_extractor = (
                ImageExtractor(output_dir, prefix=img_prefix) if extract_images else None
            )
            if file_type == "pdf":
                proc = PDFProcessor(ocr_engine, image_extractor, extract_images, lang)
            else:
                proc = PPTXProcessor(ocr_engine, image_extractor, extract_images, lang)
            blocks = proc.process(input_path)
            result["engine"] = ocr_name

        result["pages"] = (
            count_pdf_pages(input_path) if file_type == "pdf" else count_pptx_slides(input_path)
        )

        # MarkItDown no referencia imágenes embebidas: extraerlas aparte si se pidieron.
        if markitdown_used and extract_images:
            extractor = ImageExtractor(output_dir, prefix=img_prefix)
            if file_type == "pdf":
                image_paths = extractor.extract_from_pdf(input_path)
            else:
                image_paths = [p for _, p in extractor.extract_from_pptx(input_path)]
            if image_paths:
                refs = "\n".join(
                    f"![Figura {i}](images/{p.name})"
                    for i, p in enumerate(image_paths, start=1)
                )
                blocks.append(f"\n## Imágenes extraídas\n\n{refs}\n")

        markdown = formatter.format(
            blocks,
            source=input_path,
            pages=result["pages"],
            ocr_engine=result["engine"],
            markitdown_used=markitdown_used,
            languages=lang,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        result["output"] = str(output_path)
        logger.info(f"✓ {input_path.name} → {output_path.name}")

    except Exception as exc:
        logger.error(f"Error procesando {input_path.name}: {exc}")
        result["status"] = f"error: {exc}"

    return result


@app.command()
def main(
    input_path: Path = typer.Argument(..., help="Archivo PDF, PPTX o carpeta a procesar"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Carpeta de salida (default: output/)"),
    lang: str = typer.Option("es,en", "--lang", "-l", help="Idiomas OCR separados por coma (ISO 639-1)"),
    ocr: str = typer.Option("tesseract", "--ocr", help="Motor OCR: paddle | surya | tesseract"),
    extract_images: bool = typer.Option(False, "--extract-images", help="Extraer imágenes embebidas"),
    workers: int = typer.Option(4, "--workers", "-w", help="Hilos paralelos para batch"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Output detallado"),
    no_markitdown: bool = typer.Option(False, "--no-markitdown", help="Saltar MarkItDown; ir directo a OCR"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Buscar en subcarpetas"),
) -> None:
    """DeepDoc: convierte PDF y PPTX a Markdown con OCR avanzado."""
    from src.utils import collect_files, setup_logging

    setup_logging(verbose)

    lang_list = [item.strip() for item in lang.split(",") if item.strip()]
    use_markitdown = not no_markitdown

    if input_path.is_dir():
        files = collect_files(input_path, recursive)
    elif input_path.is_file():
        files = [input_path]
    else:
        console.print(f"[red]Error:[/red] {input_path} no existe.")
        raise typer.Exit(1)

    if not files:
        console.print("[yellow]No se encontraron archivos PDF o PPTX.[/yellow]")
        raise typer.Exit(0)

    output_dir = output if output else Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"Procesando {len(files)} archivo(s)...", total=len(files))

        if len(files) == 1 or workers == 1:
            for f in files:
                progress.update(task_id, description=f"Procesando [cyan]{f.name}[/cyan]...")
                results.append(
                    _process_file(f, output_dir, lang_list, ocr, extract_images, use_markitdown)
                )
                progress.advance(task_id)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_map = {
                    executor.submit(
                        _process_file, f, output_dir, lang_list, ocr,
                        extract_images, use_markitdown,
                    ): f
                    for f in files
                }
                for future in concurrent.futures.as_completed(future_map):
                    f = future_map[future]
                    try:
                        res = future.result()
                    except Exception as exc:
                        res = {
                            "file": f.name,
                            "engine": ocr,
                            "pages": 0,
                            "status": f"error: {exc}",
                            "output": None,
                        }
                    results.append(res)
                    progress.update(task_id, description=f"Listo: [cyan]{f.name}[/cyan]")
                    progress.advance(task_id)

    _print_summary(results)


def _print_summary(results: list[dict]) -> None:
    """Imprime la tabla resumen de la corrida."""
    table = Table(title="[bold]DeepDoc — Resultado[/bold]")
    table.add_column("Archivo", style="cyan", no_wrap=True)
    table.add_column("Páginas", justify="right", style="blue")
    table.add_column("Motor", style="magenta")
    table.add_column("Estado")
    table.add_column("Salida", style="dim")

    for r in results:
        status = (
            f"[green]{r['status']}[/green]"
            if r["status"] == "ok"
            else f"[red]{r['status']}[/red]"
        )
        table.add_row(r["file"], str(r["pages"]), r["engine"], status, r.get("output") or "—")

    console.print()
    console.print(table)


if __name__ == "__main__":
    app()
