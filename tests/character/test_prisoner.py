from ceres.character.careers.loader import load_careers, selectable_careers
from ceres.character.characteristics import Chars
from ceres.character.events import (
    AdvancementEvent,
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    ParoleRollEvent,
    PendingAdvancement,
    PendingAssignmentChangeChoice,
    PendingCareerChoice,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    PendingDoubleInjuryRoll,
    PendingInitialTrainingChoice,
    PendingInjuryTable,
    PendingMusterOut,
    PendingSkillChoice,
    PendingSkillTable,
    SkillChoiceEvent,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, WorkerProfession
from ceres.character.sophonts import VILANI
from ceres.character.state import (
    Ally,
    Enemy,
)
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def test_prisoner_career_loads_but_is_not_selectable():
    careers = load_careers()

    assert 'Prisoner' in careers
    assert 'Prisoner' not in selectable_careers()


def test_prisoner_is_not_listed_after_background_skills():
    projection = replay(1, _setup())

    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice))
    assert 'Prisoner' not in pending.options


def test_prisoner_can_be_entered_when_event_log_sends_character_there():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Prisoner', assignment='Inmate', qualification_roll=0),
    ]

    projection = replay(1, events)

    assert projection.summary.current_career == 'Prisoner'
    assert projection.summary.current_assignment == 'Inmate'
    assert projection.summary.skill_level('Melee') == 1
    assert any(isinstance(p, PendingInitialTrainingChoice) for p in projection.pending_inputs)


# ── prisoner event-handler helpers ───────────────────────────────────────────
# Prisoner service_skills has {skill: Profession} → PendingInitialTrainingChoice at '4.0'.
# PendingParoleRoll goes to '4.1' (added after start_new_term).
# After resolving InitialTrainingChoice, PendingSurvive is queued at '<choice_event_id>.0'.
# Inmate survival: END 7+, END=6, DM+0 → need roll 7.  PT after ParoleRoll(roll=3) = 5.


def _enter_prisoner() -> list:
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Prisoner', assignment='Inmate', qualification_roll=0),
        SkillChoiceEvent(id=5, fulfills='4.0', skill=WorkerProfession()),
        ParoleRollEvent(id=6, fulfills='4.1', roll=3),  # PT = 5
    ]


def _through_survive(survive_roll: int = 8) -> list:
    return [*_enter_prisoner(), SurviveEvent(id=7, fulfills='5.0', roll=survive_roll)]


def _through_term_event(event_roll: int) -> list:
    return [*_through_survive(), TermEventEvent(id=8, fulfills='7.0', roll=event_roll)]


def _setup_to_mishap() -> list:
    return [
        *_enter_prisoner(),
        SurviveEvent(id=7, fulfills='5.0', roll=6),  # END 7+, DM+0, 6 < 7 — fail
    ]


def _prisoner_at_advancement() -> list:
    """Events leaving a Prisoner/Inmate at PendingAdvancement('8.0').

    Uses term event 8 (parole hearing, PT −1): PT goes 5 → 4. Inmate advancement:
    STR 7+, STR=7, DM=0.  effective = roll (no DM).  Parole threshold = 4.
    """
    return _through_term_event(event_roll=8)


# ── mishap 3: prison gang ─────────────────────────────────────────────────────


