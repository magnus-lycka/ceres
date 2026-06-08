"""Tests for the Navy career — line/crew, engineer/gunner, and flight assignments."""

from ceres.character.domain.career import NAVY
from ceres.character.domain.career.career_events import (
    CareerChoiceHandler,
    CareerEntryHandler,
    MishapHandler,
    PendingAdvancement,
    PendingBenefitChoice,
    PendingCareerChoice,
    PendingChoices,
    PendingCommissionChoice,
    PendingMusterOut,
    PendingSkillChoice,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.career.navy import (
    NavyEvent10Profit,
    NavyEvent10Refuse,
    NavyMishap4NotResponsible,
    NavyMishap4Responsible,
    PendingNavyMishap3SkillRoll,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.connection import Enemy
from ceres.character.domain.skills import (
    Admin,
    Athletics,
    Carouse,
    Drive,
    Electronics,
    Gunner,
    Mechanic,
    Pilot,
    Tactics,
    VaccSuit,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD, CharacterDriver


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — INT DM+1, EDU DM+2."""
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Ens')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
    ]


def _enter_navy(assignment: str = 'Line/Crew', qual_roll: int = 5) -> list:
    """Through qualification — INT 6+, INT=9 DM+1, roll 5 → 6 ≥ 6."""
    return [
        *_setup(),
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(
                career=NAVY, assignment=NAVY.assignment(assignment), qualification_roll=qual_roll
            ),
        ),
    ]


def _through_survive(assignment: str = 'Line/Crew', survive_roll: int = 4) -> list:
    """Navy service skills are all single-choice — survival queued at '4.0'.

    Line/Crew survival: INT 5+, DM+1, roll 4 → 5 ≥ 5 (pass).
    """
    return [*_enter_navy(assignment), Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Line/Crew') -> list:
    return [*_through_survive(assignment), Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=event_roll))]


# ── mishap 3: battle skill check (assignment-specific) ───────────────────────


class TestNavyMishap3:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_navy('Line/Crew'),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),  # INT 5+, DM+1, 3 → 4 < 5 — fail
        ]

    def test_line_crew_mishap_3_options_are_electronics_or_gunner(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingNavyMishap3SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Electronics(), Gunner()]

    def test_engineer_gunner_mishap_3_options_are_mechanic_or_vacc_suit(self):
        events = [
            *_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=NAVY, assignment=NAVY.assignment('Engineer/Gunner'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=4)),  # INT 6+, DM+1, fail with roll 4
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingNavyMishap3SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Mechanic(), VaccSuit()]

    def test_flight_mishap_3_options_are_pilot_or_tactics(self):
        events = [
            *_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=NAVY, assignment=NAVY.assignment('Flight'), qualification_roll=5),
            ),
            Event(
                id=5, fulfills=(4, 0), handler=SurviveHandler(roll=6)
            ),  # DEX 7+, DM+1, fail with roll 6 → 7 ≥ 7 — pass, need fail
            # Actually DEX 7+, DEX=8, DM+1, need roll 6+ to pass; roll 5 → 6 < 7 fails
        ]
        # Reset: Flight survival DEX 7+, DEX=8, DM+1, roll 5 → 6 < 7 — fail
        events = [
            *_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=NAVY, assignment=NAVY.assignment('Flight'), qualification_roll=5),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=5)),  # DEX 7+, DM+1, 5 → 6 < 7 — fail
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingNavyMishap3SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Pilot(), Tactics()]

    def test_success_keeps_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_failure_loses_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_both_outcomes_end_career(self):
        for roll in (9, 7):
            events = [
                *self._setup_to_mishap(),
                Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
                Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=roll)),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, f'roll={roll}'


# ── mishap 4: blamed for accident ────────────────────────────────────────────


class TestNavyMishap4:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_navy('Line/Crew'),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),
        ]

    def test_mishap_4_creates_choice_pending(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {NavyMishap4Responsible, NavyMishap4NotResponsible}

    def test_responsible_adds_problem_note(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=NavyMishap4Responsible.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any('free' in p.lower() or 'skill' in p.lower() for p in projection.summary.problems)

    def test_responsible_loses_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=NavyMishap4Responsible.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_not_responsible_adds_enemy(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=NavyMishap4NotResponsible.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_not_responsible_keeps_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=NavyMishap4NotResponsible.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_both_choices_end_career(self):
        for choice_cls in (NavyMishap4Responsible, NavyMishap4NotResponsible):
            events = [
                *self._setup_to_mishap(),
                Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
                Event(
                    id=7, fulfills=(6, 0), handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default)
                ),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, choice_cls


# ── event 5: advanced training ────────────────────────────────────────────────


class TestNavyEvent5:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=5)

    def test_creates_edu_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingAdvancedTrainingSkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == ['EDU']

    def test_success_creates_skill_choice_from_existing_skills(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        # Navy service skills auto-applied first career: Pilot, Vacc Suit, Athletics, Gunner, Mechanic, Gun Combat
        assert any(isinstance(o, Athletics) for o in pending.options)

    def test_failure_no_skill_choice(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_queues_career_progress(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        # On failure no skill choice created; _apply_skill_roll auto-queues advancement
        # (Navy at rank 0 can attempt commission, so may be PendingCommissionChoice)
        has_progress = any(
            isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs
        )
        assert has_progress


# ── event 10: abuse position for profit ──────────────────────────────────────


class TestNavyEvent10:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=10)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {NavyEvent10Profit, NavyEvent10Refuse}

    def test_profit_schedules_extra_benefit_roll(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=NavyEvent10Profit.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_refuse_schedules_advancement_dm_2(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=NavyEvent10Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 2

    def test_profit_no_advancement_dm(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=NavyEvent10Profit.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 0

    def test_both_choices_queue_career_progress(self):
        for choice_cls in (NavyEvent10Profit, NavyEvent10Refuse):
            events = [
                *self._setup_to_event(),
                Event(
                    id=7, fulfills=(6, 0), handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default)
                ),
            ]
            projection = replay(1, events)
            # Navy at rank 0 can attempt commission → PendingCommissionChoice; otherwise PendingAdvancement
            has_progress = any(
                isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs
            )
            assert has_progress, choice_cls


# ── muster out: choice benefit on last roll ───────────────────────────────────


class TestNavyMusterOutChoiceBenefit:
    """Navy muster out: when the last roll is a ChoiceBenefit, both PendingBenefitChoice
    and PendingCareerChoice must have distinct pending_ids so neither overwrites the other."""

    def _driver_through_muster_out(self) -> CharacterDriver:
        """Navy Line/Crew (SOC=5, can't commission), one term, muster out."""
        from ceres.character.domain.sophont import VILANI

        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD)
            .ucp('7869A5')  # SOC=5 → commission impossible; INT=9 DM+1 for qualif/survival
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Navy', 'Line/Crew', roll=5)  # INT 6+, DM+1, roll 5 → 6 ≥ 6 ✓
            .survive(roll=4)  # INT 5+, DM+1, 4 → 5 ≥ 5 ✓
            .term_event(roll=4)  # BenefitDm: no extra pending, just queues commission/advancement
            .commission(attempt=False)  # skip commission (SOC=5 < 8, would fail anyway)
            .advancement(roll=2)  # fail (Navy advancement varies; roll 2 always fails at SOC 5)
            .reenlist(reenlist=False)  # muster out
            .muster_out(table='benefits', roll=6)  # row 6 = ChoiceBenefit([Ship's Boat, Ship Share])
        )

    def test_last_muster_roll_choice_benefit_queues_benefit_pending(self):
        d = self._driver_through_muster_out()
        assert any(isinstance(p, PendingBenefitChoice) for p in d.projection.pending_inputs)

    def test_last_muster_roll_choice_benefit_does_not_yet_queue_career_choice(self):
        # Career choice is deferred until the benefit choice is resolved
        d = self._driver_through_muster_out()
        assert not any(isinstance(p, PendingCareerChoice) for p in d.projection.pending_inputs)

    def test_career_choice_queued_after_benefit_choice_resolved(self):
        d = self._driver_through_muster_out().benefit_choice(choice_index=0)
        career_choices = [p for p in d.projection.pending_inputs if isinstance(p, PendingCareerChoice)]
        assert len(career_choices) == 1
        assert career_choices[0].pending_id is not None

    def test_benefit_choice_resolves_without_affecting_career_choice(self):
        d = self._driver_through_muster_out().benefit_choice(choice_index=0)
        assert any(isinstance(p, PendingCareerChoice) for p in d.projection.pending_inputs)
        assert not any(isinstance(p, PendingBenefitChoice) for p in d.projection.pending_inputs)
