from ceres.character.domain.career import CITIZEN, SCOUT
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.career.loader import load_careers
from ceres.character.domain.character_state import CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Level
from ceres.character.domain.sophont import HUMANITI
from tests.character.helpers import MOCK_WORLD


def _summary(**kwargs) -> CharacterSummary:
    kwargs.setdefault('name', 'Test')
    kwargs.setdefault('sophont', HUMANITI)
    kwargs.setdefault('homeworld', MOCK_WORLD)
    return CharacterSummary(**kwargs)


def test_ucp_uses_sophont_characteristic_order_and_ehex_codes() -> None:
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

    assert summary.ucp == '89A67B'


def test_ucp_is_absent_until_every_ucp_characteristic_exists() -> None:
    summary = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        characteristics={Chars.STR: 8},
    )

    assert summary.ucp is None


def test_latest_career_prefers_current_career_then_last_career() -> None:
    current = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        current_career=CITIZEN,
        last_career=SCOUT,
    )
    former = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        last_career=SCOUT,
    )

    assert current.latest_career is CITIZEN
    assert former.latest_career is SCOUT


def test_rank_title_retains_title_from_previous_rank() -> None:
    psion = load_careers()['Psion']
    adept = psion.assignment('Adept')
    assert adept is not None
    summary = CharacterSummary(
        name='Aria',
        sophont=HUMANITI,
        homeworld=MOCK_WORLD,
        current_career=psion,
        current_assignment=adept,
        rank=2,
        career_terms=[CareerTerm(career=psion, assignment=adept, rank_after_term=2)],
    )

    assert summary.rank_title == ('2', 'Initiate')


# ── CharacterSummary.diff ──────────────────────────────────────────────────────


def test_diff_returns_empty_list_when_nothing_changed() -> None:
    s = _summary(characteristics={}, skills=[])
    assert s.diff(s) == []


def test_diff_reports_new_narrative_entries() -> None:
    before = _summary(narrative=['Term 1'])
    after = _summary(narrative=['Term 1', 'Survived the storm'])
    assert any('Survived the storm' in c for c in before.diff(after))


def test_diff_reports_characteristic_change() -> None:
    before = _summary(characteristics={Chars.STR: 7, Chars.DEX: 8})
    after = _summary(characteristics={Chars.STR: 8, Chars.DEX: 8})
    assert any('STR' in c and '7' in c and '8' in c for c in before.diff(after))


def test_diff_reports_newly_gained_skill() -> None:
    before = _summary()
    after = _summary(skills=[Admin()])
    assert any('Admin' in c for c in before.diff(after))


def test_diff_reports_skill_level_increase() -> None:
    before = _summary(skills=[Admin()])
    after = _summary(skills=[Admin(level=Level(value=1))])
    assert any('Admin' in c and '0' in c and '1' in c for c in before.diff(after))


def test_diff_reports_rank_change() -> None:
    before = _summary(rank=0)
    after = _summary(rank=1)
    assert any('Rank' in c and '1' in c for c in before.diff(after))


def test_diff_reports_cash_change() -> None:
    before = _summary(cash=0)
    after = _summary(cash=5000)
    assert any('5000' in c or '5,000' in c for c in before.diff(after))
