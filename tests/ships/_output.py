"""Helpers for writing generated regression artifacts from ship tests."""

from pathlib import Path

from stuart import copy_static_assets

OUTPUT_DIR = Path(__file__).parent / 'generated_output'
HTML_OUTPUT_DIR = OUTPUT_DIR / 'html'
PDF_OUTPUT_DIR = OUTPUT_DIR / 'pdf'
TYPST_OUTPUT_DIR = OUTPUT_DIR / 'typst'


def write_html_output(test_name: str, content: str) -> Path:
    HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_static_assets(HTML_OUTPUT_DIR)
    output_path = HTML_OUTPUT_DIR / f'{test_name}.html'
    output_path.write_text(content, encoding='utf-8')
    return output_path


def write_pdf_output(test_name: str, content: bytes) -> Path:
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PDF_OUTPUT_DIR / f'{test_name}.pdf'
    output_path.write_bytes(content)
    return output_path


def write_typst_output(test_name: str, content: str) -> Path:
    TYPST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TYPST_OUTPUT_DIR / f'{test_name}.typ'
    output_path.write_text(content, encoding='utf-8')
    return output_path
