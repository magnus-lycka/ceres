"""Unit tests for make/ship/view.py — spec row collapsing logic."""

from ceres.make.ship.spec import SpecRow, SpecSection
from ceres.make.ship.view import (
    _blocks_match,
    _can_collapse,
    _collapse_repeated_blocks,
    _copy_notes,
    _merge_rows,
    _sum_or_none,
    collapsed_main_rows,
)
from ceres.shared import NoteList


def _row(
    item='Widget',
    tons=2.0,
    cost=100.0,
    power=-4.0,
    section=SpecSection.SYSTEMS,
    notes=None,
    emphasize_tons=False,
    emphasize_power=False,
) -> SpecRow:
    return SpecRow(
        section=section,
        item=item,
        tons=tons,
        cost=cost,
        power=power,
        notes=notes or NoteList(),
        emphasize_tons=emphasize_tons,
        emphasize_power=emphasize_power,
    )


class TestSumOrNone:
    def test_both_none_returns_none(self):
        assert _sum_or_none(None, None) is None

    def test_left_none_returns_right(self):
        assert _sum_or_none(None, 3.0) == 3.0

    def test_right_none_returns_left(self):
        assert _sum_or_none(2.5, None) == 2.5

    def test_both_present_sums(self):
        assert _sum_or_none(1.5, 2.5) == 4.0


class TestCanCollapse:
    def test_identical_rows_can_collapse(self):
        assert _can_collapse(_row(), _row())

    def test_different_items_cannot_collapse(self):
        assert not _can_collapse(_row(item='A'), _row(item='B'))

    def test_different_sections_cannot_collapse(self):
        assert not _can_collapse(
            _row(section=SpecSection.HULL),
            _row(section=SpecSection.SYSTEMS),
        )

    def test_different_tons_can_still_collapse(self):
        assert _can_collapse(_row(tons=1.0), _row(tons=2.0))

    def test_different_cost_can_still_collapse(self):
        assert _can_collapse(_row(cost=100.0), _row(cost=200.0))

    def test_different_notes_cannot_collapse(self):
        assert not _can_collapse(_row(notes=NoteList().info('left')), _row(notes=NoteList().info('right')))

    def test_different_emphasize_tons_cannot_collapse(self):
        assert not _can_collapse(_row(emphasize_tons=True), _row(emphasize_tons=False))

    def test_different_emphasize_power_cannot_collapse(self):
        assert not _can_collapse(_row(emphasize_power=True), _row(emphasize_power=False))


class TestBlocksMatch:
    def test_same_collapsible_rows_match(self):
        left = [_row('A'), _row('B')]
        right = [_row('A'), _row('B')]

        assert _blocks_match(left, right)

    def test_different_lengths_do_not_match(self):
        assert not _blocks_match([_row('A')], [_row('A'), _row('B')])

    def test_non_collapsible_row_prevents_match(self):
        assert not _blocks_match([_row('A'), _row('B')], [_row('A'), _row('C')])


class TestMergeRows:
    def test_sums_tons(self):
        merged = _merge_rows(_row(tons=3.0), _row(tons=5.0))
        assert merged.tons == 8.0

    def test_sums_cost(self):
        merged = _merge_rows(_row(cost=100.0), _row(cost=150.0))
        assert merged.cost == 250.0

    def test_sums_power(self):
        merged = _merge_rows(_row(power=-4.0), _row(power=-6.0))
        assert merged.power == -10.0

    def test_quantity_accumulates_from_one(self):
        merged = _merge_rows(_row(), _row())
        assert merged.quantity == 2

    def test_existing_quantity_is_respected(self):
        merged1 = _merge_rows(_row(), _row())
        merged2 = _merge_rows(merged1, _row())
        assert merged2.quantity == 3

    def test_none_tons_handled(self):
        r1 = SpecRow(section=SpecSection.HULL, item='X', tons=None)
        r2 = SpecRow(section=SpecSection.HULL, item='X', tons=2.0)
        assert _merge_rows(r1, r2).tons == 2.0

    def test_notes_are_copied_not_reused(self):
        notes = NoteList().info('copied')
        merged = _merge_rows(_row(notes=notes), _row())

        assert merged.notes == notes
        assert merged.notes is not notes


