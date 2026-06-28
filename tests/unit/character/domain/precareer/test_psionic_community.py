"""Unit tests for psionic_community.py — PsionicCommunityPreCareer."""

import pytest

from ceres.character.domain.career.psion import Psion
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import Enemy, Rival
from ceres.character.domain.precareer.psionic_community import PsionicCommunityPreCareer
from ceres.character.domain.psionics import Psionics
from ceres.character.domain.skills import LifeScience
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD

_PSIONIC = PsionicCommunityPreCareer()


def _proj(with_psionics: bool = True) -> CharacterProjection:
    summary = CharacterSummary(
        name='T',
        sophont=VILANI,
        homeworld=MOCK_WORLD,
        characteristics={Chars.PSI: 9, Chars.INT: 8},
    )
    if with_psionics:
        summary.psionics = Psionics()
    return CharacterProjection(character_id=1, summary=summary)


def _event() -> Event:
    from ceres.character.domain.career.career_events import SurviveHandler

    return Event(handler=SurviveHandler(roll=5))


class TestPsionicCommunityData:
    def test_entry_is_psi_8_plus(self):
        assert _PSIONIC.entry.characteristic == Chars.PSI
        assert _PSIONIC.entry.target == 8

    def test_entry_dm_int_8_plus(self):
        assert _PSIONIC.entry_dms.get('INT_8+') == 1

    def test_graduation_is_psi_6_plus(self):
        assert _PSIONIC.graduation.characteristic == Chars.PSI
        assert _PSIONIC.graduation.target == 6

    def test_graduation_dm_int_8_plus(self):
        assert _PSIONIC.graduation_dms.get('INT_8+') == 1

    def test_honours_target(self):
        assert _PSIONIC.honours_target == 12


class TestPsionicCommunityIsAvailable:
    def test_available_when_psionics_present(self):
        proj = _proj(with_psionics=True)
        assert _PSIONIC.is_available(proj.summary) is True

    def test_not_available_without_psionics(self):
        proj = _proj(with_psionics=False)
        assert _PSIONIC.is_available(proj.summary) is False


class TestPsionicCommunityGraduation:
    def test_grants_psi_plus_1(self):
        proj = _proj()
        _PSIONIC.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.PSI] == 10

    def test_grants_life_science_psionicology_1(self):
        proj = _proj()
        _PSIONIC.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.skill_level(LifeScience, 0) == 1

    def test_auto_qualifies_for_psion(self):
        proj = _proj()
        _PSIONIC.make_term().apply_graduation(proj, _event(), honours=False)
        assert Psion in proj.auto_qualify_careers

    def test_gains_rival_without_honours(self):
        proj = _proj()
        _PSIONIC.make_term().apply_graduation(proj, _event(), honours=False)
        assert any(isinstance(c, Rival) for c in proj.summary.connections)

    def test_gains_enemy_with_honours(self):
        proj = _proj()
        _PSIONIC.make_term().apply_graduation(proj, _event(), honours=True)
        assert any(isinstance(c, Enemy) for c in proj.summary.connections)

    def test_raises_without_psionics(self):
        proj = _proj(with_psionics=False)
        with pytest.raises(ValueError, match='Psionic Strength'):
            _PSIONIC.make_term().apply_graduation(proj, _event(), honours=False)
