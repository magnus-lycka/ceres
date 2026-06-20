from ceres.character.domain.sophont.humaniti import DARMINE, HUMANITI, VILANI
from tests.character.helpers import MOCK_WORLD_2

_IMPERIAL_WORLD = MOCK_WORLD_2  # allegiance 'ImDd'
_NON_IMPERIAL_WORLD = MOCK_WORLD_2.model_copy(update={'allegiance': 'DaCf'})


class TestVilaniAvailability:
    def test_available_on_imperial_world(self):
        assert VILANI.available_at(_IMPERIAL_WORLD) is True

    def test_not_available_outside_imperium(self):
        assert VILANI.available_at(_NON_IMPERIAL_WORLD) is False


_DARMINE_WORLD = MOCK_WORLD_2.model_copy(update={'remarks': 'Ni Darm5'})
_DARMINE_WORLD_NAMED = MOCK_WORLD_2.model_copy(update={'remarks': 'Hi In (Darmine)'})
_NON_DARMINE_WORLD = MOCK_WORLD_2  # remarks: 'Ri Pa Ph An Cp (Spinward Marches) Sa'


class TestDarmineAvailability:
    def test_available_on_world_with_darm_remark(self):
        assert DARMINE.available_at(_DARMINE_WORLD) is True

    def test_available_on_world_with_parenthesized_darmine(self):
        assert DARMINE.available_at(_DARMINE_WORLD_NAMED) is True

    def test_not_available_on_world_without_darm_remark(self):
        assert DARMINE.available_at(_NON_DARMINE_WORLD) is False


class TestHumanitiAvailability:
    def test_available_on_imperial_world(self):
        assert HUMANITI.available_at(_IMPERIAL_WORLD) is True

    def test_available_outside_imperium(self):
        assert HUMANITI.available_at(_NON_IMPERIAL_WORLD) is True
