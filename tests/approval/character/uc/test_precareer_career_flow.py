"""Use-case approval snapshots for mixed precareer/career term flows.

Each test drives a character through a complete sequence of precareers and
careers and snapshots the full summary at the natural resolution point. They
verify both that the expected terms, skills, and characteristics are present
and that nothing unexpected changed.

Scenarios:
- Spacer Community precareer → Scholar career
- Scout career → University precareer → Citizen career
- Spacer Community precareer → Citizen career → University precareer → Citizen career
"""

import pytest

from ceres.character.domain.precareer.spacer_community import SpacerCommunityPreCareer
from ceres.character.domain.precareer.university import UniversityPreCareer
from ceres.character.domain.skills import Admin, Astrogation, Athletics, Carouse, Electronics, Engineer
from ceres.character.domain.sophont import HUMANITI
from tests.approval.character.helpers import (
    CharacterSession,
    background_skills_form,
    career_entry_form,
    keep_homeworld_form,
    muster_out_form,
    precareer_entry_form,
    reenlist_form,
    roll_form,
    skill_form,
    ucp_form,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


def _session() -> CharacterSession:
    """EDU=2 → 1 background skill."""
    session = CharacterSession()
    session.start(HUMANITI, MOCK_WORLD)
    session.submit(ucp_form('777727'))
    session.submit(background_skills_form(Admin()))
    return session


def _complete_spacer_precareer(session: CharacterSession, *, entry_roll: int = 7) -> None:
    """Drive Spacer Community from entry through graduation (not honours).

    VaccSuit 1 is auto-granted on entry. Two level-0 skill picks follow.
    Graduation at roll=9 yields 3 more picks (2 level-0, 1 level-1).
    """
    session.submit(precareer_entry_form(SpacerCommunityPreCareer, entry_roll))
    session.submit(skill_form(Astrogation()))
    session.submit(skill_form(Electronics()))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(9))  # graduation
    session.submit(skill_form(Astrogation()))
    session.submit(skill_form(Electronics()))
    session.submit(skill_form(Engineer()))  # level-1 pick: increment_skill → Engineer 1


def _complete_university_precareer(session: CharacterSession, *, entry_roll: int = 12) -> None:
    """Drive University from entry through graduation (not honours).

    Two skill picks are stored in the term and boosted on graduation; no extra picks.
    """
    session.submit(precareer_entry_form(UniversityPreCareer, entry_roll))
    session.submit(skill_form(Admin()))  # level-0 entry pick
    session.submit(skill_form(Astrogation()))  # level-1 entry pick
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(7))  # graduation


def _complete_citizen_term(session: CharacterSession, *, assignment: str = 'Corporate') -> None:
    """Drive one complete Citizen term ending in muster out.

    First career auto-grants all service skills; subsequent entries queue
    PendingInitialTrainingChoice which is handled if present.
    """
    session.submit(career_entry_form('Citizen', assignment, roll=7))
    if session.projection.pending_inputs[0].kind == 'initial_training_choice':
        session.submit(skill_form(Admin()))
    session.submit(roll_form(7))  # survive
    session.submit(roll_form(5))  # term_event
    session.submit(roll_form(3))  # advancement fail
    session.submit(reenlist_form(False))
    session.submit(muster_out_form('cash', 1))


def _complete_scout_term(session: CharacterSession, *, assignment: str = 'Courier') -> None:
    """Drive one complete Scout term ending in muster out.

    Scout auto-grants all 6 service skills on entry.
    MOCK_WORLD has an Imperial Scout Base ('S' in Bases), so PendingHomeworldChangeOffered
    is queued after entry — resolved here with keep_homeworld_form().
    """
    session.submit(career_entry_form('Scout', assignment, roll=7))
    session.submit(keep_homeworld_form())  # PendingHomeworldChangeOffered
    session.submit(roll_form(8))  # survive
    session.submit(roll_form(5))  # term_event
    session.submit(roll_form(3))  # advancement fail (DEX 8+, DEX=7, DM+0, 3 < 8)
    session.submit(reenlist_form(False))
    session.submit(muster_out_form('cash', 1))


@pytest.mark.approval
def test_spacer_then_scholar(snapshot):
    """Spacer Community precareer (term 1) then Scholar career (term 2)."""
    session = _session()
    _complete_spacer_precareer(session)
    session.submit(career_entry_form('Scholar', 'Field Researcher', roll=7))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_scout_then_university_then_citizen(snapshot):
    """Scout career (term 1) then University precareer (term 2) then Citizen career (term 3)."""
    session = CharacterSession()
    session.start(HUMANITI, MOCK_WORLD)
    session.submit(ucp_form('777777'))  # EDU=7: 3 background skills
    session.submit(background_skills_form(Admin(), Athletics(), Carouse()))
    _complete_scout_term(session)
    _complete_university_precareer(session)  # roll=12: passes at term 2 with any EDU
    session.submit(career_entry_form('Citizen', 'Corporate', roll=7))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_spacer_citizen_university_citizen(snapshot):
    """Spacer precareer (1) then Citizen (2) then University precareer (3) then Citizen (4)."""
    session = _session()
    _complete_spacer_precareer(session)
    _complete_citizen_term(session, assignment='Corporate')
    _complete_university_precareer(session)  # roll=12: passes at term 3 with EDU=2 (DM-2: 12-2-2=8≥6)
    # 'Worker' avoids same-assignment re-entry restriction after voluntary departure
    session.submit(career_entry_form('Citizen', 'Worker', roll=7))
    snap = AnnotatedSnapshot(session.projection.summary.model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