class TestCollapseRepeatedBlocks:
    def test_short_input_returns_original_rows(self):
        rows = [_row('A')]

        assert _collapse_repeated_blocks(rows, block_len=2) is rows

    def test_repeated_two_row_blocks_are_collapsed_by_position(self):
        rows = [_row('A', tons=1), _row('B', tons=2), _row('A', tons=3), _row('B', tons=4)]

        collapsed = _collapse_repeated_blocks(rows, block_len=2)

        assert [row.item for row in collapsed] == ['A', 'B']
        assert [row.quantity for row in collapsed] == [2, 2]
        assert [row.tons for row in collapsed] == [4, 6]

    def test_non_repeating_block_advances_one_row(self):
        rows = [_row('A'), _row('B'), _row('C'), _row('D')]

        collapsed = _collapse_repeated_blocks(rows, block_len=2)

        assert [row.item for row in collapsed] == ['A', 'B', 'C', 'D']

    def test_trailing_partial_block_is_preserved(self):
        rows = [_row('A'), _row('B'), _row('A'), _row('B'), _row('C')]

        collapsed = _collapse_repeated_blocks(rows, block_len=2)

        assert [row.item for row in collapsed] == ['A', 'B', 'C']

    def test_can_collapse_more_than_two_repeated_blocks(self):
        rows = [_row('A'), _row('B'), _row('A'), _row('B'), _row('A'), _row('B')]

        collapsed = _collapse_repeated_blocks(rows, block_len=2)

        assert [row.quantity for row in collapsed] == [3, 3]


def test_copy_notes_returns_a_new_list_with_same_notes():
    notes = NoteList().warning('careful')

    copied = _copy_notes(notes)

    assert copied == notes
    assert copied is not notes


def _spec(*rows: SpecRow):
    from ceres.make.ship.spec import ShipSpec

    spec = ShipSpec()
    for row in rows:
        spec.add_row(row)
    return spec


class TestCollapsedMainRows:
    def test_empty_spec_returns_empty(self):
        assert collapsed_main_rows(_spec()) == []

    def test_filters_power_only_rows(self):
        result = collapsed_main_rows(
            _spec(
                SpecRow(section=SpecSection.POWER, item='Plant', tons=None, cost=None, power=100.0),
                SpecRow(section=SpecSection.SYSTEMS, item='Sensor', tons=5.0, cost=500.0, power=-4.0),
            )
        )
        assert all(r.item != 'Plant' for r in result)

    def test_collapses_identical_adjacent_rows(self):
        bunk = _row('Bunk', tons=4.0, cost=200.0, power=0.0)
        result = collapsed_main_rows(_spec(bunk, bunk, bunk))
        assert len(result) == 1
        assert result[0].quantity == 3
        assert result[0].tons == 12.0

    def test_does_not_collapse_different_items(self):
        result = collapsed_main_rows(
            _spec(
                _row('A', tons=1.0, cost=10.0, power=0.0),
                _row('B', tons=2.0, cost=20.0, power=0.0),
            )
        )
        assert len(result) == 2

    def test_collapses_repeated_two_row_blocks_before_adjacent_collapse(self):
        result = collapsed_main_rows(
            _spec(
                _row('Stateroom', tons=4.0, cost=0.5, power=0.0),
                _row('Common Area', tons=1.0, cost=0.1, power=0.0),
                _row('Stateroom', tons=4.0, cost=0.5, power=0.0),
                _row('Common Area', tons=1.0, cost=0.1, power=0.0),
            )
        )

        assert [row.item for row in result] == ['Stateroom', 'Common Area']
        assert [row.quantity for row in result] == [2, 2]
