import pytest

from ceres.character.report import render_stat_block_gallery_pdf, render_stat_block_gallery_typst
from tests.approval.character.e2e.test_kasimir_yuen import build_kasimir_yuen

from ._output import write_pdf_output, write_typst_output

pytestmark = pytest.mark.generated_output

_NPCS = sorted(
    [
        ('test_kasimir_yuen', build_kasimir_yuen),
    ],
    key=lambda entry: entry[1]().name.lower(),
)


def test_npc_gallery_typst_output() -> None:
    specs = [builder() for _name, builder in _NPCS]
    typst_src = render_stat_block_gallery_typst(specs)
    output_path = write_typst_output('npcs_gallery', typst_src)
    assert output_path.exists()
    assert 'report_data' in output_path.read_text(encoding='utf-8')


@pytest.mark.slow
def test_npc_gallery_pdf_output() -> None:
    specs = [builder() for _name, builder in _NPCS]
    typst_src = render_stat_block_gallery_typst(specs)
    write_typst_output('npcs_gallery', typst_src)
    pdf_bytes = render_stat_block_gallery_pdf(specs)
    output_path = write_pdf_output('npcs_gallery', pdf_bytes)

    assert output_path.exists()
    assert pdf_bytes[:4] == b'%PDF'
