from pathlib import Path

from ceres.report.html import copy_static_assets

OUTPUT_DIR = Path(__file__).parent / 'generated_output'
HTML_OUTPUT_DIR = OUTPUT_DIR / 'html'
PDF_OUTPUT_DIR = OUTPUT_DIR / 'pdf'
TYPST_OUTPUT_DIR = OUTPUT_DIR / 'typst'


def write_html_output(name: str, content: str) -> Path:
    HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_static_assets(HTML_OUTPUT_DIR)
    path = HTML_OUTPUT_DIR / f'{name}.html'
    path.write_text(content, encoding='utf-8')
    return path


def write_pdf_output(name: str, content: bytes) -> Path:
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = PDF_OUTPUT_DIR / f'{name}.pdf'
    path.write_bytes(content)
    return path


def write_typst_output(name: str, content: str) -> Path:
    TYPST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = TYPST_OUTPUT_DIR / f'{name}.typ'
    path.write_text(content, encoding='utf-8')
    return path
