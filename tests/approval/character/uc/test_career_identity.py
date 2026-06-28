"""Approval snapshots for career assignment identity and current-assignment tracking."""

import pytest

from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive
from ceres.character.domain.sophont import VILANI
from tests.approval.character.helpers import (
    CharacterSession,
    background_skills_form,
    career_entry_form,
    keep_homeworld_form,
    roll_form,
    skill_table_form,
    ucp_form,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


def _session(ucp: str = '7869A5') -> CharacterSession:
    session = CharacterSession()
    session.start(VILANI, MOCK_WORLD)
    session.submit(ucp_form(ucp))
    session.submit(background_skills_form(Admin(), Athletics(), Carouse(), Drive()))
    return session


@pytest.mark.approval
def test_scout_courier_assignment_after_entry(snapshot):
    session = _session()
    session.submit(career_entry_form('Scout', 'Courier', 7))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scout_surveyor_assignment_after_entry(snapshot):
    session = _session()
    session.submit(career_entry_form('Scout', 'Surveyor', 7))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scout_explorer_assignment_after_entry(snapshot):
    session = _session()
    session.submit(career_entry_form('Scout', 'Explorer', 7))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_noble_administrator_assignment_after_entry(snapshot):
    # Noble requires SOC 10+; UCP '7869AB' gives SOC=11 (DM+1) so roll=9 is enough.
    session = _session(ucp='7869AB')
    session.submit(career_entry_form('Noble', 'Administrator', 9))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_noble_dilettante_assignment_after_entry(snapshot):
    session = _session(ucp='7869AB')
    session.submit(career_entry_form('Noble', 'Dilettante', 9))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_assignment_change_updates_current_assignment(snapshot):
    """Switching assignment mid-career updates current_assignment."""
    session = _session()
    session.submit(career_entry_form('Scout', 'Courier', 7))
    session.submit(keep_homeworld_form())  # PendingHomeworldChangeOffered (MOCK_WORLD has Scout base)
    session.submit(roll_form(7))  # survive
    session.submit(roll_form(5))  # term_event
    session.submit(roll_form(9))  # advancement (success: DEX 8+, DEX=8, DM+0, 9 ≥ 8)
    session.submit(skill_table_form('service_skills', 1))  # PendingSkillTable queued before assignment change
    session.submit({'choice': 'switch'})  # PendingAssignmentChangeChoice → switch
    session.submit({'assignment': 'Surveyor', 'roll': '5'})  # PendingSwitchAssignment
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scout_current_career_after_normal_advancement(snapshot):
    """current_career remains Scout after survive + term_event + advancement."""
    session = _session()
    session.submit(career_entry_form('Scout', 'Courier', 7))
    session.submit(keep_homeworld_form())
    session.submit(roll_form(8))  # survive
    session.submit(roll_form(5))  # term_event
    session.submit(roll_form(9))  # advancement
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
