"""Helpers for writing generated regression artifacts from NPC tests."""

from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / 'generated_output'
PDF_OUTPUT_DIR = OUTPUT_DIR / 'pdf'
TYPST_OUTPUT_DIR = OUTPUT_DIR / 'typst'


def write_pdf_output(test_name: str, pdf_bytes: bytes) -> Path:
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PDF_OUTPUT_DIR / f'{test_name}.pdf'
    output_path.write_bytes(pdf_bytes)
    return output_path


def write_typst_output(test_name: str, typst_src: str) -> Path:
    TYPST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TYPST_OUTPUT_DIR / f'{test_name}.typ'
    output_path.write_text(typst_src, encoding='utf-8')
    return output_path
