from pathlib import Path

from tests.output import write_binary_output, write_text_output

OUTPUT_DIR = Path(__file__).parent / 'generated_output'
HTML_OUTPUT_DIR = OUTPUT_DIR / 'html'
PDF_OUTPUT_DIR = OUTPUT_DIR / 'pdf'
TYPST_OUTPUT_DIR = OUTPUT_DIR / 'typst'


def write_html_output(name: str, content: str) -> Path:
    return write_text_output(HTML_OUTPUT_DIR, name, 'html', content)


def write_pdf_output(name: str, content: bytes) -> Path:
    return write_binary_output(PDF_OUTPUT_DIR, name, 'pdf', content)


def write_typst_output(name: str, content: str) -> Path:
    return write_text_output(TYPST_OUTPUT_DIR, name, 'typ', content)