class TestPrisonerMishap3:
    def test_mishap_3_creates_choice_pending(self):
        events = [*_setup_to_mishap(), MishapEvent(id=8, fulfills='7.0', roll=3)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerMishap)), None)
        assert pending is not None
        assert set(pending.options) == {'fight', 'submit'}

    def test_submit_adds_problem_and_queues_advancement(self):
        events = [
            *_setup_to_mishap(),
            MishapEvent(id=8, fulfills='7.0', roll=3),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_mishap_3', choice='submit'),
        ]
        projection = replay(1, events)
        assert any('submit' in p.lower() or 'gang' in p.lower() for p in projection.summary.problems)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_fight_creates_melee_roll(self):
        events = [
            *_setup_to_mishap(),
            MishapEvent(id=8, fulfills='7.0', roll=3),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_mishap_3', choice='fight'),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert pending.options == ['Melee']

    def test_fight_success_adds_enemy_and_increases_pt(self):
        events = [
            *_setup_to_mishap(),
            MishapEvent(id=8, fulfills='7.0', roll=3),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_mishap_3', choice='fight'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_mishap_3_fight', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1
        assert projection.summary.parole_threshold == 6  # PT was 5; +1 = 6

    def test_fight_failure_creates_double_injury(self):
        events = [
            *_setup_to_mishap(),
            MishapEvent(id=8, fulfills='7.0', roll=3),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_mishap_3', choice='fight'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_mishap_3_fight', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingDoubleInjuryRoll) for p in projection.pending_inputs)


# ── event 3: escape opportunity ───────────────────────────────────────────────


class TestPrisonerEvent3:
    def test_creates_event_pending_with_options(self):
        projection = replay(1, _through_term_event(event_roll=3))
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 3), None
        )
        assert pending is not None
        assert set(pending.options) == {'attempt', 'stay'}

    def test_stay_queues_advancement(self):
        events = [
            *_through_term_event(event_roll=3),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_3', choice='stay'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_attempt_creates_skill_roll(self):
        events = [
            *_through_term_event(event_roll=3),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_3', choice='attempt'),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert set(pending.options) == {'Stealth', 'Deception'}

    def test_escape_success_ends_career_with_muster_out(self):
        events = [
            *_through_term_event(event_roll=3),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_3', choice='attempt'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_event_3_escape', skill=Admin(), modified_roll=11),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_escape_failure_increases_pt(self):
        events = [
            *_through_term_event(event_roll=3),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_3', choice='attempt'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_event_3_escape', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 7  # PT was 5; +2 = 7


# ── event 4: hard labour ──────────────────────────────────────────────────────


class TestPrisonerEvent4:
    def test_creates_end_roll_pending(self):
        projection = replay(1, _through_term_event(event_roll=4))
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 4), None
        )
        assert pending is not None
        assert pending.options == [Chars.END]

    def test_success_decreases_pt_and_creates_skill_choice(self):
        events = [
            *_through_term_event(event_roll=4),
            SkillRollEvent(id=9, fulfills='8.0', context='prisoner_event_4', skill=Chars.END, modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 4  # PT was 5; −1 = 4
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert set(pending.options) == {'Athletics', 'Mechanic', 'Melee'}

    def test_failure_increases_pt_and_queues_advancement(self):
        events = [
            *_through_term_event(event_roll=4),
            SkillRollEvent(id=9, fulfills='8.0', context='prisoner_event_4', skill=Chars.END, modified_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 6  # PT was 5; +1 = 6
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 5: gang opportunity ─────────────────────────────────────────────────


class TestPrisonerEvent5:
    def test_creates_skill_roll_pending(self):
        projection = replay(1, _through_term_event(event_roll=5))
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 5), None
        )
        assert pending is not None
        assert set(pending.options) == {'Persuade', 'Melee'}

    def test_success_increases_pt_and_creates_skill_choice(self):
        events = [
            *_through_term_event(event_roll=5),
            SkillRollEvent(id=9, fulfills='8.0', context='prisoner_event_5', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 6  # PT was 5; +1 = 6
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_adds_enemy_and_queues_advancement(self):
        events = [
            *_through_term_event(event_roll=5),
            SkillRollEvent(id=9, fulfills='8.0', context='prisoner_event_5', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 6: vocational training ─────────────────────────────────────────────


class TestPrisonerEvent6:
    def test_creates_edu_roll_pending(self):
        projection = replay(1, _through_term_event(event_roll=6))
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 6), None
        )
        assert pending is not None
        assert pending.options == [Chars.EDU]

    def test_success_creates_any_skill_choice(self):
        events = [
            *_through_term_event(event_roll=6),
            SkillRollEvent(id=9, fulfills='8.0', context='prisoner_event_6', skill=Chars.EDU, modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert 'Admin' in pending.options

    def test_failure_queues_advancement(self):
        events = [
            *_through_term_event(event_roll=6),
            SkillRollEvent(id=9, fulfills='8.0', context='prisoner_event_6', skill=Chars.EDU, modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 7: prison event sub-table ──────────────────────────────────────────


class TestPrisonerEvent7:
    def test_creates_sub_table_pending(self):
        projection = replay(1, _through_term_event(event_roll=7))
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 7), None
        )
        assert pending is not None
        assert set(pending.options) == {'1', '2', '3', '4', '5', '6'}

    def test_sub_1_riot_creates_end_roll(self):
        events = [
            *_through_term_event(event_roll=7),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_7', choice='1'),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert pending.options == [Chars.END]

    def test_sub_1_riot_failure_creates_injury_table(self):
        events = [
            *_through_term_event(event_roll=7),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_7', choice='1'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_event_7_riot', skill=Chars.END, modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_sub_2_gang_increases_pt_and_adds_enemy(self):
        events = [
            *_through_term_event(event_roll=7),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_7', choice='2'),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 6  # PT was 5; +1 = 6
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_sub_3_transfer_adds_problem(self):
        events = [
            *_through_term_event(event_roll=7),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_7', choice='3'),
        ]
        projection = replay(1, events)
        assert any('transfer' in p.lower() for p in projection.summary.problems)

    def test_sub_4_visitation_adds_ally(self):
        events = [
            *_through_term_event(event_roll=7),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_7', choice='4'),
        ]
        projection = replay(1, events)
        allies = [c for c in projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1

    def test_sub_5_parole_hearing_decreases_pt(self):
        events = [
            *_through_term_event(event_roll=7),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_7', choice='5'),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 4  # PT was 5; −1 = 4

    def test_sub_6_good_behaviour_decreases_pt(self):
        events = [
            *_through_term_event(event_roll=7),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_7', choice='6'),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 4  # PT was 5; −1 = 4


# ── event 9: hire lawyer ──────────────────────────────────────────────────────


class TestPrisonerEvent9:
    def test_creates_event_pending_with_options(self):
        projection = replay(1, _through_term_event(event_roll=9))
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 9), None
        )
        assert pending is not None
        assert set(pending.options) == {'level_1', 'level_2', 'level_3', 'decline'}

    def test_decline_queues_advancement(self):
        events = [
            *_through_term_event(event_roll=9),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_9', choice='decline'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_hire_level_1_creates_skill_roll(self):
        events = [
            *_through_term_event(event_roll=9),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_9', choice='level_1'),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None

    def test_level_1_success_decreases_pt(self):
        # roll + level (1) >= 8 → roll 8: 8 + 1 = 9 >= 8 → success → PT−1
        events = [
            *_through_term_event(event_roll=9),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_9', choice='level_1'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_event_9_level_1', skill=Admin(), modified_roll=8),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 4  # PT was 5; −1 = 4

    def test_level_1_failure_keeps_pt(self):
        # roll + level (1) < 8 → roll 6: 6 + 1 = 7 < 8 → fail → PT unchanged
        events = [
            *_through_term_event(event_roll=9),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_9', choice='level_1'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_event_9_level_1', skill=Admin(), modified_roll=6),
        ]
        projection = replay(1, events)
        assert projection.summary.parole_threshold == 5  # unchanged


# ── event 12: heroism ─────────────────────────────────────────────────────────


class TestPrisonerEvent12:
    def test_creates_event_pending_with_options(self):
        projection = replay(1, _through_term_event(event_roll=12))
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 12), None
        )
        assert pending is not None
        assert set(pending.options) == {'take_risk', 'refuse'}

    def test_refuse_queues_advancement(self):
        events = [
            *_through_term_event(event_roll=12),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_12', choice='refuse'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_take_risk_creates_skill_roll(self):
        events = [
            *_through_term_event(event_roll=12),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_12', choice='take_risk'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingCareerSkillRoll) for p in projection.pending_inputs)

    def test_heroism_success_adds_ally_and_decreases_pt(self):
        events = [
            *_through_term_event(event_roll=12),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_12', choice='take_risk'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_event_12_heroism', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        allies = [c for c in projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1
        assert projection.summary.parole_threshold == 3  # PT was 5; −2 = 3

    def test_heroism_failure_creates_injury_table(self):
        events = [
            *_through_term_event(event_roll=12),
            CareerChoiceEvent(id=9, fulfills='8.0', context='prisoner_event_12', choice='take_risk'),
            SkillRollEvent(id=10, fulfills='9.0', context='prisoner_event_12_heroism', skill=Admin(), modified_roll=7),
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
        events = [*_prisoner_at_advancement(), AdvancementEvent(id=9, fulfills='8.0', roll=4)]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAssignmentChangeChoice) for p in projection.pending_inputs)

    def test_assignment_change_options_exclude_muster_out_for_prisoner(self):
        events = [*_prisoner_at_advancement(), AdvancementEvent(id=9, fulfills='8.0', roll=4)]
        projection = replay(1, events)
        choice = next(p for p in projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice))
        assert 'muster_out' not in choice.options
        assert 'same' in choice.options

    def test_parole_granted_clears_career(self):
        events = [*_prisoner_at_advancement(), AdvancementEvent(id=9, fulfills='8.0', roll=5)]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_parole_granted_creates_muster_out_pending(self):
        events = [*_prisoner_at_advancement(), AdvancementEvent(id=9, fulfills='8.0', roll=5)]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_parole_narrative_recorded(self):
        events = [*_prisoner_at_advancement(), AdvancementEvent(id=9, fulfills='8.0', roll=5)]
        projection = replay(1, events)
        assert any('Parole' in n for n in projection.summary.narrative)

    def test_advancement_success_with_parole_grants_skill_table(self):
        # roll=7: success (rank 0→1) and freed → skill table + muster out both pending
        events = [*_prisoner_at_advancement(), AdvancementEvent(id=9, fulfills='8.0', roll=7)]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_advancement_success_with_parole_increments_rank(self):
        events = [*_prisoner_at_advancement(), AdvancementEvent(id=9, fulfills='8.0', roll=7)]
        projection = replay(1, events)
        assert projection.summary.rank == 1
