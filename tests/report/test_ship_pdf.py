import pytest

from ceres.make.ship.report import _fmt_cr_col, _fmt_tons, render_ship_spec_typst
from ceres.make.ship.spec import ShipSpec
from ceres.report import render_ship_pdf, render_ship_spec_pdf
from tests.ships.test_dragon import build_dragon
from tests.ships.test_small_scout_base import build_small_scout_base
from tests.ships.test_suleiman import build_suleiman
from tests.ships.test_ultralight_fighter import build_ultralight_fighter


@pytest.fixture
def suleiman_spec():
    return build_suleiman().build_spec()


@pytest.fixture
def fighter_spec():
    return build_ultralight_fighter().build_spec()


# ---------------------------------------------------------------------------
# Public API smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_render_ship_spec_pdf_returns_pdf_bytes(suleiman_spec):
    pdf = render_ship_spec_pdf(suleiman_spec)
    assert pdf[:4] == b'%PDF'


@pytest.mark.slow
def test_render_ship_pdf_returns_pdf_bytes():
    pdf = render_ship_pdf(build_suleiman())
    assert pdf[:4] == b'%PDF'


def test_render_ship_spec_typst_page_size_passed_through(suleiman_spec):
    src_a4 = render_ship_spec_typst(suleiman_spec, page_size='a4')
    src_letter = render_ship_spec_typst(suleiman_spec, page_size='us-letter')
    assert '"a4"' in src_a4
    assert '"us-letter"' in src_letter


# ---------------------------------------------------------------------------
# Banner and metadata
# ---------------------------------------------------------------------------


