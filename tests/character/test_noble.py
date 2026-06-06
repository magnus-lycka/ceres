"""Tests for the Noble career — administrator, diplomat, and dilettante assignments."""

from ceres.character.domain.career.noble import (
    NobleEvent8Accept,
    NobleEvent8Refuse,
    NobleEvent8SkillRoll,
    PendingNobleMishap3SkillRoll,
    PendingNobleMishap5SkillRoll,
)
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Athletics, Carouse, Deception, Drive, Persuade, Stealth
from ceres.character.domain.sophont import VILANI
from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    PendingAdvancement,
    PendingChoices,
    PendingMusterOut,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.mechanism.replay import replay
from ceres.character.state import (
    Enemy,
    Rival,
)
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — INT DM+1."""
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Lord'),
        UcpEvent(id=2, fulfills=(1, 0), ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills=(2, 0), skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_noble(assignment: str = 'Administrator', qual_roll: int = 11) -> list:
    """SOC 10+, SOC=5, DM−1 → need roll 11 (11+(−1)=10 ≥ 10)."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills=(3, 0), career='Noble', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Administrator', survive_roll: int = 3) -> list:
    """Administrator: INT 4+, INT=9, DM+1 → need roll 3 (3+1=4 ≥ 4)."""
    return [*_enter_noble(assignment), SurviveEvent(id=5, fulfills=(4, 0), roll=survive_roll)]


def _through_term_event(event_roll: int, assignment: str = 'Administrator') -> list:
    return [*_through_survive(assignment), TermEventEvent(id=6, fulfills=(5, 0), roll=event_roll)]


# ── mishap 3: disaster or war ─────────────────────────────────────────────────


class TestNobleMishap3:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_noble(),
            SurviveEvent(id=5, fulfills=(4, 0), roll=2),  # natural 2 — auto-mishap
        ]

    def test_mishap_3_creates_skill_roll_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills=(5, 0), roll=3)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingNobleMishap3SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Stealth(), Deception()]

    def test_success_keeps_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills=(5, 0), roll=3),
            SkillRollEvent(id=7, fulfills=(6, 0), skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_failure_loses_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills=(5, 0), roll=3),
            SkillRollEvent(id=7, fulfills=(6, 0), skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_failure_adds_injury_problem(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills=(5, 0), roll=3),
            SkillRollEvent(id=7, fulfills=(6, 0), skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() or 'escape' in p.lower() for p in projection.summary.problems)

    def test_both_outcomes_end_career(self):
        for roll in (9, 7):
            events = [
                *self._setup_to_mishap(),
                MishapEvent(id=6, fulfills=(5, 0), roll=3),
                SkillRollEvent(id=7, fulfills=(6, 0), skill=Admin(), modified_roll=roll),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, f'roll={roll}'


# ── mishap 5: assassin attempt ────────────────────────────────────────────────


class TestNobleMishap5:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_noble(),
            SurviveEvent(id=5, fulfills=(4, 0), roll=2),
        ]

    def test_mishap_5_creates_end_roll_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills=(5, 0), roll=5)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingNobleMishap5SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Chars.END]

    def test_failure_adds_handler_injury_problem(self):
        # Handler adds a specific "apply the result" problem only on failure
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills=(5, 0), roll=5),
            SkillRollEvent(id=7, fulfills=(6, 0), skill=Chars.END, modified_roll=7),
        ]
        projection = replay(1, events)
        assert any('apply the result' in p.lower() for p in projection.summary.problems)

    def test_success_no_handler_injury_problem(self):
        # On success, handler does NOT add an extra problem (only standard mishap text is in problems)
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills=(5, 0), roll=5),
            SkillRollEvent(id=7, fulfills=(6, 0), skill=Chars.END, modified_roll=9),
        ]
        projection = replay(1, events)
        assert not any('apply the result' in p.lower() for p in projection.summary.problems)

    def test_both_outcomes_end_career(self):
        for roll in (9, 7):
            events = [
                *self._setup_to_mishap(),
                MishapEvent(id=6, fulfills=(5, 0), roll=5),
                SkillRollEvent(id=7, fulfills=(6, 0), skill=Chars.END, modified_roll=roll),
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
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(NobleEvent8Refuse, id=7, fulfills=(6, 0)),
        ]
        projection = replay(1, events)
        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_refuse_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(NobleEvent8Refuse, id=7, fulfills=(6, 0)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_skill_roll(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(NobleEvent8Accept, id=7, fulfills=(6, 0)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, NobleEvent8SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Deception(), Persuade()]

    def test_accept_success_adds_extra_benefit_roll(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(NobleEvent8Accept, id=7, fulfills=(6, 0)),
            SkillRollEvent(id=8, fulfills=(7, 0), skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_accept_success_continues_career(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(NobleEvent8Accept, id=7, fulfills=(6, 0)),
            SkillRollEvent(id=8, fulfills=(7, 0), skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Noble'

    def test_accept_failure_adds_enemy_and_ends_career(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(NobleEvent8Accept, id=7, fulfills=(6, 0)),
            SkillRollEvent(id=8, fulfills=(7, 0), skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1
        assert projection.summary.current_career is None
