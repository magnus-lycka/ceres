"""Unit tests for systems/command.py — BriefingRoom, CommandBridge."""

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.command import BriefingRoom, CommandBridge


class _Ship(ShipBase):
    def __init__(self, displacement: int):
        super().__init__(tl=12, displacement=displacement)


class TestBriefingRoom:
    def test_computed_not_serialized(self):
        part = BriefingRoom.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        assert part.tons == 4.0
        assert part.cost == 500_000.0
        assert part.power == 0.0
        dump = part.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestCommandBridge:
    def test_forty_tons_thirty_mcr(self):
        bridge = CommandBridge()
        assert bridge.tons == 40.0
        assert bridge.cost == 30_000_000.0

    def test_build_notes_describes_tactics_bonus(self):
        bridge = CommandBridge()
        assert bridge.notes.infos == ['DM +1 to Tactics (naval) checks made within the command bridge']

    def test_tactics_naval_dm_is_plus_one(self):
        assert CommandBridge().tactics_naval_dm == 1

    def test_bind_rejects_ship_at_minimum_displacement(self):
        bridge = CommandBridge()

        bridge.bind(_Ship(displacement=5_000))

        assert bridge.notes.errors == ['Command bridge requires displacement greater than 5000 tons']

    def test_bind_accepts_ship_above_minimum_displacement(self):
        bridge = CommandBridge()

        bridge.bind(_Ship(displacement=5_001))

        assert bridge.notes.errors == []
