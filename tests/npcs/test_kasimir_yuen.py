"""Kasimir Yuen — Vilani Scout Courier, 2 terms, no advancement, mustered out."""

from types import SimpleNamespace

import pytest

from ceres.character.benefits import SCOUT_SHIP
from ceres.character.events import (
    AdvancementEvent,
    AssignmentChangeChoiceEvent,
    BackgroundSkillsEvent,
    CareerEvent,
    CharacterStartedEvent,
    FinishCreationEvent,
    MusterOutEvent,
    SkillChoiceEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.mechanism.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, Level, Pilot
from ceres.character.sophonts import VILANI
from ceres.character.spec import NpcSpec, spec_from_summary
from tests.character.helpers import MOCK_WORLD

_expected = SimpleNamespace(
    name='Kasimir Yuen',
    sophont='Vilani',
    ucp='7869A5',
    age=26,
    career='Scout',
    assignment='Courier',
    rank=0,
    terms=2,
    # Term 2 skill table: service_skills roll 1 (Pilot) → increments small_craft 0→1
    pilot_small_craft=1,
    cash=20_000,
    equipment=[SCOUT_SHIP],
)


def _events() -> list:
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Kasimir Yuen'),
        UcpEvent(id=2, fulfills=(1, 0), ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills=(2, 0), skills=[Admin(), Athletics(), Carouse(), Drive()]),
        # Term 1: qualify Scout Courier, survive, event 5 (benefit_dm), advancement fails, reenlist same
        CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills=(4, 0), roll=7),
        TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # benefit_dm +1 to muster out roll
        AdvancementEvent(id=7, fulfills=(6, 0), roll=5),  # EDU 9+ with DM+1 → 6, fails
        AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='same'),
        # Term 2: service skill roll (Pilot, specialised → choose small_craft), survive, event 5, advancement fails
        SkillTableEvent(id=9, fulfills=(8, 0), table='service_skills', roll=1),  # Pilot → choice pending
        SkillChoiceEvent(id=10, fulfills=(9, 0), skill=Pilot(small_craft=Level(value=1))),  # → small_craft 1
        SurviveEvent(id=11, fulfills=(10, 0), roll=7),
        TermEventEvent(id=12, fulfills=(11, 0), roll=5),  # benefit_dm +1 to muster out roll
        AdvancementEvent(id=13, fulfills=(12, 0), roll=5),  # fails
        AssignmentChangeChoiceEvent(id=14, fulfills=(13, 0), choice='muster_out'),
        # Muster out: 2 rolls (term_count=2, rank=0)
        MusterOutEvent(id=15, fulfills=(14, 0), table='benefits', roll=6),  # scout_ship
        MusterOutEvent(id=16, fulfills=(14, 1), table='cash', roll=1),  # Cr20,000
        FinishCreationEvent(id=17, fulfills=(16, 0)),
    ]


def build_kasimir_spec() -> NpcSpec:
    """2-term Scout Courier, Vilani. Mustered out with a Scout Ship."""
    from ceres.character.notes import generate_notes

    summary = replay(1, _events()).summary
    return spec_from_summary(summary, notes=generate_notes(summary))


@pytest.fixture(scope='module')
def kasimir_spec():
    return build_kasimir_spec()


def test_no_pending_inputs_after_finish_creation():
    assert replay(1, _events()).pending_inputs == []


def test_name(kasimir_spec):
    assert kasimir_spec.name == _expected.name


def test_sophont(kasimir_spec):
    assert kasimir_spec.sophont == _expected.sophont


def test_ucp(kasimir_spec):
    assert kasimir_spec.ucp == _expected.ucp


def test_age(kasimir_spec):
    assert kasimir_spec.age == _expected.age


def test_career_and_assignment(kasimir_spec):
    assert kasimir_spec.career == _expected.career
    assert kasimir_spec.assignment == _expected.assignment


def test_rank_and_terms(kasimir_spec):
    assert kasimir_spec.rank == _expected.rank
    assert kasimir_spec.terms == _expected.terms


def test_pilot_small_craft(kasimir_spec):
    pilot = next((s for s in kasimir_spec.skills if isinstance(s, Pilot)), None)
    assert pilot is not None
    assert pilot.small_craft.value == _expected.pilot_small_craft


def test_background_skills_at_level_0(kasimir_spec):
    admin = next((s for s in kasimir_spec.skills if isinstance(s, Admin)), None)
    assert admin is not None
    assert admin.level.value == 0


def test_cash(kasimir_spec):
    assert kasimir_spec.cash == _expected.cash


def test_equipment(kasimir_spec):
    assert kasimir_spec.equipment == _expected.equipment
