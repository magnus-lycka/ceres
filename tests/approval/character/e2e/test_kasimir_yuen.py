"""Kasimir Yuen — Vilani Scout Courier, 2 terms, no advancement, mustered out."""

import pytest

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
from ceres.character.domain.spec import StatBlockSpec, spec_from_summary
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


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
        career,
        survive_1,
        event_1,
        advancement_1,
        reenlist,
        skill_table,
        skill_choice,
        survive_2,
        event_2,
        advancement_2,
        muster_out,
        benefit,
        cash,
        Event(fulfills=(cash.id, 0), handler=FinishCreationHandler()),
    ]


def build_kasimir_yuen() -> StatBlockSpec:
    """2-term Scout Courier, Vilani. Mustered out with a Scout Ship and Cr20,000."""
    from ceres.character.notes import generate_notes

    summary = replay(1, _events()).summary
    return spec_from_summary(summary, notes=generate_notes(summary))


def test_no_pending_inputs_after_finish_creation():
    assert replay(1, _events()).pending_inputs == []


@pytest.mark.approval
def test_kasimir_yuen(snapshot):
    snap = AnnotatedSnapshot(build_kasimir_yuen().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
