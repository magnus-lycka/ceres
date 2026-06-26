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
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver


def _driver_at_event_3_choice() -> CharacterDriver:
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('7869A5')
    d.background_skills([Admin(), Athletics(), Carouse(), Medic()])
    d.career('Scholar', 'Field Researcher', roll=5)
    d.initial_training(Drive())
    d.initial_training(SpaceScience())
    d.survive(7)
    d.term_event(3)
    return d


def _driver_at_mishap_5_choice() -> CharacterDriver:
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('7869A5')
    d.background_skills([Admin(), Athletics(), Carouse(), Medic()])
    d.career('Scholar', 'Field Researcher', roll=5)
    d.initial_training(Drive())
    d.initial_training(SpaceScience())
    d.survive(3)
    d.mishap(5)
    return d


@pytest.mark.approval
def test_scholar_event_3_accept(snapshot):
    """Accept research against conscience: 2 science skills, D3=1 enemy, extra benefit roll."""
    d = _driver_at_event_3_choice()
    d.career_choice(ScholarEvent3Accept)
    d.connections_roll(1)
    d.choose_career_skill(SpaceScience(planetology=Level(value=1)))
    d.choose_career_skill(LifeScience(biology=Level(value=1)))
    d.name_connection()
    snap = AnnotatedSnapshot(d.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scholar_event_3_decline(snapshot):
    """Decline: nothing extra happens — summary is unchanged from pre-event state."""
    d = _driver_at_event_3_choice()
    d.career_choice(ScholarEvent3Decline)
    snap = AnnotatedSnapshot(d.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scholar_mishap_5_give_up(snapshot):
    """Give up after sabotaged work: career ends, age +4, one muster-out roll lost."""
    d = _driver_at_mishap_5_choice()
    d.career_choice(ScholarMishap5GiveUp)
    snap = AnnotatedSnapshot(d.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
