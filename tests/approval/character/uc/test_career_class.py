"""Approval snapshots verifying career identity (CareerData objects) survives the event loop."""

import pytest

from ceres.character.domain.career import ARMY
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Athletics, Drive, Electronics
from ceres.character.domain.sophont import VILANI
from tests.approval.character.helpers import (
    CharacterSession,
    background_skills_form,
    career_entry_form,
    keep_homeworld_form,
    roll_form,
    ucp_form,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


def _session() -> CharacterSession:
    """INT=9 EDU=10 → 4 background skills; SOC=5 so Noble/similar needs high roll."""
    session = CharacterSession()
    session.start(VILANI, MOCK_WORLD)
    session.submit(ucp_form('7869A5'))
    session.submit(background_skills_form(Admin(), Athletics(), Drive(), Electronics()))
    return session


@pytest.mark.approval
def test_scout_career_after_entry(snapshot):
    """current_career and career_terms[0].career are set correctly after joining Scout."""
    session = _session()
    session.submit(career_entry_form('Scout', 'Courier', 7))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scout_career_persists_after_survive(snapshot):
    """current_career remains set after a successful survival roll."""
    session = _session()
    session.submit(career_entry_form('Scout', 'Courier', 7))
    session.submit(keep_homeworld_form())  # PendingHomeworldChangeOffered (MOCK_WORLD has Scout base)
    session.submit(roll_form(8))  # survive
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scout_career_persists_after_full_term(snapshot):
    """current_career is intact after survive + term event + advancement."""
    session = _session()
    session.submit(career_entry_form('Scout', 'Courier', 7))
    session.submit(keep_homeworld_form())
    session.submit(roll_form(8))  # survive
    session.submit(roll_form(5))  # term_event
    session.submit(roll_form(9))  # advancement
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_army_can_attempt_commission_blocked_after_two_terms(snapshot):
    """commission is blocked when SOC is too low and two terms have elapsed."""
    infantry = ARMY.assignment('Infantry')
    assert infantry is not None
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='Test',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.SOC: 7},
            terms=[
                CareerTerm(career=ARMY, assignment=infantry),
                CareerTerm(career=ARMY, assignment=infantry),
            ],
        ),
    )
    snap = AnnotatedSnapshot(
        {
            'can_attempt_commission': ARMY.can_attempt_commission(proj),
            **proj.summary.model_dump(mode='json'),
        }
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
