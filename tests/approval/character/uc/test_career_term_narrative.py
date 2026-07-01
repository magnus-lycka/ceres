"""Approval snapshots for career-term narrative fields: event, mishap, prison."""

import pytest

from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, GunCombat
from ceres.character.domain.sophont import VILANI
from tests.approval.character.helpers import (
    CharacterSession,
    background_skills_form,
    career_entry_form,
    roll_form,
    skill_form,
    ucp_form,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


def _session() -> CharacterSession:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5."""
    session = CharacterSession()
    session.start(VILANI, MOCK_WORLD)
    session.submit(ucp_form('7869A5'))
    session.submit(background_skills_form(Admin(), Athletics(), Carouse(), Drive()))
    return session


@pytest.mark.approval
def test_army_fresh_entry(snapshot):
    """event/mishap/prison are all None immediately after entering Army Support."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Army', 'Support', 5))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_army_term_with_event_5(snapshot):
    """Army event roll=5 sets the special-assignment narrative on the career term."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Army', 'Support', 5))
        session.submit(skill_form(GunCombat()))
        session.submit(roll_form(5))
        session.submit(roll_form(5))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_army_term_unknown_event_roll(snapshot):
    """An event roll with no matching table entry leaves the event field as None."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Army', 'Support', 5))
        session.submit(skill_form(GunCombat()))
        session.submit(roll_form(5))
        session.submit(roll_form(99))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_army_ejection_mishap_2(snapshot):
    """Army ejection mishap roll=2 sets the unit-slaughtered mishap narrative."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Army', 'Support', 5))
        session.submit(skill_form(GunCombat()))
        session.submit(roll_form(4))
        session.submit(roll_form(2))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_army_stay_in_career_mishap(snapshot):
    """Army event roll=2 (Disaster!) triggers stay-in-career mishap; mishap field stays None."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Army', 'Support', 5))
        session.submit(skill_form(GunCombat()))
        session.submit(roll_form(5))
        session.submit(roll_form(2))
        session.submit(roll_form(5))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_rogue_arrested_mishap_2(snapshot):
    """Rogue Thief mishap roll=2 (arrested) sets the prison narrative field."""
    session = _session()
    snap = AnnotatedSnapshot({})
    try:
        session.submit(career_entry_form('Rogue', 'Thief', 6))
        session.submit(roll_form(4))
        session.submit(roll_form(2))
        snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    finally:
        snap.annotate('session_log', session.log)
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
