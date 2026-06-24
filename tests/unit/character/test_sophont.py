from ceres.character.domain.sophont import available_sophont_names
from ceres.character.domain.sophont.humaniti import (
    DARMINE,
    HUMANITI,
    LANCIANS,
    LIBERTS,
    MURRISSI,
    SWANFEI,
    URUNISHANI,
    VILANI,
    Sophont,
)
from tests.unit.character.helpers import MOCK_WORLD_2

_IMPERIAL = MOCK_WORLD_2  # allegiance 'ImDd'
_NON_IMPERIAL = MOCK_WORLD_2.model_copy(update={'allegiance': 'DaCf'})


class SophontAvailabilityTests:
    sophont: Sophont = Sophont(name='Base Class')
    true_worlds: tuple = ()
    false_worlds: tuple = ()

    def test_available_at_true_worlds(self):
        for world in self.true_worlds:
            assert self.sophont.available_at(world)

    def test_not_available_at_false_worlds(self):
        for world in self.false_worlds:
            assert not self.sophont.available_at(world)

    def test_in_available_sophont_names(self):
        for world in self.true_worlds:
            assert self.sophont.name in available_sophont_names(world)
        for world in self.false_worlds:
            assert self.sophont.name not in available_sophont_names(world)


class TestHumanitiAvailability(SophontAvailabilityTests):
    sophont = HUMANITI
    true_worlds = (_IMPERIAL, _NON_IMPERIAL)
    false_worlds = ()


class TestVilaniAvailability(SophontAvailabilityTests):
    sophont = VILANI
    true_worlds = (_IMPERIAL,)
    false_worlds = (_NON_IMPERIAL,)


class TestDarmineAvailability(SophontAvailabilityTests):
    sophont = DARMINE
    true_worlds = (
        MOCK_WORLD_2.model_copy(update={'remarks': 'Ni Darm5'}),
        MOCK_WORLD_2.model_copy(update={'remarks': 'Hi In (Darmine)'}),
    )
    false_worlds = (MOCK_WORLD_2,)


class TestLibertsAvailability(SophontAvailabilityTests):
    sophont = LIBERTS
    true_worlds = (
        MOCK_WORLD_2.model_copy(update={'remarks': 'Ni Libe3'}),
        MOCK_WORLD_2.model_copy(update={'remarks': 'Hi In (Liberts)'}),
    )
    false_worlds = (MOCK_WORLD_2,)


class TestMurrissiAvailability(SophontAvailabilityTests):
    sophont = MURRISSI
    true_worlds = (
        MOCK_WORLD_2.model_copy(update={'remarks': 'Ni MurrW'}),
        MOCK_WORLD_2.model_copy(update={'remarks': 'Hi In (Murrissi)'}),
    )
    false_worlds = (MOCK_WORLD_2,)


class TestUrunishaniAvailability(SophontAvailabilityTests):
    sophont = URUNISHANI
    true_worlds = (
        MOCK_WORLD_2.model_copy(update={'remarks': 'Ni Urun5'}),
        MOCK_WORLD_2.model_copy(update={'remarks': 'Hi In (Urunishani)'}),
    )
    false_worlds = (MOCK_WORLD_2,)


class TestSwanfeiAvailability(SophontAvailabilityTests):
    sophont = SWANFEI
    true_worlds = (
        MOCK_WORLD_2.model_copy(update={'remarks': 'Ni Swan3'}),
        MOCK_WORLD_2.model_copy(update={'remarks': 'Hi In (Swanfeh)'}),
    )
    false_worlds = (MOCK_WORLD_2,)


class TestLanciansAvailability(SophontAvailabilityTests):
    sophont = LANCIANS
    true_worlds = (
        MOCK_WORLD_2.model_copy(update={'remarks': 'Ni Lanc4'}),
        MOCK_WORLD_2.model_copy(update={'remarks': 'Hi In (Lancians)'}),
    )
    false_worlds = (MOCK_WORLD_2,)
