"""Detección y conversión de tablas a Markdown desde PDF."""
from pathlib import Path

from loguru import logger


def _rows_to_markdown(headers: list[str], rows: list[list[str]]) -> str:
    """Convierte encabezados y filas a una tabla Markdown."""
    if not headers and not rows:
        return ""
    col_count = max(len(headers), max((len(r) for r in rows), default=0))
    headers = (headers + [""] * col_count)[:col_count]
    lines = [
        "| " + " | ".join(str(h) for h in headers) + " |",
        "| " + " | ".join(["---"] * col_count) + " |",
    ]
    for row in rows:
        padded = (list(row) + [""] * col_count)[:col_count]
        lines.append("| " + " | ".join(str(c) for c in padded) + " |")
    return "\n".join(lines)


class TableDetector:
    def extract_from_pdf_page(self, pdf_path: Path, page_num: int) -> list[str]:
        """Extrae tablas de una página PDF; prueba Camelot y luego Tabula como fallback."""
        tables_md: list[str] = []

        # Intentar con Camelot (requiere Ghostscript para lattice)
        try:
            import camelot

            tables = camelot.read_pdf(str(pdf_path), pages=str(page_num + 1), flavor="lattice")
            for tbl in tables:
                df = tbl.df
                if df.empty:
                    continue
                headers = df.iloc[0].tolist()
                rows = df.iloc[1:].values.tolist()
                md = _rows_to_markdown(headers, rows)
                if md:
                    tables_md.append(md)
            if tables_md:
                return tables_md
        except Exception as exc:
            logger.debug(f"Camelot (página {page_num + 1}): {exc}")

        # Fallback con Tabula
        try:
            import tabula

            dfs = tabula.read_pdf(
                str(pdf_path), pages=page_num + 1, multiple_tables=True, silent=True
            )
            for df in dfs:
                if df is None or df.empty:
                    continue
                headers = [str(c) for c in df.columns.tolist()]
                rows = [[str(c) for c in row] for row in df.values.tolist()]
                md = _rows_to_markdown(headers, rows)
                if md:
                    tables_md.append(md)
        except Exception as exc:
            logger.debug(f"Tabula (página {page_num + 1}): {exc}")

        return tables_md
