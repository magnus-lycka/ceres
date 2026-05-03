"""Template execution engine for ceres reports.

Domain code provides a template path and a data structure of Python/Pydantic objects.
This module serialises the data and drives the template engine (Jinja2 or Typst).
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Any

import jinja2
from pydantic import BaseModel

__all__ = ['render_html', 'render_pdf', 'render_typst_source']

_TOOLKIT_TEMPLATES = Path(__file__).parent / 'templates'


# ---------------------------------------------------------------------------
# HTML rendering via Jinja2
# ---------------------------------------------------------------------------


def render_html(template_path: Path, context: dict[str, Any]) -> str:
    """Render a Jinja2 template with the given context.

    The template search path includes both the template's own directory and
    the toolkit's base templates directory, so templates can extend base.html.j2.

    CeresModel / Pydantic objects in context are passed as-is; Jinja2 accesses
    their attributes directly via dot notation.

    Custom filters available in templates: fmt_cost, fmt_mass.
    """
    loader = jinja2.FileSystemLoader(
        [str(template_path.parent), str(_TOOLKIT_TEMPLATES)],
        followlinks=True,
    )
    env = jinja2.Environment(
        loader=loader,
        autoescape=jinja2.select_autoescape(['html', 'j2']),
        undefined=jinja2.StrictUndefined,
    )
    env.filters['fmt_cost'] = _fmt_cost
    env.filters['fmt_mass'] = _fmt_mass

    template = env.get_template(template_path.name)
    return template.render(**context)


# ---------------------------------------------------------------------------
# Typst / PDF rendering
# ---------------------------------------------------------------------------


def render_typst_source(template_path: Path, data: dict[str, Any], *, page_size: str = 'a4') -> str:
    """Serialise data to a Typst preamble and prepend it to the template source.

    Returns the combined Typst source string (useful for debugging/inspection).
    The template receives the data via a top-level `report_data` variable.
    """
    preamble = f'#let report_data = {_to_typst(data)}\n\n'
    template_source = template_path.read_text(encoding='utf-8')
    return preamble + template_source


def render_pdf(template_path: Path, data: dict[str, Any], *, page_size: str = 'a4') -> bytes:
    """Serialise data, prepend to the Typst template, compile to PDF bytes.

    Toolkit base templates (e.g. base.typ) are copied into the temp dir so that
    `#import "base.typ": ...` in domain templates resolves correctly.
    """
    import shutil

    import typst

    source = render_typst_source(template_path, data, page_size=page_size)
    tmp_dir = tempfile.mkdtemp()
    try:
        for base_file in _TOOLKIT_TEMPLATES.glob('*.typ'):
            shutil.copy2(base_file, os.path.join(tmp_dir, base_file.name))
        typ_path = os.path.join(tmp_dir, 'main.typ')
        with open(typ_path, 'w', encoding='utf-8') as f:
            f.write(source)
        return typst.compile(typ_path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Typst serialiser
# ---------------------------------------------------------------------------


def _to_typst(obj: Any) -> str:
    """Recursively serialise a Python value to a Typst literal."""
    if obj is None:
        return 'none'
    if isinstance(obj, bool):
        return 'true' if obj else 'false'
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, float):
        return str(obj)
    if isinstance(obj, str):
        escaped = obj.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(obj, BaseModel):
        return _to_typst(obj.model_dump())
    if isinstance(obj, dict):
        pairs = ', '.join(f'{_typst_key(k)}: {_to_typst(v)}' for k, v in obj.items())
        return f'({pairs})'
    if isinstance(obj, (list, tuple)):
        if not obj:
            return '()'
        items = ', '.join(_to_typst(x) for x in obj)
        return f'({items},)'
    return f'"{obj}"'


def _typst_key(key: str) -> str:
    """Return a safe Typst dictionary key (quoted if it contains hyphens or spaces)."""
    if key.replace('_', '').replace('-', '').isalnum():
        return key
    return f'"{key}"'


# ---------------------------------------------------------------------------
# Shared formatting helpers (available as Jinja2 filters and to Typst callers)
# ---------------------------------------------------------------------------


def _fmt_cost(cost: float) -> str:
    if cost < 1:
        return f'Cr{cost:.2f}'
    return f'Cr{cost:,.0f}'


def _fmt_mass(mass: float) -> str:
    if mass <= 0:
        return '—'
    return f'{mass:g}'
