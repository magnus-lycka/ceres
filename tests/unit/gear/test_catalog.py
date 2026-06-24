import pytest

from ceres.gear.catalog import (
    render_communication_catalog_html,
    render_communication_catalog_pdf,
    render_communication_catalog_typst,
    render_computer_catalog_html,
    render_computer_catalog_pdf,
    render_computer_catalog_typst,
    render_gear_catalog_html,
    render_gear_catalog_typst,
)
from tests.unit.gear._output import write_html_output, write_pdf_output, write_typst_output


@pytest.fixture(scope='module')
def computer_catalog_html():
    html = render_computer_catalog_html(theme='light')
    write_html_output('computer_catalog', html)
    return html


@pytest.fixture(scope='module')
def computer_catalog_html_dark():
    html = render_computer_catalog_html(theme='dark')
    write_html_output('computer_catalog_dark', html)
    return html


@pytest.fixture(scope='module')
def computer_catalog_typst():
    source = render_computer_catalog_typst()
    write_typst_output('computer_catalog', source)
    return source


@pytest.fixture(scope='module')
def computer_catalog_pdf():
    pdf = render_computer_catalog_pdf()
    write_pdf_output('computer_catalog', pdf)
    return pdf


@pytest.fixture(scope='module')
def communication_catalog_html():
    html = render_communication_catalog_html(theme='light')
    write_html_output('communication_catalog', html)
    return html


@pytest.fixture(scope='module')
def communication_catalog_typst():
    source = render_communication_catalog_typst()
    write_typst_output('communication_catalog', source)
    return source


@pytest.fixture(scope='module')
def communication_catalog_pdf():
    pdf = render_communication_catalog_pdf()
    write_pdf_output('communication_catalog', pdf)
    return pdf


@pytest.fixture(scope='module')
def gear_catalog_html():
    html = render_gear_catalog_html(theme='light')
    write_html_output('gear_catalog', html)
    return html


@pytest.fixture(scope='module')
def gear_catalog_typst():
    source = render_gear_catalog_typst()
    write_typst_output('gear_catalog', source)
    return source


def test_computer_catalog_html_output(computer_catalog_html):
    html = computer_catalog_html
    assert 'Portable Computer' in html
    assert 'Cr1,000' in html


def test_computer_catalog_html_dark(computer_catalog_html_dark):
    html = computer_catalog_html_dark
    assert 'Tablet' in html


def test_computer_catalog_typst_output(computer_catalog_typst):
    source = computer_catalog_typst
    assert 'Portable Computer' in source
    assert 'Mid-Sized Computer' in source
    assert 'Portable Computer Options' in source
    assert 'Data Display/Recorder' in source


# @pytest.mark.skip(reason='PDF generation requires typst font — run manually')
def test_computer_catalog_pdf_output(computer_catalog_pdf):
    pdf = computer_catalog_pdf
    assert pdf[:4] == b'%PDF'


def test_communication_catalog_html_output(communication_catalog_html):
    html = communication_catalog_html
    assert 'Communication Equipment' in html
    assert 'Laser Transceiver' in html
    assert 'Meson Transceiver' in html
    assert 'Radio Transceiver' in html
    assert 'Transceiver Options' in html
    assert 'Satellite Uplink' in html
    assert '500,000km' in html


def test_communication_catalog_typst_output(communication_catalog_typst):
    source = communication_catalog_typst
    assert 'Communication Equipment' in source
    assert 'Laser Transceiver' in source
    assert 'Meson Transceiver' in source
    assert 'Radio Transceiver' in source
    assert 'Transceiver Options' in source
    assert 'Hardware Encryption Module' in source
    assert 'Computer/0' in source


def test_communication_catalog_pdf_output(communication_catalog_pdf):
    pdf = communication_catalog_pdf
    assert pdf[:4] == b'%PDF'


def test_gear_catalog_html_includes_radio_transceivers(gear_catalog_html):
    html = gear_catalog_html
    assert 'Laser Transceiver' in html
    assert 'Meson Transceiver' in html
    assert 'Radio Transceiver' in html
    assert '500,000km' in html
    assert 'Computer/0' in html


def test_gear_catalog_typst_includes_radio_transceivers(gear_catalog_typst):
    source = gear_catalog_typst
    assert 'Laser Transceiver' in source
    assert 'Meson Transceiver' in source
    assert 'Radio Transceiver' in source
    assert 'Computer/0' in source
