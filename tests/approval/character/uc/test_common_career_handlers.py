"""Approval snapshots for shared career handlers (CommonMishap1)."""

import pytest

from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive
from ceres.character.domain.sophont import VILANI
from tests.approval.character.helpers import (
    CharacterSession,
    background_skills_form,
    career_entry_form,
    choice_form,
    double_injury_form,
    roll_form,
    ucp_form,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


def _session_at_mishap1() -> CharacterSession:
    """Character through Citizen Corporate term, survived with roll=2 (mishap 1 triggered)."""
    session = CharacterSession()
    session.start(VILANI, MOCK_WORLD)
    session.submit(ucp_form('7869A5'))
    session.submit(background_skills_form(Admin(), Athletics(), Carouse(), Drive()))
    session.submit(career_entry_form('Citizen', 'Corporate', 4))
    session.submit(roll_form(2))  # survive fail (END 6+, END=6, DM+0, 2 < 6)
    session.submit(roll_form(1))  # mishap 1 → queues PendingChoices with CommonMishap1 options
    return session


@pytest.mark.approval
def test_mishap1_severe_branch(snapshot):
    """Choosing severe injury: career ends immediately, injury table queued."""
    session = _session_at_mishap1()
    session.submit(choice_form(CommonMishap1Severe))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_mishap1_double_roll_branch_nearly_killed(snapshot):
    """Choosing double roll then rolling minimum (1,1): career ends, nearly-killed result queued."""
    session = _session_at_mishap1()
    session.submit(choice_form(CommonMishap1DoubleRoll))
    session.submit(double_injury_form(1, 1))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
