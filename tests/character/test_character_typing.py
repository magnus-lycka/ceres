"""Scan tests that prevent broad Any annotations in character-domain code.

These tests enforce the typing contract from the todo: character-domain APIs
must not use broad `projection: Any`, `form: Any`, or `fulfilled_pending: Any`
annotations. Narrow types (CharacterProjection, Mapping[str, str],
PendingInputBase | None) must be used instead.

The `web/` subdirectory is excluded: it is Starlette-bound application glue
that legitimately works with FormData rather than plain Mapping.
"""

from pathlib import Path

CHARACTER_SRC = Path(__file__).parent.parent.parent / 'src' / 'ceres' / 'character'


def _find_pattern(pattern: str) -> list[str]:
    hits = []
    for py_file in sorted(CHARACTER_SRC.rglob('*.py')):
        if 'web' in py_file.parts:
            continue
        content = py_file.read_text()
        if pattern in content:
            hits.append(str(py_file.relative_to(CHARACTER_SRC)))
    return hits


def test_no_broad_projection_any():
    """No `projection: Any` annotations in the character domain."""
    assert _find_pattern('projection: Any') == []


def test_no_broad_form_any():
    """No `form: Any` annotations in the character domain."""
    assert _find_pattern('form: Any') == []


def test_no_broad_fulfilled_pending_any():
    """No `fulfilled_pending: Any` annotations in the character domain."""
    assert _find_pattern('fulfilled_pending: Any') == []
