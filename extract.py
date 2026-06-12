"""DeepDoc — CLI para convertir PDF y PPTX a Markdown con OCR avanzado."""
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
    verbose: bool,
    use_markitdown: bool,
) -> dict:
    """Procesa un único archivo y retorna un dict con métricas."""
    from loguru import logger

    from src.image_extractor import ImageExtractor
    from src.markdown_formatter import MarkdownFormatter
    from src.markitdown_processor import MarkItDownProcessor
    from src.ocr_engine import get_engine
    from src.pdf_processor import PDFProcessor
    from src.pptx_processor import PPTXProcessor
    from src.utils import detect_file_type, get_output_path

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
        image_extractor = ImageExtractor(output_dir) if extract_images else None
        ocr_engine = get_engine(ocr_name)
        formatter = MarkdownFormatter()
        markitdown_used = False
        blocks: list[str] = []

        # Pipeline rápido: MarkItDown
        if use_markitdown:
            md_proc = MarkItDownProcessor()
            quick = md_proc.convert(input_path)
            if quick:
                markitdown_used = True
                result["engine"] = "markitdown"
                blocks = [quick]

        # Fallback: pipeline OCR
        if not blocks:
            if file_type == "pdf":
                proc = PDFProcessor(ocr_engine, image_extractor, extract_images, lang)
                blocks = proc.process(input_path)
                result["pages"] = proc.get_page_count(input_path)
                result["engine"] = ocr_name
            elif file_type == "pptx":
                proc = PPTXProcessor(ocr_engine, image_extractor, extract_images, lang)
                blocks = proc.process(input_path)
                result["pages"] = proc.get_slide_count(input_path)
                result["engine"] = ocr_name

        # Conteo de páginas cuando MarkItDown fue suficiente
        if markitdown_used:
            if file_type == "pdf":
                try:
                    import fitz

                    doc = fitz.open(str(input_path))
                    result["pages"] = len(doc)
                    doc.close()
                except Exception:
                    pass
            elif file_type == "pptx":
                try:
                    from pptx import Presentation

                    result["pages"] = len(Presentation(str(input_path)).slides)
                except Exception:
                    pass

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
        from loguru import logger as _log

        _log.error(f"Error procesando {input_path.name}: {exc}")
        result["status"] = f"error: {exc}"

    return result


@app.command()
def main(
    input_path: Path = typer.Argument(..., help="Archivo PDF, PPTX o carpeta a procesar"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Carpeta de salida (default: output/)"),
    lang: str = typer.Option("es,en", "--lang", "-l", help="Idiomas OCR separados por coma"),
    ocr: str = typer.Option("tesseract", "--ocr", help="Motor OCR: paddle | surya | tesseract"),
    extract_images: bool = typer.Option(False, "--extract-images", is_flag=True, help="Extraer imágenes embebidas"),
    workers: int = typer.Option(4, "--workers", "-w", help="Hilos paralelos para batch"),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Output detallado"),
    no_markitdown: bool = typer.Option(False, "--no-markitdown", is_flag=True, help="Saltar MarkItDown; ir directo a OCR"),
    recursive: bool = typer.Option(False, "--recursive", "-r", is_flag=True, help="Buscar en subcarpetas"),
) -> None:
    """DeepDoc: convierte PDF y PPTX a Markdown con OCR avanzado."""
    from src.utils import setup_logging

    setup_logging(verbose)

    lang_list = [l.strip() for l in lang.split(",") if l.strip()]
    use_markitdown = not no_markitdown

    # Recopilar archivos
    files: list[Path] = []
    if input_path.is_dir():
        for ext in ("*.pdf", "*.pptx", "*.ppt"):
            pattern = f"**/{ext}" if recursive else ext
            files.extend(input_path.glob(pattern))
        files = sorted(set(files))
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
                res = _process_file(f, output_dir, lang_list, ocr, extract_images, verbose, use_markitdown)
                results.append(res)
                progress.advance(task_id)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_map = {
                    executor.submit(
                        _process_file, f, output_dir, lang_list, ocr, extract_images, verbose, use_markitdown
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

    # Tabla resumen
    table = Table(title="[bold]DeepDoc — Resultado[/bold]")
    table.add_column("Archivo", style="cyan", no_wrap=True)
    table.add_column("Páginas", justify="right", style="blue")
    table.add_column("Motor", style="magenta")
    table.add_column("Estado")
    table.add_column("Salida", style="dim")

    for r in results:
        status = f"[green]{r['status']}[/green]" if r["status"] == "ok" else f"[red]{r['status']}[/red]"
        table.add_row(r["file"], str(r["pages"]), r["engine"], status, r.get("output") or "—")

    console.print()
    console.print(table)


if __name__ == "__main__":
    app()
