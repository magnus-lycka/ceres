from ceres.gear.catalog import render_computer_catalog_html, render_computer_catalog_pdf, render_computer_catalog_typst
from tests.gear._output import write_html_output, write_pdf_output, write_typst_output


def test_computer_catalog_html_output():
    html = render_computer_catalog_html(theme='light')
    write_html_output('computer_catalog', html)
    assert 'Portable Computer' in html
    assert 'Cr1,000' in html


def test_computer_catalog_html_dark():
    html = render_computer_catalog_html(theme='dark')
    write_html_output('computer_catalog_dark', html)
    assert 'Tablet' in html


def test_computer_catalog_typst_output():
    source = render_computer_catalog_typst()
    write_typst_output('computer_catalog', source)
    assert 'Portable Computer' in source
    assert 'Mid-Sized Computer' in source


# @pytest.mark.skip(reason='PDF generation requires typst font — run manually')
def test_computer_catalog_pdf_output():
    pdf = render_computer_catalog_pdf()
    write_pdf_output('computer_catalog', pdf)
    assert pdf[:4] == b'%PDF'
