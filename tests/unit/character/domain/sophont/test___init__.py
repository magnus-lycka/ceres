from unittest.mock import MagicMock

from ceres.character.domain.sophont import (
    SOPHONT_NAMES,
    SOPHONTS,
    available_sophont_names,
    get_sophont,
)
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

_IMPERIAL = MOCK_WORLD_2
_NON_IMPERIAL = MOCK_WORLD_2.model_copy(update={'allegiance': 'DaCf'})


def _world(allegiance: str = 'ImDd', remarks: str = '') -> MagicMock:
    w = MagicMock()
    w.allegiance = allegiance
    w.remarks = remarks
    return w


def test_sophonts_list_is_not_empty():
    assert len(SOPHONTS) > 0


def test_sophont_names_matches_sophonts():
    assert [s.name for s in SOPHONTS] == SOPHONT_NAMES


def test_humaniti_is_in_sophonts():
    assert HUMANITI in SOPHONTS


def test_get_sophont_returns_correct_sophont():
    result = get_sophont('Vilani')
    assert result is VILANI


def test_get_sophont_returns_none_for_unknown():
    assert get_sophont('Zhodani') is None


def test_available_sophont_names_includes_humaniti_everywhere():
    names = available_sophont_names(_world(allegiance='NaXX'))
    assert 'Humaniti' in names


def test_available_sophont_names_includes_vilani_in_imperium():
    names = available_sophont_names(_world(allegiance='ImDd'))
    assert 'Vilani' in names


def test_available_sophont_names_excludes_vilani_outside_imperium():
    names = available_sophont_names(_world(allegiance='NaXX'))
    assert 'Vilani' not in names


def test_available_sophont_names_includes_remarks_sophont():
    names = available_sophont_names(_world(allegiance='NaXX', remarks='Ag Ni Darm'))
    assert 'Darmine' in names


# ── Sophont.available_at() and full availability matrix ───────────────────────


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
