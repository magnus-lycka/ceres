from ceres.character.domain.career import PRISONER
from ceres.character.domain.career.career_events import (
    AdvancementHandler,
    CareerChoiceHandler,
    CareerEntryHandler,
    MishapHandler,
    ParoleRollHandler,
    PendingAdvancement,
    PendingAssignmentChangeChoice,
    PendingCareerChoice,
    PendingChoices,
    PendingInitialTrainingChoice,
    PendingMusterOut,
    PendingRankBonusChoice,
    PendingSkillChoice,
    PendingSkillTable,
    SkillChoiceHandler,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.loader import selectable_careers
from ceres.character.domain.career.prisoner import (
    PendingPrisonerEvent3EscapeSkillRoll,
    PendingPrisonerEvent4SkillRoll,
    PendingPrisonerEvent5SkillRoll,
    PendingPrisonerEvent6SkillRoll,
    PendingPrisonerEvent7RiotSkillRoll,
    PendingPrisonerEvent9LawyerSkillRoll,
    PendingPrisonerEvent12HeroismSkillRoll,
    PendingPrisonerMishap3FightSkillRoll,
    PrisonerEvent3Attempt,
    PrisonerEvent3Stay,
    PrisonerEvent7Gang,
    PrisonerEvent7GoodBehaviour,
    PrisonerEvent7ParoleHearing,
    PrisonerEvent7Riot,
    PrisonerEvent7Transfer,
    PrisonerEvent7Visitation,
    PrisonerEvent9Decline,
    PrisonerEvent9Level1,
    PrisonerEvent9Level2,
    PrisonerEvent9Level3,
    PrisonerEvent12Refuse,
    PrisonerEvent12TakeRisk,
    PrisonerMishap3Fight,
    PrisonerMishap3Submit,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, UcpHandler
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import (
    Ally,
    Enemy,
)
from ceres.character.domain.health.health_events import (
    PendingDoubleInjuryRoll,
    PendingInjuryTable,
)
from ceres.character.domain.skills import (
    Admin,
    AnySkill,
    Athletics,
    Carouse,
    Deception,
    Drive,
    Electronics,
    Mechanic,
    Melee,
    Persuade,
    Stealth,
    WorkerProfession,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.pending_input import ChoiceBase
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver, _creation_events


def _setup() -> list:
    c = _creation_events(VILANI, MOCK_WORLD, 'NPC', 'Boss')
    ucp = Event(fulfills=(c[-1].id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(
        fulfills=(ucp.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    return [*c, ucp, background]


def test_prisoner_career_loads_but_is_not_selectable():
    assert PRISONER not in selectable_careers()


def test_prisoner_is_not_listed_after_background_skills():
    projection = replay(1, _setup())

    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice))
    assert 'Prisoner' not in {c.name for c in pending.options}


def test_prisoner_can_be_entered_when_event_log_sends_character_there():
    base = _setup()
    events = [
        *base,
        Event(
            fulfills=(base[-1].id, 0),
            handler=CareerEntryHandler(career=PRISONER, assignment=PRISONER.assignment('Inmate'), qualification_roll=0),
        ),
    ]

    projection = replay(1, events)

    assert projection.summary.current_career is not None
    assert projection.summary.current_career.name == 'Prisoner'
    assert projection.summary.current_assignment is not None
    assert projection.summary.current_assignment.name == 'Inmate'
    assert projection.summary.skill_level(Melee) == 0
    rank_bonus = next(p for p in projection.pending_inputs if isinstance(p, PendingRankBonusChoice))
    assert rank_bonus.options == [Melee()]
    assert any(isinstance(p, PendingInitialTrainingChoice) for p in projection.pending_inputs)


# ── prisoner event-handler helpers ───────────────────────────────────────────
# Prisoner service_skills has {skill: Profession} → PendingInitialTrainingChoice at '4.0'.
# PendingParoleRoll goes to '4.1' (added after start_new_term).
# After resolving InitialTrainingChoice, PendingSurvive is queued at '<choice_event_id>.0'.
# Inmate survival: END 7+, END=6, DM+0 → need roll 7.  PT after ParoleRoll(roll=3) = 5.


def _enter_prisoner() -> list:
    base = _setup()
    entry = Event(
        fulfills=(base[-1].id, 0),
        handler=CareerEntryHandler(career=PRISONER, assignment=PRISONER.assignment('Inmate'), qualification_roll=0),
    )
    training = Event(fulfills=(entry.id, 0), handler=SkillChoiceHandler(skill=WorkerProfession()))
    parole = Event(fulfills=(entry.id, 1), handler=ParoleRollHandler(roll=3))  # PT = 5
    return [
        *base,
        entry,
        training,
        parole,
    ]


def _through_survive(survive_roll: int = 8) -> list:
    base = _enter_prisoner()
    training = next(event for event in base if isinstance(event.handler, SkillChoiceHandler))
    return [*base, Event(fulfills=(training.id, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int) -> list:
    base = _through_survive()
    return [*base, Event(fulfills=(base[-1].id, 0), handler=TermEventHandler(roll=event_roll))]


def _setup_to_mishap() -> list:
    base = _enter_prisoner()
    training = next(event for event in base if isinstance(event.handler, SkillChoiceHandler))
    return [*base, Event(fulfills=(training.id, 0), handler=SurviveHandler(roll=6))]


def _prisoner_at_advancement() -> list:
    """Events leaving a Prisoner/Inmate at PendingAdvancement('8.0').

    Uses term event 8 (parole hearing, PT −1): PT goes 5 → 4. Inmate advancement:
    STR 7+, STR=7, DM=0.  effective = roll (no DM).  Parole threshold = 4.
    """
    return _through_term_event(event_roll=8)


def _career_choice_event(source: Event, choice_cls: type[ChoiceBase]) -> Event:
    return Event(
        fulfills=(source.id, 0),
        handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default),
    )


def _skill_roll_event(source: Event, skill: AnySkill | Chars, modified_roll: int) -> Event:
    return Event(fulfills=(source.id, 0), handler=SkillRollHandler(skill=skill, modified_roll=modified_roll))


def _advancement_event(source: Event, roll: int) -> Event:
    return Event(fulfills=(source.id, 0), handler=AdvancementHandler(roll=roll))


class TestPrisonerDirectOutcomeRows:
    def test_mishap_2_increases_parole_threshold_and_stays_in_career(self):
        base = _setup_to_mishap()
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=2))])

        assert projection.summary.parole_threshold == 7
        assert projection.summary.current_career is not None
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_mishap_5_decreases_soc_and_stays_in_career(self):
        base = _setup_to_mishap()
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))])

        assert projection.summary.characteristics[Chars.SOC] == 4
        assert projection.summary.current_career is not None
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_event_8_reduces_parole_threshold(self):
        projection = replay(1, _through_term_event(8))

        assert projection.summary.parole_threshold == 4

    def test_event_11_reduces_parole_threshold_by_two(self):
        projection = replay(1, _through_term_event(11))

        assert projection.summary.parole_threshold == 3


