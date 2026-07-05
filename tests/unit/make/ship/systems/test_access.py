"""Unit tests for systems/access.py — Airlock, BreachingTube, ForcedLinkageApparatus."""

from pydantic import ValidationError
import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.hull.standard import Hull, streamlined_hull
from ceres.make.ship.systems.access import Airlock, BreachingTube, ForcedLinkageApparatus
from ceres.make.ship.systems.security import BoobyTrapTL8, BoobyTrapTL12


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=200, hull=None):
        super().__init__(tl=tl, displacement=displacement)
        object.__setattr__(self, 'hull', hull)


def _bind(part, tl=12, displacement=200):
    part.bind(_Ship(tl, displacement))
    return part


def _bind_with_hull(part, *, tl=12, displacement=200, hull):
    part.bind(_Ship(tl, displacement, hull))
    return part


class TestAirlock:
    def test_description_includes_size(self):
        assert Airlock(size=3).item_description() == 'Airlock (3 tons)'

    def test_minimum_two_tons_when_not_free(self):
        airlock = _bind(Airlock(size=1), displacement=99)
        assert airlock.tons == 2.0
        assert airlock.cost == 200_000.0

    def test_large_ship_without_hull_does_not_get_free_airlock(self):
        airlock = _bind(Airlock(), displacement=200)
        assert airlock.am_i_for_free() is False
        assert airlock.tons == 2.0

    def test_large_ship_airlock_must_be_installed_on_bound_hull_to_be_free(self):
        installed = Airlock()
        uninstalled = Airlock()
        hull = Hull(configuration=streamlined_hull, airlocks=[installed])
        _bind_with_hull(uninstalled, displacement=200, hull=hull)
        assert uninstalled.am_i_for_free() is False

    def test_large_ship_airlocks_installed_on_hull_are_free_by_interval(self):
        first = Airlock()
        second = Airlock()
        third = Airlock()
        hull = Hull(configuration=streamlined_hull, airlocks=[first, second, third])

        _bind_with_hull(first, displacement=200, hull=hull)
        _bind_with_hull(second, displacement=200, hull=hull)
        _bind_with_hull(third, displacement=200, hull=hull)

        assert first.am_i_for_free() is True
        assert second.am_i_for_free() is True
        assert third.am_i_for_free() is False
        assert first.tons == 0.0
        assert first.cost == 0.0
        assert third.tons == 2.0

    def test_booby_trap_cost_remains_when_airlock_itself_is_free(self):
        airlock = Airlock(booby_trap=BoobyTrapTL8())
        hull = Hull(configuration=streamlined_hull, airlocks=[airlock])
        _bind_with_hull(airlock, displacement=100, hull=hull)
        assert airlock.tons == 0.0
        assert airlock.cost == 300_000.0

    def test_booby_trapped_airlock_cost_includes_trap(self):
        airlock = Airlock(size=3, booby_trap=BoobyTrapTL8())
        _bind(airlock, displacement=99)
        assert airlock.cost == pytest.approx(600_000.0)

    def test_booby_trapped_airlock_note(self):
        airlock = Airlock(size=3, booby_trap=BoobyTrapTL8())
        _bind(airlock, displacement=99)
        assert airlock.notes.infos == ['Booby-trapped: 5D damage/round']

    def test_untrapped_airlock_has_no_notes(self):
        airlock = _bind(Airlock())
        assert airlock.notes.infos == []

    def test_booby_trap_tl_mismatch_is_error(self):
        airlock = Airlock(booby_trap=BoobyTrapTL12())
        _bind(airlock, tl=10, displacement=99)
        assert 'Requires TL12, ship is TL10' in airlock.notes.errors


class TestBreachingTube:
    def test_fixed_tonnage_cost_and_notes(self):
        tube = _bind(BreachingTube())
        assert tube.tons == 3.0
        assert tube.cost == 3_000_000.0
        assert tube.power == 0.0
        assert 'DM +1 to Boarding Actions rolls' in tube.notes.infos
        assert 'Can only attach to disabled or otherwise inert ships' in tube.notes.infos
        assert any('2D damage' in info for info in tube.notes.infos)


class TestForcedLinkageApparatus:
    def test_tier_is_required(self):
        with pytest.raises(ValidationError):
            ForcedLinkageApparatus()

    @pytest.mark.parametrize(
        ('tier', 'tl', 'pilot_dm'),
        [
            ('Basic', 7, -2),
            ('Improved', 9, -1),
            ('Enhanced', 12, 0),
            ('Advanced', 15, 2),
        ],
    )
    def test_tier_table_values(self, tier, tl, pilot_dm):
        apparatus = ForcedLinkageApparatus(tier=tier)
        assert apparatus.tl == tl
        assert apparatus.pilot_check_dm == pilot_dm
        assert apparatus.tons == 2.0
        assert apparatus.cost > 0.0

    def test_description_and_notes_include_tier_and_operating_limits(self):
        apparatus = _bind(ForcedLinkageApparatus(tier='Advanced'))
        assert apparatus.item_description() == 'Forced Linkage Apparatus (Advanced)'
        assert 'Pilot check DM +2' in apparatus.notes.infos
        assert 'Requires Thrust advantage of at least 1 over the target' in apparatus.notes.infos
        assert 'Cannot target ships above 5000 tons' in apparatus.notes.infos
        assert 'May be combined with a breaching tube' in apparatus.notes.infos

    def test_rejects_ship_above_5000_tons(self):
        apparatus = _bind(ForcedLinkageApparatus(tier='Enhanced'), displacement=5_001)
        assert 'Forced linkage apparatus may only be used on ships of 5000 tons or less' in apparatus.notes.errors

    def test_allows_ship_at_5000_tons(self):
        apparatus = _bind(ForcedLinkageApparatus(tier='Enhanced'), displacement=5_000)
        assert 'Forced linkage apparatus may only be used on ships of 5000 tons or less' not in apparatus.notes.errors
