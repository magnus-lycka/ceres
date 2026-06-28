"""Unit tests for systems/command.py — BriefingRoom, CommandBridge."""

from ceres.make.ship.systems.command import BriefingRoom, CommandBridge


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
