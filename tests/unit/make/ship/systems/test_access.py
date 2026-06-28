"""Unit tests for systems/access.py — Airlock, BreachingTube, ForcedLinkageApparatus."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.access import Airlock, ForcedLinkageApparatus
from ceres.make.ship.systems.security import BoobyTrapTL8, BoobyTrapTL12


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=200):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=200):
    part.bind(_Ship(tl, displacement))
    return part


class TestAirlock:
    def test_booby_trapped_airlock_cost_includes_trap(self):
        airlock = Airlock(size=3, booby_trap=BoobyTrapTL8())
        _bind(airlock, displacement=99)
        assert airlock.cost == pytest.approx(600_000.0)

    def test_booby_trapped_airlock_note(self):
        airlock = Airlock(size=3, booby_trap=BoobyTrapTL8())
        _bind(airlock, displacement=99)
        assert airlock.notes.infos == ['Booby-trapped: 5D damage/round']

    def test_booby_trap_tl_mismatch_is_error(self):
        airlock = Airlock(booby_trap=BoobyTrapTL12())
        _bind(airlock, tl=10, displacement=99)
        assert 'Requires TL12, ship is TL10' in airlock.notes.errors


class TestForcedLinkageApparatus:
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

    def test_rejects_ship_above_5000_tons(self):
        apparatus = _bind(ForcedLinkageApparatus(tier='Enhanced'), displacement=5_001)
        assert 'Forced linkage apparatus may only be used on ships of 5000 tons or less' in apparatus.notes.errors

    def test_allows_ship_at_5000_tons(self):
        apparatus = _bind(ForcedLinkageApparatus(tier='Enhanced'), displacement=5_000)
        assert 'Forced linkage apparatus may only be used on ships of 5000 tons or less' not in apparatus.notes.errors
