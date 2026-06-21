"""Kasimir Yuen — Vilani Scout Courier, 2 terms, no advancement, mustered out."""

from types import SimpleNamespace

import pytest

from ceres.character.domain.benefits import SCOUT_SHIP
from ceres.character.domain.career import SCOUT
from ceres.character.domain.career.career_events import (
    AdvancementHandler,
    AssignmentChangeChoiceHandler,
    CareerEntryHandler,
    MusterOutHandler,
    SkillChoiceHandler,
    SkillTableHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.character_start import (
    BackgroundSkillsHandler,
    CharacterStartedHandler,
    FinishCreationHandler,
    UcpHandler,
)
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, Level, Pilot
from ceres.character.domain.sophont import VILANI
from ceres.character.domain.spec import NpcSpec, spec_from_summary
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
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
    started = Event(
        handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Kasimir Yuen')
    )
    ucp = Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(
        fulfills=(ucp.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    career = Event(
        fulfills=(background.id, 0),
        handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
    )
    survive_1 = Event(fulfills=(career.id, 0), handler=SurviveHandler(roll=7))
    event_1 = Event(fulfills=(survive_1.id, 0), handler=TermEventHandler(roll=5))
    advancement_1 = Event(fulfills=(event_1.id, 0), handler=AdvancementHandler(roll=5))
    reenlist = Event(fulfills=(advancement_1.id, 0), handler=AssignmentChangeChoiceHandler(choice='same'))
    skill_table = Event(fulfills=(reenlist.id, 0), handler=SkillTableHandler(table='service_skills', roll=1))
    skill_choice = Event(
        fulfills=(skill_table.id, 0),
        handler=SkillChoiceHandler(skill=Pilot(small_craft=Level(value=1))),
    )
    survive_2 = Event(fulfills=(skill_choice.id, 0), handler=SurviveHandler(roll=7))
    event_2 = Event(fulfills=(survive_2.id, 0), handler=TermEventHandler(roll=5))
    advancement_2 = Event(fulfills=(event_2.id, 0), handler=AdvancementHandler(roll=5))
    muster_out = Event(fulfills=(advancement_2.id, 0), handler=AssignmentChangeChoiceHandler(choice='muster_out'))
    benefit = Event(fulfills=(muster_out.id, 0), handler=MusterOutHandler(table='benefits', roll=6))
    cash = Event(fulfills=(benefit.id, 0), handler=MusterOutHandler(table='cash', roll=1))
    return [
        started,
        ucp,
        background,
        # Term 1: qualify Scout Courier, survive, event 5 (benefit_dm), advancement fails, reenlist same
        career,
        survive_1,
        event_1,  # benefit_dm +1 to muster out roll
        advancement_1,  # EDU 9+ with DM+1 → 6, fails
        reenlist,
        # Term 2: service skill roll (Pilot, specialised → choose small_craft), survive, event 5, advancement fails
        skill_table,  # Pilot → choice pending
        skill_choice,  # → small_craft 1
        survive_2,
        event_2,  # benefit_dm +1 to muster out roll
        advancement_2,  # fails
        muster_out,
        # Muster out: 2 rolls (term_count=2, rank=0), sequential
        benefit,  # scout_ship
        cash,  # Cr20,000
        Event(fulfills=(cash.id, 0), handler=FinishCreationHandler()),
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
