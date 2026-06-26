"""Unit tests for humaniti.py — Sophont dataclass and pre-defined sophonts."""

from ceres.character.domain.sophont.humaniti import (
    HUMANITI,
    VILANI,
)
from tests.unit.character.helpers import MOCK_WORLD


class TestSophontAvailableAt:
    def test_humaniti_available_everywhere(self):
        assert HUMANITI.available_at(MOCK_WORLD) is True

    def test_vilani_available_at_imperium_world(self):
        # MOCK_WORLD has allegiance 'ImDi' which starts with 'Im'
        assert VILANI.available_at(MOCK_WORLD) is True

    def test_remarks_based_sophont_unavailable_at_mock_world(self):
        from ceres.character.domain.sophont.humaniti import DARMINE

        assert DARMINE.available_at(MOCK_WORLD) is False

    def test_remarks_match_when_code_in_remarks(self):
        from ceres.adapters.travellermap import TravellerMapWorld
        from tests.unit.character.helpers import MOCK_WORLD

        world = TravellerMapWorld.model_validate(
            {
                **MOCK_WORLD.model_dump(),
                'Remarks': 'Ag Darm Ni',
            }
        )
        from ceres.character.domain.sophont.humaniti import DARMINE

        assert DARMINE.available_at(world) is True


class TestSophontFields:
    def test_name(self):
        assert VILANI.name == 'Vilani'

    def test_ucp_stats_default_length(self):
        assert len(VILANI.ucp_stats) == 6

    def test_allegiance_pattern(self):
        assert VILANI.allegiance_pattern == 'Im*'

    def test_humaniti_wildcard(self):
        assert HUMANITI.allegiance_pattern == '*'
