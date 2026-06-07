"""Tests for the Entertainer career — artist, journalist, and performer assignments."""

from ceres.character.domain.career import ENTERTAINER
from ceres.character.domain.career.career_events import (
    CareerChoiceHandler,
    CareerEntryHandler,
    PendingAdvancement,
    PendingChoices,
    SkillChoiceHandler,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.entertainer import (
    EntertainerEvent8Accept,
    EntertainerEvent8Refuse,
    PendingEntertainerEvent3SkillRoll,
    PendingEntertainerEvent8SkillRoll,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.connection import Enemy
from ceres.character.domain.skills import (
    Admin,
    Athletics,
    Carouse,
    CreativeArt,
    Drive,
    Investigate,
    PerformingArt,
    PresentationArt,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5."""
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Star')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
    ]


def _enter_entertainer(assignment: str = 'Artist', qual_roll: int = 4) -> list:
    """INT 5+, qualification_dm = max(DEX_dm=0, INT_dm=1) = 1 → need roll 4 (4+1=5 ≥ 5).
    Entertainer service_skills include Art (broad category) → PendingInitialTrainingChoice at '4.0'.
    Resolve with PerformingArt; PendingSurvive queued at '5.0'.
    """
    return [
        *_setup(),
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(
                career=ENTERTAINER, assignment=ENTERTAINER.assignment(assignment), qualification_roll=qual_roll
            ),
        ),
        Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=PerformingArt())),
    ]


def _through_survive(assignment: str = 'Artist', survive_roll: int = 7) -> list:
    """Artist: SOC 6+, SOC=5, DM−1 → need roll 7 (7+(−1)=6 ≥ 6)."""
    return [*_enter_entertainer(assignment), Event(id=6, fulfills=(5, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Artist') -> list:
    return [*_through_survive(assignment), Event(id=7, fulfills=(6, 0), handler=TermEventHandler(roll=event_roll))]


# ── event 3: controversial exhibition ────────────────────────────────────────


class TestEntertainerEvent3:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=3)

    def test_creates_art_or_investigate_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingEntertainerEvent3SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [PerformingArt(), CreativeArt(), PresentationArt(), Investigate()]

    def test_success_increases_soc(self):
        events = [
            *self._setup_to_event(),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        from ceres.character.domain.characteristics import Chars

        assert projection.summary.characteristics[Chars.SOC] == 6  # SOC was 5; +1 = 6

    def test_failure_decreases_soc(self):
        events = [
            *self._setup_to_event(),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        from ceres.character.domain.characteristics import Chars

        assert projection.summary.characteristics[Chars.SOC] == 4  # SOC was 5; −1 = 4

    def test_both_outcomes_queue_advancement(self):
        for roll in (9, 7):
            events = [
                *self._setup_to_event(),
                Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=roll)),
            ]
            projection = replay(1, events)
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs), f'roll={roll}'


# ── event 8: criticise political leader ──────────────────────────────────────


class TestEntertainerEvent8:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=8)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {EntertainerEvent8Accept, EntertainerEvent8Refuse}

    def test_refuse_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=8,
                fulfills=(7, 0),
                handler=CareerChoiceHandler(choice=EntertainerEvent8Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_art_or_investigate_roll(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=8,
                fulfills=(7, 0),
                handler=CareerChoiceHandler(choice=EntertainerEvent8Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingEntertainerEvent8SkillRoll)), None)
        assert pending is not None
        assert pending.options == [PerformingArt(), CreativeArt(), PresentationArt(), Investigate()]

    def test_accept_success_schedules_advancement_dm_2(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=8,
                fulfills=(7, 0),
                handler=CareerChoiceHandler(choice=EntertainerEvent8Accept.model_fields['kind'].default),
            ),
            Event(id=9, fulfills=(8, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 2

    def test_accept_failure_adds_enemy(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=8,
                fulfills=(7, 0),
                handler=CareerChoiceHandler(choice=EntertainerEvent8Accept.model_fields['kind'].default),
            ),
            Event(id=9, fulfills=(8, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_both_accept_outcomes_queue_advancement(self):
        for roll in (9, 7):
            events = [
                *self._setup_to_event(),
                Event(
                    id=8,
                    fulfills=(7, 0),
                    handler=CareerChoiceHandler(choice=EntertainerEvent8Accept.model_fields['kind'].default),
                ),
                Event(id=9, fulfills=(8, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=roll)),
            ]
            projection = replay(1, events)
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs), f'roll={roll}'
