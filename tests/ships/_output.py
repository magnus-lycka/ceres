"""Helpers for writing generated regression artifacts from ship tests."""

from pathlib import Path

from ceres.make.ship.ship import Ship
from tests.output import write_binary_output, write_json_model_output, write_text_output

OUTPUT_DIR = Path(__file__).parent / 'generated_output'
HTML_OUTPUT_DIR = OUTPUT_DIR / 'html'
PDF_OUTPUT_DIR = OUTPUT_DIR / 'pdf'
TYPST_OUTPUT_DIR = OUTPUT_DIR / 'typst'
JSON_OUTPUT_DIR = OUTPUT_DIR / 'json'


def write_html_output(test_name: str, content: str) -> Path:
    return write_text_output(HTML_OUTPUT_DIR, test_name, 'html', content)


def write_pdf_output(test_name: str, content: bytes) -> Path:
    return write_binary_output(PDF_OUTPUT_DIR, test_name, 'pdf', content)


def write_typst_output(test_name: str, content: str) -> Path:
    return write_text_output(TYPST_OUTPUT_DIR, test_name, 'typ', content)


def write_json_output(test_name: str, ship: Ship) -> Path:
    return write_json_model_output(JSON_OUTPUT_DIR, test_name, ship)