def test_source_contains_ship_class_uppercased(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'SULEIMAN' in src


def test_source_contains_ship_type(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'Scout/Courier' in src


def test_source_contains_tech_level(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'TL12' in src


# ---------------------------------------------------------------------------
# Main spec table
# ---------------------------------------------------------------------------


def test_source_contains_section_names(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'Hull' in src
    assert 'Jump' in src
    assert 'Power' in src
    assert 'Fuel' in src


def test_source_contains_item_names(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'Jump 2' in src
    assert 'Fuel Processor' in src
    assert 'Staterooms' in src


def test_source_collapses_identical_rows_for_display():
    src = render_ship_spec_typst(build_small_scout_base().build_spec())
    assert 'Full Hangar: Passenger Shuttle × 10' in src
    assert 'Passenger Shuttle × 10' in src


def test_source_contains_formatted_ton_value(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert '20.00' in src


def test_source_contains_formatted_cr_value(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert '15,000,000' in src


def test_fmt_cr_col_formats_nine_billion():
    assert _fmt_cr_col(9_000_000_000) == '9,000,000,000'


def test_fmt_tons_formats_nine_million():
    assert _fmt_tons(9_000_000) == '9,000,000.00'


# ---------------------------------------------------------------------------
# Notes (info / warning / error)
# ---------------------------------------------------------------------------


def test_source_contains_info_notes(suleiman_spec):
    info_rows = [r for r in suleiman_spec.rows if any(n.category.value == 'info' for n in r.notes)]
    assert info_rows, 'precondition: Suleiman has info notes'
    src = render_ship_spec_typst(suleiman_spec)
    for row in info_rows:
        for note in row.notes:
            if note.category.value == 'info':
                assert note.message in src


def test_info_notes_use_gentle_clues_info_box(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'gc-info(' in src


def test_source_renders_warning_notes_via_gentle_clues():
    from ceres.make.ship.base import NoteList
    from ceres.make.ship.spec import SpecRow, SpecSection

    spec = ShipSpec(ship_class='Test')
    notes = NoteList()
    notes.warning('Check this')
    row = SpecRow(
        section=SpecSection.HULL,
        item='Widget',
        tons=1.0,
        notes=notes,
    )
    spec.add_row(row)
    src = render_ship_spec_typst(spec)
    assert 'Check this' in src
    assert 'gc-warning(' in src


def test_source_renders_error_notes_via_gentle_clues():
    from ceres.make.ship.base import NoteList
    from ceres.make.ship.spec import SpecRow, SpecSection

    spec = ShipSpec(ship_class='Test')
    notes = NoteList()
    notes.error('Fix this')
    row = SpecRow(section=SpecSection.HULL, item='Widget', tons=1.0, notes=notes)
    spec.add_row(row)
    src = render_ship_spec_typst(spec)
    assert 'Fix this' in src
    assert 'gc-error(' in src


def test_source_renders_ship_level_notes_below_main_table():
    from ceres.make.ship.base import NoteList

    spec = ShipSpec(ship_class='Test')
    spec.ship_notes = NoteList()
    spec.ship_notes.error('No airlock installed')
    spec.ship_notes.warning('Crew below recommended count')

    src = render_ship_spec_typst(spec)
    assert 'No airlock installed' in src
    assert 'Crew below recommended count' in src


def test_source_renders_crew_notes_with_crew_table():
    from ceres.make.ship.base import NoteList

    spec = ShipSpec(ship_class='Test')
    spec.crew = []
    spec.crew_notes = NoteList()
    spec.crew_notes.warning('GUNNER below recommended count: 0 < 1')

    src = render_ship_spec_typst(spec)
    assert 'CREW' in src
    assert 'GUNNER below recommended count: 0 < 1' in src


def test_source_renders_multiple_info_crew_notes_via_gentle_clues():
    from ceres.make.ship.base import NoteList

    spec = ShipSpec(ship_class='Test')
    spec.crew = []
    spec.crew_notes = NoteList()
    spec.crew_notes.info('ASTROGATOR above recommended count: 1 > 0')
    spec.crew_notes.info('GUNNER above recommended count: 6 > 5')
    spec.crew_notes.info('MAINTENANCE above recommended count: 1 > 0')

    src = render_ship_spec_typst(spec)
    assert 'CREW' in src
    assert 'ASTROGATOR above recommended count: 1 > 0' in src
    assert 'GUNNER above recommended count: 6 > 5' in src
    assert 'MAINTENANCE above recommended count: 1 > 0' in src
    assert 'gc-info(' in src


def test_source_contains_dragon_bulkhead_notes():
    spec = build_dragon().build_spec()
    bulkhead_rows = [r for r in spec.rows if 'Bulkhead' in r.item]
    assert bulkhead_rows, 'precondition: Dragon has armoured bulkhead row'
    src = render_ship_spec_typst(spec)
    for row in bulkhead_rows:
        for note in row.notes:
            if note.category.value != 'item':
                assert note.message[:20] in src


def test_source_uses_guard_column_for_sections(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'breakable: false' in src


def test_source_has_rowspan_for_multi_row_sections(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'rowspan:' in src


def test_source_uses_uniform_internal_table_rules(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert '#let table-border = 0.6pt + ink' in src
    assert '#let table-rule = 0.3pt + rgb("#b0a090")' in src
    assert '#set table(stroke: table-rule)' in src
    assert 'stroke: (_x, _y) => (right: table-rule, bottom: table-rule),' in src
    assert 'if y == 0' not in src


def test_power_only_rows_excluded_from_main_table(suleiman_spec):
    from ceres.make.ship.view import collapsed_main_rows

    power_only = [r for r in suleiman_spec.rows if r.power is not None and r.tons is None and r.cost is None]
    assert power_only, 'precondition: Suleiman has power-only rows'
    main = collapsed_main_rows(suleiman_spec)
    for row in power_only:
        assert row not in main


# ---------------------------------------------------------------------------
# Crew card
# ---------------------------------------------------------------------------


def test_source_contains_crew_roles(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'CREW' in src
    for c in suleiman_spec.crew:
        assert c.role in src


def test_source_shows_uncrewed_for_no_crew():
    spec = ShipSpec(ship_class='Drone')
    src = render_ship_spec_typst(spec)
    assert 'Uncrewed' in src


# ---------------------------------------------------------------------------
# Power card
# ---------------------------------------------------------------------------


def test_source_contains_power_section_sums(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'POWER' in src
    sections_with_power = {
        r.section.value for r in suleiman_spec.rows if r.power is not None and r.item != 'Basic Ship Systems'
    }
    for section in sections_with_power:
        assert section in src


def test_source_shows_basic_ship_systems_as_own_row(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'Basic Ship Systems' in src


def test_source_power_sums_by_section(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    from collections import defaultdict

    sums: dict = defaultdict(float)
    for r in suleiman_spec.rows:
        if r.power is not None:
            sums[r.section.value] += r.power
    for section, total in sums.items():
        assert f'{abs(total):.2f}' in src


def test_source_bolds_power_producing_sections(suleiman_spec):
    from ceres.make.ship.report import _build_power

    producing_sections = {r.section.value for r in suleiman_spec.rows if r.power is not None and r.emphasize_power}
    assert producing_sections, 'precondition: Suleiman has power producers'
    power = _build_power(suleiman_spec.rows)
    by_label = {p['label']: p for p in power}
    for section in producing_sections:
        assert by_label[section]['emphasize'] is True
    src = render_ship_spec_typst(suleiman_spec)
    assert '*#p.label*' in src


def test_source_power_producers_before_consumers(suleiman_spec):
    from ceres.make.ship.report import _build_power

    power = _build_power(suleiman_spec.rows)
    producers = [p for p in power if p['emphasize']]
    assert producers, 'precondition: Suleiman has power producers'
    basic_index = next(i for i, p in enumerate(power) if p['label'] == 'Basic Ship Systems')
    first_producer_index = power.index(producers[0])
    assert first_producer_index < basic_index


# ---------------------------------------------------------------------------
# Costs card
# ---------------------------------------------------------------------------


def test_source_contains_cost_labels(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert 'COSTS' in src
    for e in suleiman_spec.expenses:
        assert e.label in src


def test_source_formats_costs(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    production = next(e for e in suleiman_spec.expenses if e.label == 'Production Cost')
    mcr = f'{production.amount / 1_000_000:.3f}'.rstrip('0').rstrip('.')
    assert f'MCr {mcr}' in src
    assert 'COSTS (Cr)' in src


# ---------------------------------------------------------------------------
# Sidebar cards are kept together
# ---------------------------------------------------------------------------


def test_source_wraps_sidebar_cards_in_non_breakable_blocks(suleiman_spec):
    src = render_ship_spec_typst(suleiman_spec)
    assert src.count('block(breakable: false') == 3
