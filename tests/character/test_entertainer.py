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
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.entertainer import (
    EntertainerEvent8Accept,
    EntertainerEvent8Refuse,
    PendingEntertainerEvent3SkillRoll,
    PendingEntertainerEvent8SkillRoll,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import Enemy, Rival
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
from tests.character.helpers import MOCK_WORLD, CharacterDriver


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5."""
    ev1 = Event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Star'))
    ev2 = Event(fulfills=(ev1.id, 0), handler=UcpHandler(ucp='7869A5'))
    return [
        ev1,
        ev2,
        Event(fulfills=(ev2.id, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])),
    ]


def _enter_entertainer(assignment: str = 'Artist', qual_roll: int = 4) -> list:
    """INT 5+, qualification_dm = max(DEX_dm=0, INT_dm=1) = 1 → need roll 4 (4+1=5 ≥ 5).
    Entertainer service_skills include Art (broad category) → PendingInitialTrainingChoice at '4.0'.
    Resolve with PerformingArt; PendingSurvive queued at '5.0'.
    """
    _base = _setup()
    ev4 = Event(
        fulfills=(_base[-1].id, 0),
        handler=CareerEntryHandler(
            career=ENTERTAINER, assignment=ENTERTAINER.assignment(assignment), qualification_roll=qual_roll
        ),
    )
    return [
        *_base,
        ev4,
        Event(fulfills=(ev4.id, 0), handler=SkillChoiceHandler(skill=PerformingArt())),
    ]


def _through_survive(assignment: str = 'Artist', survive_roll: int = 7) -> list:
    """Artist: SOC 6+, SOC=5, DM−1 → need roll 7 (7+(−1)=6 ≥ 6)."""
    _enter = _enter_entertainer(assignment)
    return [*_enter, Event(fulfills=(_enter[-1].id, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Artist') -> list:
    _surv = _through_survive(assignment)
    return [*_surv, Event(fulfills=(_surv[-1].id, 0), handler=TermEventHandler(roll=event_roll))]


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
        _base = self._setup_to_event()
        events = [
            *_base,
            Event(fulfills=(_base[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        from ceres.character.domain.characteristics import Chars

        assert projection.summary.characteristics[Chars.SOC] == 6  # SOC was 5; +1 = 6

    def test_failure_decreases_soc(self):
        _base = self._setup_to_event()
        events = [
            *_base,
            Event(fulfills=(_base[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        from ceres.character.domain.characteristics import Chars

        assert projection.summary.characteristics[Chars.SOC] == 4  # SOC was 5; −1 = 4

    def test_both_outcomes_queue_advancement(self):
        for roll in (9, 7):
            _base = self._setup_to_event()
            events = [
                *_base,
                Event(fulfills=(_base[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=roll)),
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
        _base = self._setup_to_event()
        events = [
            *_base,
            Event(
                fulfills=(_base[-1].id, 0),
                handler=CareerChoiceHandler(choice=EntertainerEvent8Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_art_or_investigate_roll(self):
        _base = self._setup_to_event()
        events = [
            *_base,
            Event(
                fulfills=(_base[-1].id, 0),
                handler=CareerChoiceHandler(choice=EntertainerEvent8Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingEntertainerEvent8SkillRoll)), None)
        assert pending is not None
        assert pending.options == [PerformingArt(), CreativeArt(), PresentationArt(), Investigate()]

    def test_accept_success_schedules_advancement_dm_2(self):
        _base = self._setup_to_event()
        ev8 = Event(
            fulfills=(_base[-1].id, 0),
            handler=CareerChoiceHandler(choice=EntertainerEvent8Accept.model_fields['kind'].default),
        )
        events = [
            *_base,
            ev8,
            Event(fulfills=(ev8.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 2

    def test_accept_failure_adds_enemy(self):
        _base = self._setup_to_event()
        ev8 = Event(
            fulfills=(_base[-1].id, 0),
            handler=CareerChoiceHandler(choice=EntertainerEvent8Accept.model_fields['kind'].default),
        )
        events = [
            *_base,
            ev8,
            Event(fulfills=(ev8.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_both_accept_outcomes_queue_advancement(self):
        for roll in (9, 7):
            _base = self._setup_to_event()
            ev8 = Event(
                fulfills=(_base[-1].id, 0),
                handler=CareerChoiceHandler(choice=EntertainerEvent8Accept.model_fields['kind'].default),
            )
            events = [
                *_base,
                ev8,
                Event(fulfills=(ev8.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=roll)),
            ]
            projection = replay(1, events)
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs), f'roll={roll}'


# ── mishap 1: severely injured ────────────────────────────────────────────────


class TestEntertainerMishap1:
    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Entertainer', 'Artist', roll=4)
        d.initial_training(PerformingArt())
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}


class TestEntertainerDirectOutcomeRows:
    def _driver(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Star')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Entertainer', 'Artist', roll=4)
            .initial_training(PerformingArt())
        )

    def test_mishap_3_decreases_soc_and_ends_career(self):
        driver = self._driver().survive(2).mishap(3)

        assert driver.projection.summary.characteristics[Chars.SOC] == 4
        assert driver.projection.summary.current_career is None

    def test_mishap_4_adds_rival_and_ends_career(self):
        driver = self._driver().survive(2).mishap(4)

        assert any(isinstance(c, Rival) for c in driver.projection.summary.connections)
        assert driver.projection.summary.current_career is None

    def test_event_5_adds_benefit_dm(self):
        projection = self._driver().survive(7).term_event(5).projection

        dms = projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms
        assert len(dms) == 1
        assert dms[0].amount == 1


# ── mishap 6: censorship or controversy ──────────────────────────────────────


class TestEntertainerMishap6:
    def _setup_to_mishap(self) -> CharacterDriver:
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Entertainer', 'Artist', roll=4)
        d.initial_training(PerformingArt())
        d.survive(2)  # Artist SOC 6+, DM−1; roll 2 → 1 < 6 — fail
        d.mishap(6)
        return d

    def test_grants_qualification_dm_plus_2(self):
        d = self._setup_to_mishap()
        assert d.projection.pending_qualification_dm == 2

    def test_does_not_set_advancement_dm(self):
        d = self._setup_to_mishap()
        assert d.projection.pending_advancement_dm == 0
