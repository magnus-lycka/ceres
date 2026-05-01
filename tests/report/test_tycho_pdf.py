import pytest

from ceres.report import render_ship_pdf, render_ship_spec_pdf, render_ship_spec_typst, render_ship_typst
from ceres.report.tycho_pdf import _build_typst_source
from tests.ships.test_dragon import build_dragon
from tests.ships.test_small_scout_base import build_small_scout_base
from tests.ships.test_suleiman import build_suleiman
from tests.ships.test_ultralight_fighter import build_ultralight_fighter
from ceres.make.ship.spec import ShipSpec


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


def test_render_ship_spec_pdf_page_size_passed_through(suleiman_spec):
    src_a4     = _build_typst_source(suleiman_spec, page_size='a4')
    src_letter = _build_typst_source(suleiman_spec, page_size='us-letter')
    assert 'paper: "a4"'        in src_a4
    assert 'paper: "us-letter"' in src_letter


# ---------------------------------------------------------------------------
# Banner and metadata
# ---------------------------------------------------------------------------

def test_source_contains_ship_class_uppercased(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'SULEIMAN' in src


def test_source_contains_ship_type(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'Scout/Courier' in src


def test_source_contains_tech_level(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'TL12' in src


# ---------------------------------------------------------------------------
# Main spec table
# ---------------------------------------------------------------------------

def test_source_contains_section_names(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'Hull' in src
    assert 'Jump' in src
    assert 'Power' in src
    assert 'Fuel' in src


def test_source_contains_item_names(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'Jump 2' in src
    assert 'Fuel Processor' in src
    assert 'Staterooms' in src


def test_source_collapses_identical_rows_for_display():
    src = _build_typst_source(build_small_scout_base().build_spec(), page_size='a4')
    assert 'Full Hangar: Passenger Shuttle × 10' in src
    assert 'Passenger Shuttle × 10' in src


def test_source_contains_formatted_ton_value(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    # Jump fuel for 100t ship Jump-2 = 20t
    assert '20.00' in src


def test_source_contains_formatted_cr_value(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    # Jump 2 for 100t = MCr15 = 15,000,000 Cr
    assert '15,000,000' in src


def test_fmt_cr_col_formats_nine_billion():
    from ceres.report.tycho_pdf import _fmt_cr_col
    assert _fmt_cr_col(9_000_000_000) == '9,000,000,000'


def test_fmt_tons_formats_nine_million():
    from ceres.report.tycho_pdf import _fmt_tons
    assert _fmt_tons(9_000_000) == '9,000,000.00'


# ---------------------------------------------------------------------------
# Notes (info / warning / error)
# ---------------------------------------------------------------------------

def test_source_contains_info_notes(suleiman_spec):
    info_rows = [r for r in suleiman_spec.rows if any(n.category.value == 'info' for n in r.notes)]
    assert info_rows, 'precondition: Suleiman has info notes'
    src = _build_typst_source(suleiman_spec, page_size='a4')
    for row in info_rows:
        for note in row.notes:
            if note.category.value == 'info':
                assert note.message in src


def test_info_notes_use_default_text_size():
    from ceres.make.ship.base import Note, NoteCategory
    from ceres.report.tycho_pdf import _render_notes
    notes = [Note(category=NoteCategory.INFO, message='Some info')]
    rendered = _render_notes(notes)
    assert '8pt' not in rendered
    assert 'Some info' in rendered


def test_source_renders_warning_notes_as_orange_italic():
    from ceres.make.ship.base import Note, NoteCategory
    spec = ShipSpec(ship_class='Test')
    from ceres.make.ship.spec import SpecRow, SpecSection
    row = SpecRow(section=SpecSection.HULL, item='Widget', tons=1.0,
                  notes=[Note(category=NoteCategory.WARNING, message='Check this')])
    spec.add_row(row)
    src = _build_typst_source(spec, page_size='a4')
    assert 'Warning: Check this' in src
    assert 'style: "italic"' in src
    assert 'e07800' in src


def test_source_renders_error_notes_as_red_bold():
    from ceres.make.ship.base import Note, NoteCategory
    spec = ShipSpec(ship_class='Test')
    from ceres.make.ship.spec import SpecRow, SpecSection
    row = SpecRow(section=SpecSection.HULL, item='Widget', tons=1.0,
                  notes=[Note(category=NoteCategory.ERROR, message='Fix this')])
    spec.add_row(row)
    src = _build_typst_source(spec, page_size='a4')
    assert 'Error: Fix this' in src
    assert 'weight: "bold"' in src
    assert 'cc2036' in src


def test_source_renders_ship_level_notes_below_main_table():
    from ceres.make.ship.base import Note, NoteCategory

    spec = ShipSpec(ship_class='Test')
    spec.ship_notes = [
        Note(category=NoteCategory.ERROR, message='No airlock installed'),
        Note(category=NoteCategory.WARNING, message='Crew below recommended count'),
    ]

    src = _build_typst_source(spec, page_size='a4')
    assert 'Error: No airlock installed' in src
    assert 'Warning: Crew below recommended count' in src


def test_source_renders_crew_notes_with_crew_table():
    from ceres.make.ship.base import Note, NoteCategory

    spec = ShipSpec(ship_class='Test')
    spec.crew = []
    spec.crew_notes = [
        Note(category=NoteCategory.WARNING, message='GUNNER below recommended count: 0 < 1'),
    ]

    src = _build_typst_source(spec, page_size='a4')
    assert 'CREW' in src
    assert 'Warning: GUNNER below recommended count: 0 < 1' in src


def test_source_escapes_multiple_info_crew_notes_to_avoid_nested_list_indentation():
    from ceres.make.ship.base import Note, NoteCategory

    spec = ShipSpec(ship_class='Test')
    spec.crew = []
    spec.crew_notes = [
        Note(category=NoteCategory.INFO, message='ASTROGATOR above recommended count: 1 > 0'),
        Note(category=NoteCategory.INFO, message='GUNNER above recommended count: 6 > 5'),
        Note(category=NoteCategory.INFO, message='MAINTENANCE above recommended count: 1 > 0'),
    ]

    src = _build_typst_source(spec, page_size='a4')
    assert 'CREW' in src
    assert 'ASTROGATOR above recommended count: 1 > 0' in src
    assert 'GUNNER above recommended count: 6 > 5' in src
    assert 'MAINTENANCE above recommended count: 1 > 0' in src
    assert '\\-' not in src
    assert 'style: "italic"' in src


def test_source_contains_dragon_bulkhead_notes():
    spec = build_dragon().build_spec()
    bulkhead_rows = [r for r in spec.rows if 'Bulkhead' in r.item]
    assert bulkhead_rows, 'precondition: Dragon has armoured bulkhead row'
    src = _build_typst_source(spec, page_size='a4')
    for row in bulkhead_rows:
        for note in row.notes:
            if note.category.value != 'item':
                assert note.message[:20] in src


def test_source_uses_guard_column_for_sections(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'breakable: false' in src


def test_source_has_rowspan_for_multi_row_sections(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'rowspan:' in src


def test_source_uses_uniform_internal_table_rules(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert '#let table-border = 0.6pt + ink' in src
    assert '#let table-rule = 0.3pt + rgb("#b0a090")' in src
    assert '#set table(stroke: table-rule)' in src
    assert 'stroke: (_x, _y) => (right: table-rule, bottom: table-rule),' in src
    assert 'if y == 0' not in src


def test_power_only_rows_excluded_from_main_table(suleiman_spec):
    from ceres.report.tycho_pdf import _main_rows
    power_only = [r for r in suleiman_spec.rows if r.power is not None and r.tons is None and r.cost is None]
    assert power_only, 'precondition: Suleiman has power-only rows'
    main = _main_rows(suleiman_spec)
    for row in power_only:
        assert row not in main


# ---------------------------------------------------------------------------
# Crew card
# ---------------------------------------------------------------------------

def test_source_contains_crew_roles(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'CREW' in src
    for c in suleiman_spec.crew:
        assert c.role in src


def test_source_shows_uncrewed_for_no_crew():
    spec = ShipSpec(ship_class='Drone')
    src = _build_typst_source(spec, page_size='a4')
    assert 'Uncrewed' in src


def test_esc_escapes_typst_markup_characters():
    from ceres.report.tycho_pdf import _esc

    assert _esc('foo*bar') == 'foo\\*bar'
    assert _esc('item_name') == 'item\\_name'
    assert _esc('[foo]') == '\\[foo\\]'
    assert _esc('#label') == '\\#label'
    assert _esc('back\\slash') == 'back\\\\slash'


# ---------------------------------------------------------------------------
# Power card
# ---------------------------------------------------------------------------

def test_source_contains_power_section_sums(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'POWER' in src
    sections_with_power = {
        r.section.value for r in suleiman_spec.rows
        if r.power is not None and r.item != 'Basic Ship Systems'
    }
    for section in sections_with_power:
        assert section in src


def test_source_shows_basic_ship_systems_as_own_row(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'Basic Ship Systems' in src


def test_source_power_sums_by_section(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    # Hull section: Basic Ship Systems consumes 20W — verify sum appears, not individual items
    from collections import defaultdict
    sums: dict = defaultdict(float)
    for r in suleiman_spec.rows:
        if r.power is not None:
            sums[r.section.value] += r.power
    for section, total in sums.items():
        assert f'{abs(total):.2f}' in src


def test_source_bolds_power_producing_sections(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    producing_sections = {r.section.value for r in suleiman_spec.rows if r.power is not None and r.emphasize_power}
    assert producing_sections, 'precondition: Suleiman has power producers'
    for section in producing_sections:
        assert f'*{section}*' in src


def test_source_power_producers_before_consumers(suleiman_spec):
    from ceres.report.tycho_pdf import _power_rows
    rows_src = _power_rows(suleiman_spec)
    producing_sections = {r.section.value for r in suleiman_spec.rows if r.power is not None and r.emphasize_power}
    first_producer = min(rows_src.index(f'*{s}*') for s in producing_sections if f'*{s}*' in rows_src)
    assert rows_src.index('Basic Ship Systems') > first_producer


# ---------------------------------------------------------------------------
# Costs card
# ---------------------------------------------------------------------------

def test_source_contains_cost_labels(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert 'COSTS' in src
    for e in suleiman_spec.expenses:
        assert e.label in src


def test_source_formats_costs_with_thousands_no_unit(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    production = next(e for e in suleiman_spec.expenses if e.label == 'Production Cost')
    assert f'{round(production.amount):,}' in src
    assert 'COSTS (Cr)' in src


# ---------------------------------------------------------------------------
# Sidebar cards are kept together
# ---------------------------------------------------------------------------

def test_source_wraps_sidebar_cards_in_non_breakable_blocks(suleiman_spec):
    src = _build_typst_source(suleiman_spec, page_size='a4')
    assert src.count('block(breakable: false') == 3
