import pytest

from ceres.make.ship.base import NoteList
from ceres.make.ship.spec import CrewRow, ExpenseRow, ShipSpec, SpecRow, SpecSection


def build_spec() -> ShipSpec:
    spec = ShipSpec(ship_class='Test', ship_type='Demo', tl=12, hull_points=40)
    spec.add_row(SpecRow(section=SpecSection.FUEL, item='Jump 2', tons=20.0))
    spec.add_row(SpecRow(section=SpecSection.JUMP, item='Jump 2', power=20.0))
    notes = NoteList()
    notes.info('Library included')
    notes.warning('Limited by software')
    spec.add_row(
        SpecRow(
            section=SpecSection.COMPUTER,
            item='Computer/5',
            notes=notes,
        )
    )
    spec.expenses = [ExpenseRow(label='Production Cost', amount=1_000_000)]
    spec.crew = [CrewRow(role='PILOT', salary=6_000)]
    return spec


def test_spec_row_notes_only_contain_display_notes():
    notes = NoteList()
    notes.info('Library included')
    notes.warning('Limited by software')
    notes.error('Broken')
    row = SpecRow(
        section=SpecSection.COMPUTER,
        item='Computer/5',
        notes=notes,
    )

    row_notes = row.notes
    assert row_notes.infos == ['Library included']
    assert row_notes.warnings == ['Limited by software']
    assert row_notes.errors == ['Broken']


def test_ship_spec_rows_for_section_returns_matching_rows():
    spec = build_spec()

    assert [row.item for row in spec.rows_for_section(SpecSection.FUEL)] == ['Jump 2']


def test_ship_spec_row_can_disambiguate_by_section():
    spec = build_spec()

    assert spec.row('Jump 2', section=SpecSection.FUEL).section == SpecSection.FUEL
    assert spec.row('Jump 2', section=SpecSection.JUMP).section == SpecSection.JUMP


def test_ship_spec_row_raises_helpful_key_error_for_missing_sectioned_row():
    spec = build_spec()

    with pytest.raises(KeyError, match=r"item='Jump 2' in section=<SpecSection.POWER: 'Power'>"):
        spec.row('Jump 2', section=SpecSection.POWER)


def test_ship_spec_rows_matching_returns_all_rows_with_item():
    spec = build_spec()

    assert [row.section for row in spec.rows_matching('Jump 2')] == [SpecSection.JUMP, SpecSection.FUEL]


def test_spec_row_can_store_quantity_separately_from_item():
    row = SpecRow(section=SpecSection.HABITATION, item='Staterooms', quantity=10, tons=40.0)

    assert row.item == 'Staterooms'
    assert row.quantity == 10


def test_crew_row_can_store_quantity_separately_from_role():
    row = CrewRow(role='PILOT', quantity=3, salary=18_000)

    assert row.role == 'PILOT'
    assert row.quantity == 3
