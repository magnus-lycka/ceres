"""Tests for the Noble career — administrator, diplomat, and dilettante assignments."""

from ceres.character.domain.career import NOBLE
from ceres.character.domain.career.career_events import (
    CareerChoiceHandler,
    CareerEntryHandler,
    MishapHandler,
    PendingAdvancement,
    PendingChoices,
    PendingMusterOut,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.noble import (
    NobleEvent8Accept,
    NobleEvent8Refuse,
    NobleEvent8SkillRoll,
    PendingNobleMishap3SkillRoll,
    PendingNobleMishap5SkillRoll,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import (
    Enemy,
    Rival,
)
from ceres.character.domain.skills import Admin, Athletics, Carouse, Deception, Drive, Persuade, Stealth
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD, CharacterDriver


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — INT DM+1."""
    started = Event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Lord'))
    ucp = Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(
        fulfills=(ucp.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    return [started, ucp, background]


def _enter_noble(assignment: str = 'Administrator', qual_roll: int = 11) -> list:
    """SOC 10+, SOC=5, DM−1 → need roll 11 (11+(−1)=10 ≥ 10)."""
    base = _setup()
    entry = Event(
        fulfills=(base[-1].id, 0),
        handler=CareerEntryHandler(career=NOBLE, assignment=NOBLE.assignment(assignment), qualification_roll=qual_roll),
    )
    return [
        *base,
        entry,
    ]


def _through_survive(assignment: str = 'Administrator', survive_roll: int = 3) -> list:
    """Administrator: INT 4+, INT=9, DM+1 → need roll 3 (3+1=4 ≥ 4)."""
    base = _enter_noble(assignment)
    return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Administrator') -> list:
    base = _through_survive(assignment)
    return [*base, Event(fulfills=(base[-1].id, 0), handler=TermEventHandler(roll=event_roll))]


class TestNobleDirectOutcomeRows:
    def test_mishap_2_decreases_soc_and_ends_career(self):
        base = _enter_noble()
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=2))
        projection = replay(1, [*base, survive, Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=2))])

        assert projection.summary.characteristics[Chars.SOC] == 4
        assert projection.summary.current_career is None

    def test_event_5_adds_benefit_dm(self):
        projection = replay(1, _through_term_event(5))

        dms = projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms
        assert len(dms) == 1
        assert dms[0].amount == 1


# ── mishap 3: disaster or war ─────────────────────────────────────────────────


class TestNobleMishap3:
    def _setup_to_mishap(self) -> list:
        base = _enter_noble()
        return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=2))]

    def test_mishap_3_creates_skill_roll_pending(self):
        base = self._setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingNobleMishap3SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Stealth(), Deception()]

    def test_success_keeps_benefit_roll(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_failure_loses_benefit_roll(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_failure_adds_injury_problem(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() or 'escape' in p.lower() for p in projection.summary.problems)

    def test_both_outcomes_end_career(self):
        for roll in (9, 7):
            base = self._setup_to_mishap()
            mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=3))
            events = [
                *base,
                mishap,
                Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=roll)),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, f'roll={roll}'


# ── mishap 5: assassin attempt ────────────────────────────────────────────────


class TestNobleMishap5:
    def _setup_to_mishap(self) -> list:
        base = _enter_noble()
        return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=2))]

    def test_mishap_5_creates_end_roll_pending(self):
        base = self._setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingNobleMishap5SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Chars.END]

    def test_failure_adds_handler_injury_problem(self):
        # Handler adds a specific "apply the result" problem only on failure
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Chars.END, modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any('apply the result' in p.lower() for p in projection.summary.problems)

    def test_success_no_handler_injury_problem(self):
        # On success, handler does NOT add an extra problem (only standard mishap text is in problems)
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Chars.END, modified_roll=9)),
        ]
        projection = replay(1, events)
        assert not any('apply the result' in p.lower() for p in projection.summary.problems)

    def test_both_outcomes_end_career(self):
        for roll in (9, 7):
            base = self._setup_to_mishap()
            mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
            events = [
                *base,
                mishap,
                Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Chars.END, modified_roll=roll)),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, f'roll={roll}'


# ── event 8: conspiracy recruitment ──────────────────────────────────────────


class TestNobleEvent8:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=8)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {NobleEvent8Accept, NobleEvent8Refuse}

    def test_refuse_adds_rival(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=NobleEvent8Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_refuse_queues_advancement(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=NobleEvent8Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_skill_roll(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=NobleEvent8Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, NobleEvent8SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Deception(), Persuade()]

    def test_accept_success_adds_extra_benefit_roll(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=NobleEvent8Accept.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_accept_success_continues_career(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=NobleEvent8Accept.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Noble'

    def test_accept_failure_adds_enemy_and_ends_career(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=NobleEvent8Accept.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1
        assert projection.summary.current_career is None


# ── mishap 1: severely injured ────────────────────────────────────────────────


class TestNobleMishap1:
    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Noble', 'Administrator', roll=11)
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}