# ── mishap 3: prison gang ─────────────────────────────────────────────────────


class TestPrisonerMishap3:
    def test_mishap_3_creates_choice_pending(self):
        base = _setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {PrisonerMishap3Fight, PrisonerMishap3Submit}

    def test_submit_adds_problem_and_queues_advancement(self):
        base = _setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))
        events = [
            *base,
            mishap,
            _career_choice_event(mishap, PrisonerMishap3Submit),
        ]
        projection = replay(1, events)
        assert any('submit' in p.lower() or 'gang' in p.lower() for p in projection.summary.problems)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_fight_creates_melee_roll(self):
        base = _setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))
        events = [
            *base,
            mishap,
            _career_choice_event(mishap, PrisonerMishap3Fight),
        ]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingPrisonerMishap3FightSkillRoll)), None
        )
        assert pending is not None
        assert pending.options == [Melee()]

    def test_fight_success_adds_enemy_and_increases_pt(self):
        base = _setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))
        fight = _career_choice_event(mishap, PrisonerMishap3Fight)
        events = [
            *base,
            mishap,
            fight,
            _skill_roll_event(fight, Admin(), 9),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1
        assert projection.summary.parole_threshold == 6  # PT was 5; +1 = 6

    def test_fight_failure_creates_double_injury(self):
        base = _setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))
        fight = _career_choice_event(mishap, PrisonerMishap3Fight)
        events = [
            *base,
            mishap,
            fight,
            _skill_roll_event(fight, Admin(), 7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingDoubleInjuryRoll) for p in projection.pending_inputs)


