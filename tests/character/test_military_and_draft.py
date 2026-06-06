from ceres.character.careers.loader import load_careers
from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerEvent,
    CharacterStartedEvent,
    CommissionEvent,
    DraftAssignmentEvent,
    DraftEvent,
    PendingAdvancement,
    PendingCommissionChoice,
    PendingDraftAssignmentChoice,
    PendingDraftChoice,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, Leadership
from ceres.character.sophonts import VILANI
from tests.character.helpers import MOCK_WORLD


def _setup(ucp: str = '7869A5') -> list:
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills=(1, 0), ucp=ucp),
        BackgroundSkillsEvent(id=3, fulfills=(2, 0), skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def test_new_core_careers_load():
    careers = load_careers()

    assert careers['Merchant'].assignment('Merchant Marine') is not None
    assert careers['Army'].assignment('Infantry') is not None
    assert careers['Marines'].assignment('Star Marine') is not None
    assert careers['Navy'].assignment('Line/Crew') is not None


def test_failed_qualification_creates_draft_choice():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills=(3, 0), career='Merchant', assignment='Merchant Marine', qualification_roll=2),
    ]

    projection = replay(1, events)

    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingDraftChoice))
    assert pending.options == ['draft', 'drifter']
    assert projection.summary.current_career is None


def test_draftable_careers_tell_whether_this_character_can_be_drafted():
    careers = load_careers()
    replay(1, _setup())

    draft_careers = [career.name for career in careers.values() if career.does_draft()]

    assert {'Navy', 'Army', 'Marines', 'Merchant', 'Scout', 'Agent'} <= set(draft_careers)
    assert 'Citizen' not in draft_careers


def test_draft_event_records_selected_career_and_assignment():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills=(3, 0), career='Army', assignment='Infantry', qualification_roll=2),
        DraftEvent(id=5, fulfills=(4, 0), career='Merchant', assignment='Merchant Marine'),
    ]

    projection = replay(1, events)

    assert projection.summary.drafted
    assert projection.summary.current_career is not None
    assert projection.summary.current_career.name == 'Merchant'
    assert projection.summary.current_assignment == 'Merchant Marine'


def test_draft_to_career_with_multiple_assignments_asks_player_to_choose_assignment():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills=(3, 0), career='Merchant', assignment='Merchant Marine', qualification_roll=2),
        DraftEvent(id=5, fulfills=(4, 0), career='Army'),
    ]

    projection = replay(1, events)

    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingDraftAssignmentChoice))
    assert pending.career == 'Army'
    assert pending.options == ['Support', 'Infantry', 'Cavalry']
    assert projection.summary.current_career is None


def test_draft_assignment_choice_starts_selected_assignment():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills=(3, 0), career='Merchant', assignment='Merchant Marine', qualification_roll=2),
        DraftEvent(id=5, fulfills=(4, 0), career='Army'),
        DraftAssignmentEvent(id=6, fulfills=(5, 0), career='Army', assignment='Cavalry'),
    ]

    projection = replay(1, events)

    assert projection.summary.drafted
    assert projection.summary.current_career is not None
    assert projection.summary.current_career.name == 'Army'
    assert projection.summary.current_assignment == 'Cavalry'


def test_merchant_does_not_offer_commission_before_advancement():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills=(3, 0), career='Merchant', assignment='Merchant Marine', qualification_roll=8),
        SurviveEvent(id=5, fulfills=(4, 0), roll=8),
        TermEventEvent(id=6, fulfills=(5, 0), roll=9),
    ]

    projection = replay(1, events)

    assert not any(isinstance(p, PendingCommissionChoice) for p in projection.pending_inputs)


def test_army_first_term_offers_commission_before_advancement():
    events = [
        *_setup(ucp='7869A9'),
        CareerEvent(id=4, fulfills=(3, 0), career='Army', assignment='Infantry', qualification_roll=8),
        SurviveEvent(id=5, fulfills=(4, 0), roll=8),
        TermEventEvent(id=6, fulfills=(5, 0), roll=9),
    ]

    projection = replay(1, events)

    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingCommissionChoice))
    assert pending.options == ['attempt', 'skip']


def test_successful_commission_sets_officer_rank_and_skips_advancement():
    events = [
        *_setup(ucp='7869A9'),
        CareerEvent(id=4, fulfills=(3, 0), career='Army', assignment='Infantry', qualification_roll=8),
        SurviveEvent(id=5, fulfills=(4, 0), roll=8),
        TermEventEvent(id=6, fulfills=(5, 0), roll=10),
        CommissionEvent(id=7, fulfills=(6, 0), attempt=True, roll=8),
    ]

    projection = replay(1, events)

    assert projection.summary.rank == 1
    assert projection.summary.career_terms[-1].commission
    assert projection.summary.skill_level(Leadership) == 1
    assert not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


def test_qualification_dm_is_consumed_on_career_entry():
    from ceres.character.characteristics import Chars
    from ceres.character.state import CharacterProjection, CharacterSummary

    careers = load_careers()
    army = careers['Army']
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='Test',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.END: 7},
        ),
    )
    # DM of +10 ensures a roll of 0 still qualifies (Army END 5+)
    proj.pending_qualification_dm = 10
    infantry = army.assignment('Infantry')
    assert infantry is not None
    army.start_career(proj, infantry, event_id=6, qualification_roll=0)

    assert proj.summary.current_career is not None
    assert proj.summary.current_career.name == 'Army'
    assert proj.pending_qualification_dm == 0
