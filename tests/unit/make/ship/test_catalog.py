import pytest

from ceres.make.ship.catalog import (
    render_ship_computer_catalog_html,
    render_ship_computer_catalog_pdf,
    render_ship_computer_catalog_typst,
)
from tests.unit.make.ship._output import write_html_output, write_pdf_output, write_typst_output


@pytest.fixture(scope='module')
def ship_computer_catalog_html():
    html = render_ship_computer_catalog_html(theme='light')
    write_html_output('ship_computer_catalog', html)
    return html


@pytest.fixture(scope='module')
def ship_computer_catalog_html_dark():
    html = render_ship_computer_catalog_html(theme='dark')
    write_html_output('ship_computer_catalog_dark', html)
    return html


@pytest.fixture(scope='module')
def ship_computer_catalog_typst():
    source = render_ship_computer_catalog_typst()
    write_typst_output('ship_computer_catalog', source)
    return source


@pytest.fixture(scope='module')
def ship_computer_catalog_pdf():
    pdf = render_ship_computer_catalog_pdf()
    write_pdf_output('ship_computer_catalog', pdf)
    return pdf


def test_ship_computer_catalog_html_output(ship_computer_catalog_html):
    html = ship_computer_catalog_html
    assert 'Computer' in html
    assert 'Core' in html
    assert 'MCr' in html


def test_ship_computer_catalog_html_dark(ship_computer_catalog_html_dark):
    html = ship_computer_catalog_html_dark
    assert 'Core' in html


def test_ship_computer_catalog_html_contains_all_processing_levels(ship_computer_catalog_html):
    html = ship_computer_catalog_html
    for processing in [5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100]:
        assert str(processing) in html


def test_ship_computer_catalog_html_shows_bis_and_fib_costs(ship_computer_catalog_html):
    html = ship_computer_catalog_html
    assert 'BIS' in html
    assert 'FIB' in html


def test_ship_computer_catalog_html_uses_kcr_below_mcr1(ship_computer_catalog_html):
    html = ship_computer_catalog_html
    assert 'kCr' in html  # Computer5 (Cr30,000) and Computer10 (Cr160,000) are below MCr1


def test_ship_computer_catalog_html_shows_retro_section(ship_computer_catalog_html):
    html = ship_computer_catalog_html
    assert 'Retro' in html


def test_ship_computer_catalog_html_shows_proto_section(ship_computer_catalog_html):
    html = ship_computer_catalog_html
    assert 'Proto' in html


def test_ship_computer_catalog_typst_output(ship_computer_catalog_typst):
    source = ship_computer_catalog_typst
    assert 'Computer' in source
    assert 'Core' in source
    assert 'MCr' in source


def test_ship_computer_catalog_pdf_output(ship_computer_catalog_pdf):
    pdf = ship_computer_catalog_pdf
    assert pdf[:4] == b'%PDF'