# ── event 3: escape opportunity ───────────────────────────────────────────────


class TestPrisonerEvent3:
    def test_creates_event_pending_with_options(self):
        projection = replay(1, _through_term_event(event_roll=3))
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {PrisonerEvent3Attempt, PrisonerEvent3Stay}

    def test_stay_queues_advancement(self):
        base = _through_term_event(event_roll=3)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent3Stay),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_attempt_creates_skill_roll(self):
        base = _through_term_event(event_roll=3)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent3Attempt),
        ]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingPrisonerEvent3EscapeSkillRoll)), None
        )
        assert pending is not None
        assert pending.options == [Stealth(), Deception()]

    def test_escape_success_ends_career_with_muster_out(self):
        base = _through_term_event(event_roll=3)
        attempt = _career_choice_event(base[-1], PrisonerEvent3Attempt)
        events = [
            *base,
            attempt,
            _skill_roll_event(attempt, Admin(), 11),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_escape_failure_increases_pt(self):
        base = _through_term_event(event_roll=3)
        attempt = _career_choice_event(base[-1], PrisonerEvent3Attempt)
        events = [
            *base,
            attempt,
            _skill_roll_event(attempt, Admin(), 9),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 7  # PT was 5; +2 = 7


# ── event 4: hard labour ──────────────────────────────────────────────────────


class TestPrisonerEvent4:
    def test_creates_end_roll_pending(self):
        projection = replay(1, _through_term_event(event_roll=4))
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingPrisonerEvent4SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Chars.END]

    def test_success_decreases_pt_and_creates_skill_choice(self):
        base = _through_term_event(event_roll=4)
        events = [
            *base,
            _skill_roll_event(base[-1], Chars.END, 9),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 4  # PT was 5; −1 = 4
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [Athletics(), Mechanic(), Melee()]

    def test_failure_increases_pt_and_queues_advancement(self):
        base = _through_term_event(event_roll=4)
        events = [
            *base,
            _skill_roll_event(base[-1], Chars.END, 7),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 6  # PT was 5; +1 = 6
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 5: gang opportunity ─────────────────────────────────────────────────


class TestPrisonerEvent5:
    def test_creates_skill_roll_pending(self):
        projection = replay(1, _through_term_event(event_roll=5))
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingPrisonerEvent5SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Persuade(), Melee()]

    def test_success_increases_pt_and_creates_skill_choice(self):
        base = _through_term_event(event_roll=5)
        events = [
            *base,
            _skill_roll_event(base[-1], Admin(), 9),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 6  # PT was 5; +1 = 6
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_adds_enemy_and_queues_advancement(self):
        base = _through_term_event(event_roll=5)
        events = [
            *base,
            _skill_roll_event(base[-1], Admin(), 7),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 6: vocational training ─────────────────────────────────────────────


class TestPrisonerEvent6:
    def test_creates_edu_roll_pending(self):
        projection = replay(1, _through_term_event(event_roll=6))
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingPrisonerEvent6SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Chars.EDU]

    def test_success_creates_any_skill_choice(self):
        base = _through_term_event(event_roll=6)
        events = [
            *base,
            _skill_roll_event(base[-1], Chars.EDU, 9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert any(isinstance(o, Admin) for o in pending.options)

    def test_failure_queues_advancement(self):
        base = _through_term_event(event_roll=6)
        events = [
            *base,
            _skill_roll_event(base[-1], Chars.EDU, 7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 7: prison event sub-table ──────────────────────────────────────────


class TestPrisonerEvent7:
    def test_creates_sub_table_pending(self):
        projection = replay(1, _through_term_event(event_roll=7))
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {
            PrisonerEvent7Riot,
            PrisonerEvent7Gang,
            PrisonerEvent7Transfer,
            PrisonerEvent7Visitation,
            PrisonerEvent7ParoleHearing,
            PrisonerEvent7GoodBehaviour,
        }

    def test_sub_1_riot_creates_end_roll(self):
        base = _through_term_event(event_roll=7)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent7Riot),
        ]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingPrisonerEvent7RiotSkillRoll)), None
        )
        assert pending is not None
        assert pending.options == [Chars.END]

    def test_sub_1_riot_failure_creates_injury_table(self):
        base = _through_term_event(event_roll=7)
        riot = _career_choice_event(base[-1], PrisonerEvent7Riot)
        events = [
            *base,
            riot,
            _skill_roll_event(riot, Chars.END, 7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_sub_2_gang_increases_pt_and_adds_enemy(self):
        base = _through_term_event(event_roll=7)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent7Gang),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 6  # PT was 5; +1 = 6
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_sub_3_transfer_adds_problem(self):
        base = _through_term_event(event_roll=7)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent7Transfer),
        ]
        projection = replay(1, events)
        assert any('transfer' in p.lower() for p in projection.summary.problems)

    def test_sub_4_visitation_adds_ally(self):
        base = _through_term_event(event_roll=7)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent7Visitation),
        ]
        projection = replay(1, events)
        allies = [c for c in projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1

    def test_sub_5_parole_hearing_decreases_pt(self):
        base = _through_term_event(event_roll=7)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent7ParoleHearing),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 4  # PT was 5; −1 = 4

    def test_sub_6_good_behaviour_decreases_pt(self):
        base = _through_term_event(event_roll=7)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent7GoodBehaviour),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 4  # PT was 5; −1 = 4


