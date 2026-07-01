"""Approval snapshots for draft, commission, and qualification-DM flows."""

import pytest

from ceres.character.domain.career import ARMY
from ceres.character.domain.career.loader import load_careers
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, GunCombat
from ceres.character.domain.sophont import VILANI
from tests.approval.character.helpers import (
    CharacterSession,
    background_skills_form,
    career_entry_form,
    commission_form,
    draft_assignment_form,
    draft_form,
    roll_form,
    skill_form,
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
def test_draftable_careers(snapshot):
    """Careers that implement draft are enumerated correctly."""
    draft_careers = sorted(c.name for c in load_careers() if c.does_draft())
    snap = AnnotatedSnapshot({'draft_careers': draft_careers})
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_failed_qualification_leaves_no_current_career(snapshot):
    """Failing qualification clears current_career and queues a draft choice."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Merchant', 'Merchant Marine', 2))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_draft_alternative_sets_career_and_assignment(snapshot):
    """Taking the draft alternative (Drifter) directly sets current career and assignment."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Army', 'Infantry', 2))
        session.submit(draft_form('alternative', assignment='Barbarian'))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_draft_to_multi_assignment_career_waits_for_choice(snapshot):
    """Drafting to a multi-assignment career leaves current_career None pending assignment choice."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Merchant', 'Merchant Marine', 2))
        session.submit(draft_form('draft', roll=2))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_draft_assignment_choice_sets_assignment(snapshot):
    """Selecting an assignment after draft sets current_career and current_assignment."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Merchant', 'Merchant Marine', 2))
        session.submit(draft_form('draft', roll=2))
        session.submit(draft_assignment_form('Cavalry'))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_merchant_no_commission_before_advancement(snapshot):
    """Merchant does not offer commission; after term_event only PendingAdvancement queued."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Merchant', 'Merchant Marine', 8))
        session.submit(roll_form(8))
        session.submit(roll_form(9))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_army_commission_offered_after_survive_and_event(snapshot):
    """Army first term: commission choice is queued after survive + term_event."""
    session = _session(ucp='7869A9')
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Army', 'Infantry', 8))
        session.submit(skill_form(GunCombat()))
        session.submit(roll_form(8))
        session.submit(roll_form(9))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_successful_commission(snapshot):
    """Successful commission sets rank=1, grants Leadership, skips advancement."""
    session = _session(ucp='7869A9')
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Army', 'Infantry', 8))
        session.submit(skill_form(GunCombat()))
        session.submit(roll_form(8))
        session.submit(roll_form(9))
        session.submit(commission_form(attempt=True, roll=8))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_qualification_dm_consumed_on_career_entry(snapshot):
    """A pending_qualification_dm of +10 allows a roll of 0 to qualify, then DM resets to 0."""
    infantry = ARMY.assignment('Infantry')
    assert infantry is not None
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='Test',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.END: 7},
        ),
    )
    proj.pending_qualification_dm = 10
    ARMY.start_career(proj, infantry, event_id=6, qualification_roll=0)
    snap = AnnotatedSnapshot(
        {
            **proj.summary.model_dump(mode='json'),
            'pending_qualification_dm': proj.pending_qualification_dm,
        }
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
