"""Helpers for writing generated Markdown from ship regression tests."""

from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / 'generated_md'


def write_markdown_output(test_name: str, content: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f'{test_name}.md'
    output_path.write_text(content, encoding='utf-8')
    return output_path
