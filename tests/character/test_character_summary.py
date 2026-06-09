from ceres.character.domain.career import CITIZEN, SCOUT
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.career.loader import load_careers
from ceres.character.domain.character_state import CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.sophont import HUMANITI
from tests.character.helpers import MOCK_WORLD


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
