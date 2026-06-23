"""Scan tests that prevent broad Any annotations in character-domain code.

These tests enforce the typing contract: character-domain APIs must not use
broad `Any` annotations for named parameters. The `web/` subdirectory is
excluded: it is Starlette-bound application glue that legitimately works with
FormData rather than plain Mapping.
"""

from pathlib import Path
import re

CHARACTER_SRC = Path(__file__).parent.parent.parent / 'src' / 'ceres' / 'character'

# Patterns that are legitimately `Any` and must not be flagged:
#   kwargs: Any      — **kwargs forwarding in subclass hooks (__init_subclass__ etc.)
#   cls: Any =       — local dynamic-dispatch escape (skill_cls, _cls, cls = ...)
#   data: Any, hand  — CareerData._from_registry: Pydantic model_validator(mode='wrap')
#                      input; dict-narrowing from `object` loses key typing in ty
_ALLOWED_PATTERNS: frozenset[str] = frozenset(
    {
        'kwargs: Any',
        'cls: Any = ',
        'data: Any, hand',
    }
)

_ANY_ANNOTATION = re.compile(r': Any(?:\W|$)')


def _scan_files() -> list[Path]:
    return [py_file for py_file in sorted(CHARACTER_SRC.rglob('*.py')) if 'web' not in py_file.parts]


def _find_pattern(pattern: str) -> list[str]:
    return [str(py_file.relative_to(CHARACTER_SRC)) for py_file in _scan_files() if pattern in py_file.read_text()]


def _find_any_annotations() -> list[tuple[str, int, str]]:
    hits = []
    for py_file in _scan_files():
        for lineno, line in enumerate(py_file.read_text().splitlines(), 1):
            if _ANY_ANNOTATION.search(line) and not any(p in line for p in _ALLOWED_PATTERNS):
                hits.append((str(py_file.relative_to(CHARACTER_SRC)), lineno, line.strip()))
    return hits


def test_no_broad_any_annotations():
    """No broad `: Any` annotations in character domain outside explicitly allowed patterns."""
    hits = _find_any_annotations()
    assert hits == [], f'{len(hits)} unexpected : Any annotation(s):\n' + '\n'.join(
        f'  {f}:{n}: {line}' for f, n, line in hits
    )


def test_no_broad_projection_any():
    """No `projection: Any` annotations in the character domain."""
    assert _find_pattern('projection: Any') == []


def test_no_broad_form_any():
    """No `form: Any` annotations in the character domain."""
    assert _find_pattern('form: Any') == []


def test_no_broad_fulfilled_pending_any():
    """No `fulfilled_pending: Any` annotations in the character domain."""
    assert _find_pattern('fulfilled_pending: Any') == []
