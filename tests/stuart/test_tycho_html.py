from stuart import render_ship_spec_html

from tests.ships.test_suleiman import build_suleiman


def test_render_ship_spec_html_uses_high_guard_like_split_layout():
    spec = build_suleiman().build_spec()
    html = render_ship_spec_html(spec)

    assert 'class="ship-grid"' in html
    assert 'class="spec-table"' in html
    assert 'class="ship-sidebar"' in html
    assert '<th>Section</th><th>Item</th><th class="num">Tons</th><th class="num">Cost (MCr)</th>' in html
    assert '<th>Item</th><th class="num">Power</th>' in html
    assert '<th>Item</th><th class="num">Amount</th>' in html
    assert 'Power</header>' in html
    assert 'Costs</header>' in html
    assert 'Basic Ship Systems' in html
    assert 'Jump 2' in html
    assert 'Staterooms × 4' in html
    assert html.index('Fusion (TL 12)') < html.index('Basic Ship Systems')
    assert 'class="num power-positive">60.00</td>' in html
    assert '<td>Basic Ship Systems</td><td class="num">20.00</td>' in html
    assert 'scope="rowgroup" class="section-cell" rowspan="' in html
    assert '<ul class="item-notes">' in html
    assert 'Features: Passive optical and thermal sensors' in html
    assert 'data-theme-toggle' in html
    assert '<body class="theme-light">' in html


def test_render_ship_spec_html_supports_dark_theme():
    spec = build_suleiman().build_spec()
    html = render_ship_spec_html(spec, theme='dark')

    assert '<body class="theme-dark">' in html
    assert 'data-theme-toggle' in html
    assert 'aria-label="Switch theme"' in html
