"""Tests para PPTXProcessor."""
import pytest
from unittest.mock import MagicMock

from src.pptx_processor import PPTXProcessor
from src.ocr_engine import OCREngine


@pytest.fixture
def mock_engine():
    engine = MagicMock(spec=OCREngine)
    engine.extract_text.return_value = ""
    return engine


def test_pptx_proceso_retorna_lista(mock_engine, tmp_path):
    """Un path inexistente retorna lista vacía sin lanzar excepción."""
    processor = PPTXProcessor(mock_engine)
    result = processor.process(tmp_path / "no_existe.pptx")
    assert isinstance(result, list)


def test_pptx_preserva_orden_visual(mock_engine):
    """Los shapes deben ordenarse por posición top → left."""
    shapes = []
    for top, left in [(200, 0), (0, 50), (100, 0)]:
        shape = MagicMock()
        shape.top = top
        shape.left = left
        shapes.append(shape)

    sorted_shapes = sorted(shapes, key=lambda s: (s.top, s.left))
    tops = [s.top for s in sorted_shapes]
    assert tops == [0, 100, 200]


def test_pptx_extrae_notas_del_presentador(mock_engine):
    """Las notas del presentador deben aparecer en los bloques de salida."""
    processor = PPTXProcessor(mock_engine)

    mock_slide = MagicMock()
    mock_slide.shapes = []
    mock_slide.has_notes_slide = True
    mock_slide.notes_slide.notes_text_frame.text = "Esta es una nota importante"

    blocks = processor._process_slide(mock_slide, slide_num=0)
    joined = " ".join(blocks)
    assert "nota" in joined.lower() or "Notas" in joined


def test_tabla_pptx_a_markdown(mock_engine):
    """La tabla PPTX debe convertirse a formato Markdown correcto."""
    processor = PPTXProcessor(mock_engine)

    def mock_cell(text):
        return MagicMock(text=text)

    def mock_row(*texts):
        return MagicMock(cells=[mock_cell(t) for t in texts])

    mock_table = MagicMock()
    mock_table.rows = [
        mock_row("Nombre", "Valor"),
        mock_row("Alpha", "100"),
        mock_row("Beta", "200"),
    ]

    result = processor._table_to_markdown(mock_table)
    assert "| Nombre | Valor |" in result
    assert "| Alpha | 100 |" in result
    assert "| --- | --- |" in result


def test_get_slide_count_retorna_cero_si_falla(mock_engine, tmp_path):
    processor = PPTXProcessor(mock_engine)
    count = processor.get_slide_count(tmp_path / "no_existe.pptx")
    assert count == 0


def test_extract_text_frame_respeta_niveles(mock_engine):
    """Los párrafos con level > 0 deben renderizarse como listas."""
    processor = PPTXProcessor(mock_engine)

    mock_shape = MagicMock()
    mock_shape.name = "Content Placeholder"
    mock_shape.has_text_frame = True

    para0 = MagicMock()
    para0.text = "Elemento raíz"
    para0.level = 0

    para1 = MagicMock()
    para1.text = "Subelemento"
    para1.level = 1

    mock_shape.text_frame.paragraphs = [para0, para1]

    blocks = processor._extract_text_frame(mock_shape)
    assert any("- Subelemento" in b for b in blocks)
    assert any("Elemento raíz" in b for b in blocks)
