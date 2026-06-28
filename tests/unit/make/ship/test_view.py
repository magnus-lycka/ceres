"""Unit tests for make/ship/view.py — spec row collapsing logic."""

from ceres.make.ship.spec import SpecRow, SpecSection
from ceres.make.ship.view import (
    _can_collapse,
    _merge_rows,
    _sum_or_none,
    collapsed_main_rows,
)


def _row(item='Widget', tons=2.0, cost=100.0, power=-4.0, section=SpecSection.SYSTEMS) -> SpecRow:
    return SpecRow(section=section, item=item, tons=tons, cost=cost, power=power)


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
