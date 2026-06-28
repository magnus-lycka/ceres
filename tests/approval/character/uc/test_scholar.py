"""Usecase approval snapshots for complex Scholar event scenarios.

These tests drive a Scholar through multi-step event sequences and snapshot
the full character summary at the natural resolution point. They verify both
that the expected consequences occurred and that nothing unexpected changed.

Scenarios covered:
- Event 3 accept: research against conscience (skills, enemy, extra benefit roll)
- Event 3 decline: no consequences
- Mishap 5 give up: career ends, age increments, muster-out roll lost
"""

import pytest

from ceres.character.domain.career.scholar import (
    ScholarEvent3Accept,
    ScholarEvent3Decline,
    ScholarMishap5GiveUp,
)
from ceres.character.domain.skills import (
    Admin,
    Athletics,
    Carouse,
    Drive,
    Level,
    LifeScience,
    Medic,
    SpaceScience,
)
from ceres.character.domain.sophont import VILANI
from tests.approval.character.helpers import (
    CharacterSession,
    background_skills_form,
    career_entry_form,
    choice_form,
    connection_name_form,
    connections_form,
    roll_form,
    skill_form,
    ucp_form,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


def _session_at_event_3_choice() -> CharacterSession:
    session = CharacterSession()
    session.start(VILANI, MOCK_WORLD)
    session.submit(ucp_form('7869A5'))
    session.submit(background_skills_form(Admin(), Athletics(), Carouse(), Medic()))
    session.submit(career_entry_form('Scholar', 'Field Researcher', 5))
    session.submit(skill_form(Drive()))  # first PendingInitialTrainingChoice
    session.submit(skill_form(SpaceScience()))  # second PendingInitialTrainingChoice
    session.submit(roll_form(7))  # survive (EDU 6+, EDU=10, DM+2, 7+2=9 ≥ 6)
    session.submit(roll_form(3))  # term_event → event 3 choice
    return session


def _session_at_mishap_5_choice() -> CharacterSession:
    session = CharacterSession()
    session.start(VILANI, MOCK_WORLD)
    session.submit(ucp_form('7869A5'))
    session.submit(background_skills_form(Admin(), Athletics(), Carouse(), Medic()))
    session.submit(career_entry_form('Scholar', 'Field Researcher', 5))
    session.submit(skill_form(Drive()))  # first PendingInitialTrainingChoice
    session.submit(skill_form(SpaceScience()))  # second PendingInitialTrainingChoice
    session.submit(roll_form(3))  # survive fail (EDU 6+, DM+2, 3+2=5 < 6)
    session.submit(roll_form(5))  # mishap 5 → queues PendingChoices (mishap 5 options)
    return session


@pytest.mark.approval
def test_scholar_event_3_accept(snapshot):
    """Accept research against conscience: 2 science skills, D3=1 enemy, extra benefit roll."""
    session = _session_at_event_3_choice()
    session.submit(choice_form(ScholarEvent3Accept))
    session.submit(connections_form(1))  # PendingConnectionsRoll (enemy)
    session.submit(skill_form(SpaceScience(planetology=Level(value=1))))  # first career skill pick
    session.submit(skill_form(LifeScience(biology=Level(value=1))))  # second career skill pick
    session.submit(connection_name_form())  # PendingConnectionName
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scholar_event_3_decline(snapshot):
    """Decline: nothing extra happens — summary is unchanged from pre-event state."""
    session = _session_at_event_3_choice()
    session.submit(choice_form(ScholarEvent3Decline))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scholar_mishap_5_give_up(snapshot):
    """Give up after sabotaged work: career ends, age +4, one muster-out roll lost."""
    session = _session_at_mishap_5_choice()
    session.submit(choice_form(ScholarMishap5GiveUp))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
