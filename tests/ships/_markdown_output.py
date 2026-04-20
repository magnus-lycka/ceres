"""Helpers for writing generated regression artifacts from ship tests."""

from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / 'generated_output'
MARKDOWN_OUTPUT_DIR = OUTPUT_DIR / 'md'
HTML_OUTPUT_DIR = OUTPUT_DIR / 'html'
PDF_OUTPUT_DIR = OUTPUT_DIR / 'pdf'


def write_markdown_output(test_name: str, content: str) -> Path:
    MARKDOWN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = MARKDOWN_OUTPUT_DIR / f'{test_name}.md'
    output_path.write_text(content, encoding='utf-8')
    return output_path


def write_html_output(test_name: str, content: str) -> Path:
    HTML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = HTML_OUTPUT_DIR / f'{test_name}.html'
    output_path.write_text(content, encoding='utf-8')
    return output_path


def write_pdf_output(test_name: str, content: bytes) -> Path:
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PDF_OUTPUT_DIR / f'{test_name}.pdf'
    output_path.write_bytes(content)
    return output_path
