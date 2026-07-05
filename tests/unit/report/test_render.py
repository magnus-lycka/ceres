"""Tests for the ceres.report template execution engine.

Uses plain Python dicts — no domain objects — to test the engine in isolation.
"""

from pathlib import Path

import jinja2
import pytest

from ceres.report.render import (
    _fmt_cost,
    _fmt_mass,
    _to_typst,
    render_html,
    render_pdf,
    render_pdf_source,
    render_typst_source,
)

# ---------------------------------------------------------------------------
# _to_typst serialiser
# ---------------------------------------------------------------------------


def test_to_typst_none():
    assert _to_typst(None) == 'none'


def test_to_typst_bool():
    assert _to_typst(True) == 'true'
    assert _to_typst(False) == 'false'


def test_to_typst_int():
    assert _to_typst(42) == '42'


def test_to_typst_float():
    assert _to_typst(3.14) == '3.14'


def test_to_typst_string_plain():
    assert _to_typst('hello') == '"hello"'


def test_to_typst_string_escapes_quotes():
    assert _to_typst('say "hi"') == '"say \\"hi\\""'


def test_to_typst_list():
    result = _to_typst([1, 2, 3])
    assert result == '(1, 2, 3,)'


def test_to_typst_empty_list():
    assert _to_typst([]) == '()'


def test_to_typst_empty_tuple():
    assert _to_typst(()) == '()'


def test_to_typst_tuple():
    assert _to_typst((1, 'x')) == '(1, "x",)'


def test_to_typst_dict():
    result = _to_typst({'a': 1, 'b': 'x'})
    assert result == '(a: 1, b: "x")'


def test_to_typst_quotes_keys_with_spaces():
    assert _to_typst({'display name': 'Scout Courier'}) == '("display name": "Scout Courier")'


def test_to_typst_nested():
    result = _to_typst({'items': [{'v': 1}, {'v': 2}]})
    assert result == '(items: ((v: 1), (v: 2),))'


def test_to_typst_pydantic_model():
    from pydantic import BaseModel

    class M(BaseModel):
        x: int
        y: str

    assert _to_typst(M(x=5, y='hi')) == '(x: 5, y: "hi")'


def test_to_typst_fallback_uses_string_representation():
    assert _to_typst(Path('reports/out.pdf')) == '"reports/out.pdf"'


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def test_fmt_cost_large():
    assert _fmt_cost(1234.0) == 'Cr1,234'


def test_fmt_cost_small():
    assert _fmt_cost(0.5) == 'Cr0.50'


def test_fmt_mass_positive():
    assert _fmt_mass(2.5) == '2.5'


def test_fmt_mass_zero():
    assert _fmt_mass(0.0) == '—'


# ---------------------------------------------------------------------------
# render_html — uses a minimal inline template (no domain objects)
# ---------------------------------------------------------------------------


def test_render_html_extends_base(tmp_path: Path):
    tmpl = tmp_path / 'test.html.j2'
    tmpl.write_text(
        '{% extends "base.html.j2" %}{% block content %}<p>{{ greeting }}</p>{% endblock %}',
        encoding='utf-8',
    )
    html = render_html(tmpl, {'title': 'Test', 'greeting': 'Hello world'})
    assert '<p>Hello world</p>' in html
    assert '<title>Test</title>' in html
    assert 'class="theme-light"' in html


def test_render_html_dark_theme(tmp_path: Path):
    tmpl = tmp_path / 'test.html.j2'
    tmpl.write_text(
        '{% extends "base.html.j2" %}{% block content %}x{% endblock %}',
        encoding='utf-8',
    )
    html = render_html(tmpl, {'title': 'T', 'theme': 'dark'})
    assert 'class="theme-dark"' in html


def test_render_html_fmt_cost_filter(tmp_path: Path):
    tmpl = tmp_path / 'test.html.j2'
    tmpl.write_text(
        '{% extends "base.html.j2" %}{% block content %}{{ cost | fmt_cost }}{% endblock %}',
        encoding='utf-8',
    )
    html = render_html(tmpl, {'title': 'T', 'cost': 1500.0})
    assert 'Cr1,500' in html


def test_render_html_autoescape(tmp_path: Path):
    tmpl = tmp_path / 'test.html.j2'
    tmpl.write_text(
        '{% extends "base.html.j2" %}{% block content %}{{ name }}{% endblock %}',
        encoding='utf-8',
    )
    html = render_html(tmpl, {'title': 'T', 'name': '<script>alert(1)</script>'})
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html


def test_render_html_strict_undefined_raises(tmp_path: Path):
    tmpl = tmp_path / 'test.html.j2'
    tmpl.write_text(
        '{% extends "base.html.j2" %}{% block content %}{{ missing_var }}{% endblock %}',
        encoding='utf-8',
    )
    with pytest.raises(jinja2.UndefinedError):
        render_html(tmpl, {'title': 'T'})


# ---------------------------------------------------------------------------
# render_typst_source
# ---------------------------------------------------------------------------


def test_render_typst_source_prepends_data(tmp_path: Path):
    tmpl = tmp_path / 'test.typ'
    tmpl.write_text('// template body\n#report_data.title', encoding='utf-8')
    source = render_typst_source(tmpl, {'title': 'My Report'})
    assert source.startswith('#let report_data =')
    assert '"My Report"' in source
    assert '// template body' in source


def test_render_typst_source_data_before_template(tmp_path: Path):
    tmpl = tmp_path / 'test.typ'
    tmpl.write_text('TEMPLATE', encoding='utf-8')
    source = render_typst_source(tmpl, {'x': 1})
    preamble_end = source.index('\n\n')
    assert 'report_data' in source[:preamble_end]
    assert 'TEMPLATE' in source[preamble_end:]


def test_render_pdf_writes_combined_source_and_cleans_temp_dir(tmp_path: Path, monkeypatch):
    tmpl = tmp_path / 'test.typ'
    tmpl.write_text('#report_data.title', encoding='utf-8')
    compiled_paths: list[Path] = []

    def fake_compile(path: str) -> bytes:
        typ_path = Path(path)
        compiled_paths.append(typ_path)
        source = typ_path.read_text(encoding='utf-8')
        assert '"My Report"' in source
        assert '#report_data.title' in source
        return b'%PDF'

    monkeypatch.setattr('ceres.report.render.typst.compile', fake_compile)

    assert render_pdf(tmpl, {'title': 'My Report'}) == b'%PDF'
    assert compiled_paths
    assert not compiled_paths[0].exists()
    assert not compiled_paths[0].parent.exists()


def test_render_pdf_source_writes_source_and_cleans_temp_dir(monkeypatch):
    compiled_paths: list[Path] = []

    def fake_compile(path: str) -> bytes:
        typ_path = Path(path)
        compiled_paths.append(typ_path)
        assert typ_path.read_text(encoding='utf-8') == 'complete typst source'
        return b'%PDF'

    monkeypatch.setattr('ceres.report.render.typst.compile', fake_compile)

    assert render_pdf_source('complete typst source') == b'%PDF'
    assert compiled_paths
    assert not compiled_paths[0].exists()
    assert not compiled_paths[0].parent.exists()