# ── event 9: hire lawyer ──────────────────────────────────────────────────────


class TestPrisonerEvent9:
    def test_creates_event_pending_with_options(self):
        projection = replay(1, _through_term_event(event_roll=9))
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {
            PrisonerEvent9Level1,
            PrisonerEvent9Level2,
            PrisonerEvent9Level3,
            PrisonerEvent9Decline,
        }

    def test_decline_queues_advancement(self):
        base = _through_term_event(event_roll=9)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent9Decline),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_hire_level_1_creates_skill_roll(self):
        base = _through_term_event(event_roll=9)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent9Level1),
        ]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingPrisonerEvent9LawyerSkillRoll)), None
        )
        assert pending is not None

    def test_level_1_success_decreases_pt(self):
        # roll + level (1) >= 8 → roll 8: 8 + 1 = 9 >= 8 → success → PT−1
        base = _through_term_event(event_roll=9)
        level_1 = _career_choice_event(base[-1], PrisonerEvent9Level1)
        events = [
            *base,
            level_1,
            _skill_roll_event(level_1, Admin(), 8),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 4  # PT was 5; −1 = 4

    def test_level_1_failure_keeps_pt(self):
        # roll + level (1) < 8 → roll 6: 6 + 1 = 7 < 8 → fail → PT unchanged
        base = _through_term_event(event_roll=9)
        level_1 = _career_choice_event(base[-1], PrisonerEvent9Level1)
        events = [
            *base,
            level_1,
            _skill_roll_event(level_1, Admin(), 6),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 5  # unchanged


# ── event 10: special duty ───────────────────────────────────────────────────


class TestPrisonerEvent10:
    def test_electronics_option_is_computers_specialty(self):
        projection = replay(1, _through_term_event(event_roll=10))
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        electronics_opt = next((o for o in pending.options if isinstance(o, Electronics)), None)
        assert electronics_opt is not None
        assert electronics_opt.computers.value > 0


# ── event 12: heroism ─────────────────────────────────────────────────────────


class TestPrisonerEvent12:
    def test_creates_event_pending_with_options(self):
        projection = replay(1, _through_term_event(event_roll=12))
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {PrisonerEvent12TakeRisk, PrisonerEvent12Refuse}

    def test_refuse_queues_advancement(self):
        base = _through_term_event(event_roll=12)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent12Refuse),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_take_risk_creates_skill_roll(self):
        base = _through_term_event(event_roll=12)
        events = [
            *base,
            _career_choice_event(base[-1], PrisonerEvent12TakeRisk),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingPrisonerEvent12HeroismSkillRoll) for p in projection.pending_inputs)

    def test_heroism_success_adds_ally_and_decreases_pt(self):
        base = _through_term_event(event_roll=12)
        risk = _career_choice_event(base[-1], PrisonerEvent12TakeRisk)
        events = [
            *base,
            risk,
            _skill_roll_event(risk, Admin(), 9),
        ]
        projection = replay(1, events)
        allies = [c for c in projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1
        assert projection.summary.parole_threshold == 3  # PT was 5; −2 = 3

    def test_heroism_failure_creates_injury_table(self):
        base = _through_term_event(event_roll=12)
        risk = _career_choice_event(base[-1], PrisonerEvent12TakeRisk)
        events = [
            *base,
            risk,
            _skill_roll_event(risk, Admin(), 7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)


# ── prisoner advancement ──────────────────────────────────────────────────────
# Prisoner advancement differs from normal careers: it checks parole threshold.
# Parole threshold after _prisoner_at_advancement() = 4 (started at 5, event 8 −1).
# Inmate advancement: STR 7+, STR=7, DM=0.  effective = roll.
#   roll=4: fail (4<7), not freed (4≤4)         → PendingAssignmentChangeChoice
#   roll=5: fail (5<7), freed  (5>4)             → parole → muster out
#   roll=7: success (7≥7), freed (7>4)           → rank 1 + skill table + muster out


class TestPrisonerAdvancement:
    def test_advancement_failure_creates_assignment_change_choice(self):
        base = _prisoner_at_advancement()
        events = [*base, _advancement_event(base[-1], 4)]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAssignmentChangeChoice) for p in projection.pending_inputs)

    def test_assignment_change_options_exclude_muster_out_for_prisoner(self):
        base = _prisoner_at_advancement()
        events = [*base, _advancement_event(base[-1], 4)]
        projection = replay(1, events)
        choice = next(p for p in projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice))
        assert choice.muster_out is False

    def test_parole_granted_clears_career(self):
        base = _prisoner_at_advancement()
        events = [*base, _advancement_event(base[-1], 5)]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_parole_granted_creates_muster_out_pending(self):
        base = _prisoner_at_advancement()
        events = [*base, _advancement_event(base[-1], 5)]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_parole_narrative_recorded(self):
        base = _prisoner_at_advancement()
        events = [*base, _advancement_event(base[-1], 5)]
        projection = replay(1, events)
        assert any('Parole' in n for n in projection.summary.narrative)

    def test_advancement_success_with_parole_grants_skill_table(self):
        # roll=7: success (rank 0→1) and freed → skill table + muster out both pending
        base = _prisoner_at_advancement()
        events = [*base, _advancement_event(base[-1], 7)]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_advancement_success_with_parole_increments_rank(self):
        base = _prisoner_at_advancement()
        events = [*base, _advancement_event(base[-1], 7)]
        projection = replay(1, events)
        assert projection.summary.rank == 1


# ── mishap 1: severely injured (stay in career) ───────────────────────────────


class TestPrisonerMishap1:
    def _enter_prisoner(self, driver: CharacterDriver) -> None:
        pending = next(p for p in driver.projection.pending_inputs if isinstance(p, PendingCareerChoice))
        inmate = PRISONER.assignment('Inmate')
        assert inmate is not None
        driver._add(
            Event(
                fulfills=pending.pending_id,
                handler=CareerEntryHandler(career=PRISONER, assignment=inmate, qualification_roll=0),
            )
        )

    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        self._enter_prisoner(d)
        d.initial_training(WorkerProfession())
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}

    def test_career_continues_after_choice(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        self._enter_prisoner(d)
        d.initial_training(WorkerProfession())
        d.survive(2)
        d.mishap(1)
        d.career_choice(CommonMishap1Severe)
        assert d.projection.summary.current_career is not None
        assert d.projection.summary.current_career.name == 'Prisoner'
