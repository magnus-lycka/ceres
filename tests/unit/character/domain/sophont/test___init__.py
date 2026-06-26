from unittest.mock import MagicMock

from ceres.character.domain.sophont import (
    SOPHONT_NAMES,
    SOPHONTS,
    available_sophont_names,
    get_sophont,
)
from ceres.character.domain.sophont.humaniti import HUMANITI, VILANI


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
