"""Approval snapshots for CharacterSummary computed properties and diff."""

import pytest

from ceres.character.domain.career import CITIZEN, PSION, SCOUT
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.character_state import CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Level
from ceres.character.domain.sophont import HUMANITI
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


def _summary(**kwargs) -> CharacterSummary:
    kwargs.setdefault('name', 'Test')
    kwargs.setdefault('sophont', HUMANITI)
    kwargs.setdefault('homeworld', MOCK_WORLD)
    return CharacterSummary(**kwargs)


def _snap(summary: CharacterSummary) -> AnnotatedSnapshot:
    data = summary.model_dump(mode='json')
    data['_ucp'] = summary.ucp
    data['_rank_title'] = list(summary.rank_title)
    data['_latest_career'] = summary.latest_career.name if summary.latest_career else None
    return AnnotatedSnapshot(data)


@pytest.mark.approval
def test_ucp_encoding(snapshot):
    """UCP uses sophont stat order and eHex for values above 9."""
    summary = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        characteristics={
            Chars.STR: 8,
            Chars.DEX: 9,
            Chars.END: 10,
            Chars.INT: 6,
            Chars.EDU: 7,
            Chars.SOC: 11,
        },
    )
    assert _snap(summary) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_ucp_absent_when_incomplete(snapshot):
    """UCP is None until every UCP characteristic is present."""
    summary = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        characteristics={Chars.STR: 8},
    )
    assert _snap(summary) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_latest_career_prefers_current_over_last(snapshot):
    """latest_career returns the current career term career, not last_career."""
    citizen_assignment = CITIZEN.assignment('Corporate')
    assert citizen_assignment is not None
    summary = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        terms=[CareerTerm(career=CITIZEN, assignment=citizen_assignment)],
        last_career=SCOUT,
    )
    assert _snap(summary) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_latest_career_falls_back_to_last_career(snapshot):
    """latest_career returns last_career when no current career terms are present."""
    summary = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        last_career=SCOUT,
    )
    assert _snap(summary) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_rank_title_retained_from_prior_rank(snapshot):
    """rank_title retains the title from the most recently titled rank level."""
    psion = PSION
    adept = psion.assignment('Adept')
    assert adept is not None
    summary = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        rank=2,
        terms=[CareerTerm(career=psion, assignment=adept, rank=2)],
    )
    assert _snap(summary) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_diff_empty_when_unchanged(snapshot):
    s = _summary(characteristics={}, skills=[])
    assert AnnotatedSnapshot({'diff': s.diff(s)}) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_diff_new_narrative_entry(snapshot):
    before = _summary(narrative=['Term 1'])
    after = _summary(narrative=['Term 1', 'Survived the storm'])
    assert AnnotatedSnapshot({'diff': before.diff(after)}) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_diff_characteristic_change(snapshot):
    before = _summary(characteristics={Chars.STR: 7, Chars.DEX: 8})
    after = _summary(characteristics={Chars.STR: 8, Chars.DEX: 8})
    assert AnnotatedSnapshot({'diff': before.diff(after)}) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_diff_newly_gained_skill(snapshot):
    before = _summary()
    after = _summary(skills=[Admin()])
    assert AnnotatedSnapshot({'diff': before.diff(after)}) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_diff_skill_level_increase(snapshot):
    before = _summary(skills=[Admin()])
    after = _summary(skills=[Admin(level=Level(value=1))])
    assert AnnotatedSnapshot({'diff': before.diff(after)}) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_diff_rank_change(snapshot):
    before = _summary(rank=0)
    after = _summary(rank=1)
    assert AnnotatedSnapshot({'diff': before.diff(after)}) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_diff_cash_change(snapshot):
    before = _summary(cash=0)
    after = _summary(cash=5000)
    assert AnnotatedSnapshot({'diff': before.diff(after)}) == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
