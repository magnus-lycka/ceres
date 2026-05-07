from ceres.make.ship import hull, ship
from ceres.make.ship.crafts import CraftSection, FullHangar, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.spec import ShipSpec
from ceres.report import render_ship_spec_html
from ceres.shared import NoteList
from tests.ships.test_small_scout_base import build_small_scout_base
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
    assert html.index('Fusion (TL 12), Power 60') < html.index('Basic Ship Systems')
    assert 'class="num power-positive">60.00</td>' in html
    assert '<td>Basic Ship Systems</td><td class="num">20.00</td>' in html
    assert 'scope="rowgroup" class="section-cell" rowspan="' in html
    assert 'class="admonition' in html
    assert 'Passive optical and thermal sensors' in html
    assert 'data-theme-toggle' in html
    assert '<body class="theme-light">' in html


def test_render_ship_spec_html_supports_dark_theme():
    spec = build_suleiman().build_spec()
    html = render_ship_spec_html(spec, theme='dark')

    assert '<body class="theme-dark">' in html
    assert 'data-theme-toggle' in html
    assert 'aria-label="Switch theme"' in html


def test_render_ship_spec_html_renders_crew_notes_as_grouped_admonitions():
    spec = ShipSpec(ship_class='Test')
    spec.crew_notes = NoteList()
    spec.crew_notes.info('CAPTAIN above recommended count: 1 > 0')
    spec.crew_notes.warning('GUNNER below recommended count: 0 < 1')

    html = render_ship_spec_html(spec)

    assert 'class="admonition admonition-info"' in html
    assert 'CAPTAIN above recommended count: 1 &gt; 0' in html
    assert 'class="admonition admonition-warning"' in html
    assert 'GUNNER below recommended count: 0 &lt; 1' in html
    # warning appears before info (error → warning → info sort order)
    assert html.index('class="admonition admonition-warning"') < html.index('class="admonition admonition-info"')


def test_render_ship_spec_html_collapses_identical_rows_for_display():
    html = render_ship_spec_html(build_small_scout_base().build_spec())

    assert 'Full Hangar: Passenger Shuttle × 10' in html
    assert 'Passenger Shuttle × 10' in html


def test_render_ship_spec_html_keeps_craft_after_their_housing_rows():
    craft_ship = ship.Ship(
        tl=12,
        displacement=10_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        craft=CraftSection(
            internal_housing=[
                *[FullHangar(craft=SpaceCraft.from_catalog('Passenger Shuttle'))] * 10,
                *[FullHangar(craft=SpaceCraft.from_catalog("Ship's Boat"))] * 2,
                *[InternalDockingSpace(craft=Vehicle.from_catalog('G/Carrier'))] * 3,
            ],
        ),
    )
    html = render_ship_spec_html(craft_ship.build_spec())

    assert html.index('Full Hangar: Passenger Shuttle × 10') < html.index('Passenger Shuttle × 10')
    assert html.index('Full Hangar: Ship&#39;s Boat × 2') < html.index('Ship&#39;s Boat × 2')
    assert html.index('Internal Docking Space: G/Carrier × 3') < html.index('G/Carrier × 3')
