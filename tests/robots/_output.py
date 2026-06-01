"""Helpers for writing generated regression artifacts from robot tests."""

from pathlib import Path

from ceres.make.robot.robot import Robot
from tests.output import write_binary_output, write_json_model_output, write_text_output

OUTPUT_DIR = Path(__file__).parent / 'generated_output'
JSON_OUTPUT_DIR = OUTPUT_DIR / 'json'
PDF_OUTPUT_DIR = OUTPUT_DIR / 'pdf'
TYPST_OUTPUT_DIR = OUTPUT_DIR / 'typst'


def write_json_output(test_name: str, robot: Robot) -> Path:
    return write_json_model_output(JSON_OUTPUT_DIR, test_name, robot)


def write_pdf_output(test_name: str, pdf_bytes: bytes) -> Path:
    return write_binary_output(PDF_OUTPUT_DIR, test_name, 'pdf', pdf_bytes)


def write_typst_output(test_name: str, typst_src: str) -> Path:
    return write_text_output(TYPST_OUTPUT_DIR, test_name, 'typ', typst_src)
