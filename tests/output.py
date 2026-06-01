from pathlib import Path
from typing import Protocol


class JsonDumpable(Protocol):
    def model_dump_json(self, *, indent: int | None = None) -> str: ...


def write_text_output(output_dir: Path, name: str, suffix: str, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f'{name}.{suffix}'
    path.write_text(content, encoding='utf-8')
    return path


def write_binary_output(output_dir: Path, name: str, suffix: str, content: bytes) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f'{name}.{suffix}'
    path.write_bytes(content)
    return path


def write_json_model_output(output_dir: Path, name: str, model: JsonDumpable) -> Path:
    return write_text_output(output_dir, name, 'json', model.model_dump_json(indent=2))
