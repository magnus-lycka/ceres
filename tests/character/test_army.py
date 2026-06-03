"""Tests for the Army career — support, infantry, and cavalry assignments."""

from ceres.character.careers.army import PendingArmyEvent6SkillRoll, PendingArmyMishap4
from ceres.character.careers.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    PendingAdvancement,
    PendingMusterOut,
    PendingSkillChoice,
    SkillChoiceEvent,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, GunCombat, Leadership
from ceres.character.sophonts import VILANI
from ceres.character.state import Ally
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — EDU DM+2."""
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Sgt'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_army(assignment: str = 'Support', qual_roll: int = 5) -> list:
    """Through qualification — END 5+, END=6 DM+0, roll 5 → 5 ≥ 5."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Army', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Support', survive_roll: int = 5) -> list:
    """Army first career has Drive/Vacc Suit training choice before survival.

    Support survival: END 5+, DM+0, roll 5 → 5 ≥ 5 (pass).
    id=5 resolves the Drive/Vacc Suit training choice; id=6 is survival at '5.0'.
    """
    return [
        *_enter_army(assignment),
        SkillChoiceEvent(id=5, fulfills='4.0', skill=Drive()),
        SurviveEvent(id=6, fulfills='5.0', roll=survive_roll),
    ]


def _through_term_event(event_roll: int, assignment: str = 'Support') -> list:
    return [*_through_survive(assignment), TermEventEvent(id=7, fulfills='6.0', roll=event_roll)]


# ── qualification ─────────────────────────────────────────────────────────────


class TestArmyQualification:
    def test_success_enters_career(self):
        # END 5+, END=6, DM+0, roll 5 → 5 ≥ 5
        projection = replay(1, _enter_army())
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Army'

    def test_failure_clears_career(self):
        # END 5+, END=6, DM+0, roll 4 → 4 < 5
        projection = replay(1, _enter_army(qual_roll=4))
        assert projection.summary.current_career is None

    def test_all_three_assignments_accepted(self):
        for assignment in ('Support', 'Infantry', 'Cavalry'):
            projection = replay(1, _enter_army(assignment=assignment))
            assert projection.summary.current_assignment == assignment


# ── mishap 4: illegal activity ────────────────────────────────────────────────


class TestArmyMishap4:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_army(),
            SkillChoiceEvent(id=5, fulfills='4.0', skill=Drive()),
            SurviveEvent(id=6, fulfills='5.0', roll=4),  # END 5+, DM+0, 4 < 5 — fail
        ]

    def test_mishap_4_creates_choice_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=7, fulfills='6.0', roll=4)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingArmyMishap4)), None)
        assert pending is not None
        assert set(pending.options) == {'join_ring', 'cooperate'}

    def test_join_ring_adds_ally(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=7, fulfills='6.0', roll=4),
            CareerChoiceEvent(id=8, fulfills='7.0', choice='join_ring'),
        ]
        projection = replay(1, events)
        allies = [c for c in projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1

    def test_join_ring_ends_career(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=7, fulfills='6.0', roll=4),
            CareerChoiceEvent(id=8, fulfills='7.0', choice='join_ring'),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_join_ring_loses_benefit_roll(self):
        # 1 term + rank 0 normally = 1 muster roll; join_ring loses it → 0 muster rolls
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=7, fulfills='6.0', roll=4),
            CareerChoiceEvent(id=8, fulfills='7.0', choice='join_ring'),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_cooperate_no_ally(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=7, fulfills='6.0', roll=4),
            CareerChoiceEvent(id=8, fulfills='7.0', choice='cooperate'),
        ]
        projection = replay(1, events)
        allies = [c for c in projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 0

    def test_cooperate_keeps_benefit_roll(self):
        # 1 term + rank 0 = 1 muster roll; cooperate keeps it
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=7, fulfills='6.0', roll=4),
            CareerChoiceEvent(id=8, fulfills='7.0', choice='cooperate'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_cooperate_ends_career(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=7, fulfills='6.0', roll=4),
            CareerChoiceEvent(id=8, fulfills='7.0', choice='cooperate'),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None


# ── event 6: brutal ground war ────────────────────────────────────────────────


class TestArmyEvent6:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=6)

    def test_creates_edu_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingArmyEvent6SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == ['EDU']

    def test_success_creates_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=8, fulfills='7.0', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [GunCombat(), Leadership()]

    def test_success_no_injury_problem(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=8, fulfills='7.0', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert not any('injur' in p.lower() for p in projection.summary.problems)

    def test_failure_adds_injury_problem(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=8, fulfills='7.0', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() for p in projection.summary.problems)

    def test_failure_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=8, fulfills='7.0', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 8: advanced training ────────────────────────────────────────────────


class TestArmyEvent8:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=8)

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
            SkillRollEvent(id=8, fulfills='7.0', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        # Army service skills (auto-applied): Athletics, Gun Combat, Recon, Melee, Heavy Weapons
        assert any(isinstance(o, Athletics) for o in pending.options)

    def test_failure_no_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=8, fulfills='7.0', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=8, fulfills='7.0', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
