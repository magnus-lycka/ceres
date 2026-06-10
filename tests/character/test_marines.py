"""Tests for the Marines career — support, ground assault, and star marine assignments."""

from ceres.character.domain.career import MARINES
from ceres.character.domain.career.career_events import (
    CareerChoiceHandler,
    CareerEntryHandler,
    MishapHandler,
    PendingAdvancement,
    PendingChoices,
    PendingCommissionChoice,
    PendingMusterOut,
    PendingSkillChoice,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.career.marines import (
    MarinesEvent9Protect,
    MarinesEvent9Report,
    MarinesMishap4Accept,
    MarinesMishap4Refuse,
    PendingMarinesEvent6SkillRoll,
    PendingMarinesMishap4SkillRoll,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.connection import (
    Ally,
    Contact,
    Enemy,
)
from ceres.character.domain.skills import (
    Admin,
    Athletics,
    Carouse,
    Deception,
    Drive,
    GunCombat,
    Leadership,
    Melee,
    Persuade,
    Tactics,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD, CharacterDriver


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — EDU DM+2."""
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Cpl')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
    ]


def _enter_marines(assignment: str = 'Support', qual_roll: int = 6) -> list:
    """Through qualification — END 6+, END=6 DM+0, roll 6 → 6 ≥ 6."""
    return [
        *_setup(),
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(
                career=MARINES, assignment=MARINES.assignment(assignment), qualification_roll=qual_roll
            ),
        ),
    ]


def _through_survive(assignment: str = 'Support', survive_roll: int = 5) -> list:
    """Marines service_skills are all single-choice — survival queued at '4.0'.

    Support survival: END 5+, DM+0, roll 5 → 5 ≥ 5 (pass).
    """
    return [*_enter_marines(assignment), Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Support') -> list:
    return [*_through_survive(assignment), Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=event_roll))]


# ── mishap 4: black ops mission ───────────────────────────────────────────────


class TestMarinesMishap4:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_marines(),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=4)),  # END 5+, DM+0, 4 < 5 — fail
        ]

    def test_mishap_4_creates_choice_pending(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {MarinesMishap4Refuse, MarinesMishap4Accept}

    def test_refuse_adds_contact(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesMishap4Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        contacts = [c for c in projection.summary.connections if isinstance(c, Contact)]
        assert len(contacts) == 1

    def test_refuse_ends_career_and_loses_benefit(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesMishap4Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_accept_creates_skill_roll(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesMishap4Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingMarinesMishap4SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Deception(), Persuade()]

    def test_accept_success_continues_career(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesMishap4Accept.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Marines'

    def test_accept_failure_ends_career_and_loses_benefit(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesMishap4Accept.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── event 5: advanced training ────────────────────────────────────────────────


class TestMarinesEvent5:
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

    def test_success_creates_skill_choice_with_existing_skills(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        # Marines service skills (auto-applied first career): Athletics, Vacc Suit, Tactics, etc.
        assert any(isinstance(o, Athletics) for o in pending.options)

    def test_failure_no_skill_choice(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        # On failure no skill choice is created, so _apply_skill_roll auto-queues advancement
        # (Marines at rank 0 can attempt commission, so may be PendingCommissionChoice)
        has_progress = any(
            isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs
        )
        assert has_progress


# ── event 6: assault on an enemy fortress ────────────────────────────────────


class TestMarinesEvent6:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=6)

    def test_creates_melee_or_gun_combat_skill_roll(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingMarinesEvent6SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [Melee(), GunCombat()]

    def test_success_creates_tactics_or_leadership_choice(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [Tactics(), Leadership()]

    def test_failure_adds_injury_problem(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() for p in projection.summary.problems)

    def test_failure_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 9: mission goes wrong ───────────────────────────────────────────────


class TestMarinesEvent9:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=9)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {MarinesEvent9Report, MarinesEvent9Protect}

    def test_report_adds_enemy(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesEvent9Report.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_report_schedules_advancement_dm_2(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesEvent9Report.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 2

    def test_protect_adds_ally(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesEvent9Protect.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        allies = [c for c in projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1

    def test_protect_schedules_advancement_dm_1(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MarinesEvent9Protect.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 1

    def test_both_choices_queue_career_progress(self):
        for choice_cls in (MarinesEvent9Report, MarinesEvent9Protect):
            events = [
                *self._setup_to_event(),
                Event(
                    id=7, fulfills=(6, 0), handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default)
                ),
            ]
            projection = replay(1, events)
            # Marines at rank 0 can attempt commission → PendingCommissionChoice; otherwise PendingAdvancement
            has_progress = any(
                isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs
            )
            assert has_progress, choice_cls


# ── mishap 1: severely injured ────────────────────────────────────────────────


class TestMarinesMishap1:
    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Marines', 'Support', roll=6)
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}
