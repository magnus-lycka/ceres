"""Unit tests for the bulk NPC generation engine."""

import random

import pytest

from ceres.character.spec import NpcSpec
from ceres.character.store import SqliteCharacterBackend
from ceres.character.web.bulk import CohortParams, generate_cohort, generate_npc


def _backend() -> SqliteCharacterBackend:
    return SqliteCharacterBackend(':memory:')


def _scout_params(**overrides) -> CohortParams:
    defaults = {
        'career': 'Scout',
        'assignment': 'Courier',
        'sophont': 'Humaniti',
        'min_terms': 1,
        'max_terms': 2,
        'name_prefix': 'Scout',
    }
    defaults.update(overrides)
    return CohortParams(**defaults)


# ── generate_npc ──────────────────────────────────────────────────────────────


def test_generate_npc_returns_npc_spec():
    with _backend() as backend:
        spec = generate_npc(backend, _scout_params(), name='Aria', rng=random.Random(1))
    assert isinstance(spec, NpcSpec)


def test_generate_npc_career_matches_params():
    with _backend() as backend:
        spec = generate_npc(backend, _scout_params(), name='Aria', rng=random.Random(1))
    assert spec.career == 'Scout'


def test_generate_npc_sophont_matches_params():
    with _backend() as backend:
        spec = generate_npc(backend, _scout_params(), name='Aria', rng=random.Random(1))
    assert spec.sophont == 'Humaniti'


def test_generate_npc_name_matches_argument():
    with _backend() as backend:
        spec = generate_npc(backend, _scout_params(), name='Borin', rng=random.Random(1))
    assert spec.name == 'Borin'


def test_generate_npc_has_valid_ucp():
    with _backend() as backend:
        spec = generate_npc(backend, _scout_params(), name='Aria', rng=random.Random(2))
    assert len(spec.ucp) == 6
    assert all(c in '0123456789ABCDEF' for c in spec.ucp.upper())


def test_generate_npc_has_skills():
    with _backend() as backend:
        spec = generate_npc(backend, _scout_params(min_terms=2, max_terms=2), name='Aria', rng=random.Random(3))
    assert len(spec.skills) > 0


def test_generate_npc_terms_at_least_one():
    with _backend() as backend:
        spec = generate_npc(backend, _scout_params(min_terms=1, max_terms=3), name='Aria', rng=random.Random(4))
    assert spec.terms >= 1


def test_generate_npc_deterministic():
    params = _scout_params()
    with _backend() as b1:
        spec1 = generate_npc(b1, params, name='Test', rng=random.Random(42))
    with _backend() as b2:
        spec2 = generate_npc(b2, params, name='Test', rng=random.Random(42))
    assert spec1.ucp == spec2.ucp
    assert spec1.terms == spec2.terms


def test_generate_npc_different_seeds_may_differ():
    params = _scout_params()
    with _backend() as b1:
        generate_npc(b1, params, name='Test', rng=random.Random(1))
    with _backend() as b2:
        generate_npc(b2, params, name='Test', rng=random.Random(999))


def test_generate_npc_no_assignment_picks_randomly():
    params = _scout_params(assignment=None)
    with _backend() as backend:
        spec = generate_npc(backend, params, name='Test', rng=random.Random(5))
    assert spec.career == 'Scout'
    assert spec.assignment in ('Courier', 'Surveyor', 'Explorer')


# ── generate_cohort ───────────────────────────────────────────────────────────


def test_generate_cohort_returns_correct_count():
    with _backend() as backend:
        specs = generate_cohort(backend, _scout_params(), count=3, rng=random.Random(0))
    assert len(specs) == 3


def test_generate_cohort_empty():
    with _backend() as backend:
        specs = generate_cohort(backend, _scout_params(), count=0, rng=random.Random(0))
    assert specs == []


def test_generate_cohort_all_scout():
    with _backend() as backend:
        specs = generate_cohort(backend, _scout_params(), count=2, rng=random.Random(1))
    for spec in specs:
        assert spec.career == 'Scout'


def test_generate_cohort_unique_names():
    params = _scout_params(name_prefix='NPC')
    with _backend() as backend:
        specs = generate_cohort(backend, params, count=5, rng=random.Random(7))
    names = [s.name for s in specs]
    assert len(set(names)) == len(names)


def test_generate_cohort_deterministic():
    params = _scout_params(name_prefix='Test')
    with _backend() as b1:
        specs1 = generate_cohort(b1, params, count=3, rng=random.Random(99))
    with _backend() as b2:
        specs2 = generate_cohort(b2, params, count=3, rng=random.Random(99))
    assert [s.ucp for s in specs1] == [s.ucp for s in specs2]


@pytest.mark.slow
def test_generate_cohort_scholar():
    params = CohortParams(
        career='Scholar',
        assignment='Scientist',
        sophont='Humaniti',
        min_terms=1,
        max_terms=3,
        name_prefix='Doc',
    )
    with _backend() as backend:
        specs = generate_cohort(backend, params, count=3, rng=random.Random(10))
    assert len(specs) == 3
    for spec in specs:
        assert spec.career == 'Scholar'
