"""Approval snapshots for core-book military academy precareer flows."""

import pytest

from ceres.character.domain.precareer.military_academy import (
    ArmyAcademyPreCareer,
    MarineAcademyPreCareer,
    NavyAcademyPreCareer,
)
from ceres.character.domain.skills import Admin
from ceres.character.domain.sophont import HUMANITI
from tests.approval.character.helpers import (
    CharacterSession,
    background_skills_form,
    precareer_entry_form,
    roll_form,
    ucp_form,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD

_ext = AnnotatedJSONSnapshotExtension


def _base_session() -> CharacterSession:
    """UCP 778827: STR=7 DEX=7 END=8 INT=8 EDU=2 SOC=7. EDU=2 → DM=-2 → 1 background skill."""
    session = CharacterSession()
    session.start(HUMANITI, MOCK_WORLD)
    session.submit(ucp_form('778827'))
    session.submit(background_skills_form(Admin()))
    return session


def _pending_summary(projection) -> list[dict]:
    result = []
    for p in projection.pending_inputs:
        item: dict = {'type': type(p).__name__, 'kind': p.kind}
        if hasattr(p, 'level'):
            item['level'] = p.level
        if hasattr(p, 'options'):
            item['option_count'] = len(p.options)
            item['option_types'] = sorted({type(o).__name__ for o in p.options})
        result.append(item)
    return result


def _snap(projection) -> AnnotatedSnapshot:
    return AnnotatedSnapshot(
        {
            'summary': projection.summary.model_dump(mode='json'),
            'pending_inputs': _pending_summary(projection),
        }
    )


# ── Army Academy ──────────────────────────────────────────────────────────────


@pytest.mark.approval
def test_army_academy_graduation(snapshot):
    """Successful graduation: age 22, EDU+1, Army service skills granted at entry, auto-qualifies Army."""
    session = _base_session()
    session.submit(precareer_entry_form(ArmyAcademyPreCareer, roll=8))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(8))  # graduation
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_army_academy_honours_graduation(snapshot):
    """Honours graduation (roll >= 11): adds SOC+1 on top of normal benefits."""
    session = _base_session()
    session.submit(precareer_entry_form(ArmyAcademyPreCareer, roll=8))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(11))  # graduation with honours
    assert _snap(session.projection) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_army_academy_failed_graduation(snapshot):
    """Roll > 2 but below target: no EDU+1, character still auto-qualifies Army."""
    session = _base_session()
    session.submit(precareer_entry_form(ArmyAcademyPreCareer, roll=8))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(3))  # graduation fails
    assert _snap(session.projection) == snapshot(extension_class=_ext)


# ── Marine Academy ────────────────────────────────────────────────────────────


@pytest.mark.approval
def test_marine_academy_graduation(snapshot):
    """Successful graduation: age 22, EDU+1, Marine service skills, auto-qualifies Marines."""
    session = _base_session()
    session.submit(precareer_entry_form(MarineAcademyPreCareer, roll=8))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(8))  # graduation
    assert _snap(session.projection) == snapshot(extension_class=_ext)


# ── Navy Academy ──────────────────────────────────────────────────────────────


@pytest.mark.approval
def test_navy_academy_graduation(snapshot):
    """Successful graduation: age 22, EDU+1, Navy service skills, auto-qualifies Navy."""
    session = _base_session()
    session.submit(precareer_entry_form(NavyAcademyPreCareer, roll=8))
    session.submit(roll_form(5))  # precareer event
    session.submit(roll_form(8))  # graduation
    assert _snap(session.projection) == snapshot(extension_class=_ext)
