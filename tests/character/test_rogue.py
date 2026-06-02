"""Tests for the Rogue career — thief, enforcer, and pirate assignments."""

from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    PendingAdvancement,
    PendingCareerChoice,
    PendingCareerEvent,
    PendingCareerSkillRoll,
    PendingMishap,
    PendingMusterOut,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, Streetwise
from ceres.character.sophonts import VILANI
from ceres.character.state import (
    Contact,
    Enemy,
    Rival,
)
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — DEX DM+1."""
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Riv'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_rogue(assignment: str = 'Thief', qual_roll: int = 6) -> list:
    """Through qualification — DEX 6+, DEX=8 DM+0, roll 6 → 6 ≥ 6."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Rogue', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Thief', survive_roll: int = 5) -> list:
    """Through survival — Thief DEX 6+, DM+1, roll 5 → 6 ≥ 6."""
    return [*_enter_rogue(assignment), SurviveEvent(id=5, fulfills='4.0', roll=survive_roll)]


def _through_term_event(event_roll: int) -> list:
    return [*_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=event_roll)]


# ── mishap 2: arrested → Prisoner ────────────────────────────────────────────


class TestRogueMishap2:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_rogue(),
            SurviveEvent(id=5, fulfills='4.0', roll=4),  # DEX 6+, DM+1, 4 → 5 < 6 — fail
        ]

    def test_mishap_2_creates_mishap_pending(self):
        projection = replay(1, self._setup_to_mishap())
        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_mishap_2_forces_prisoner_as_only_career_choice(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=2)]
        projection = replay(1, events)
        # forced_next_career is immediately consumed into PendingCareerChoice with Prisoner as only option
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert pending.options == ['Prisoner']

    def test_mishap_2_ends_career(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=2)]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_mishap_2_no_muster_out_in_first_term(self):
        # Mishap in first term with lose_current_term=True → term_count(1) + rank(0) - 1 = 0 rolls
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=2)]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── mishap 3: betrayed by a friend ───────────────────────────────────────────


class TestRogueMishap3:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_rogue(),
            SurviveEvent(id=5, fulfills='4.0', roll=4),  # Thief INT 6+, DM+1, 4→5 < 6 — fail
        ]

    def test_mishap_3_queues_prisoner_roll_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=3)]
        projection = replay(1, events)
        pending = next(
            (
                p
                for p in projection.pending_inputs
                if isinstance(p, PendingCareerSkillRoll) and p.context == 'rogue_mishap_3_prisoner_check'
            ),
            None,
        )
        assert pending is not None

    def test_mishap_3_no_contacts_adds_rival(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=3)]
        projection = replay(1, events)
        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_mishap_3_prisoner_roll_2_forces_prisoner(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            SkillRollEvent(
                id=7, fulfills='6.0', context='rogue_mishap_3_prisoner_check', skill=Streetwise(), modified_roll=2
            ),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert pending.options == ['Prisoner']

    def test_mishap_3_prisoner_roll_other_no_forced_prisoner(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            SkillRollEvent(
                id=7, fulfills='6.0', context='rogue_mishap_3_prisoner_check', skill=Streetwise(), modified_roll=5
            ),
        ]
        projection = replay(1, events)
        prisoner_pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice) and p.options == ['Prisoner']),
            None,
        )
        assert prisoner_pending is None

    def test_mishap_3_ends_career(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            SkillRollEvent(
                id=7, fulfills='6.0', context='rogue_mishap_3_prisoner_check', skill=Streetwise(), modified_roll=5
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None


# ── event 3: arrested and charged ────────────────────────────────────────────


class TestRogueEvent3:
    def _setup_to_event(self) -> list:
        return [*_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=3)]

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 3),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'defend', 'lawyer'}

    def test_lawyer_queues_advancement_and_schedules_benefit_reduction(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_3', choice='lawyer'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        reduce_effects = [se for se in projection.scheduled_effects if se.trigger == 'muster_out_reduce']
        assert len(reduce_effects) == 1

    def test_lawyer_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_3', choice='lawyer'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_defend_creates_advocate_skill_roll(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_3', choice='defend'),
        ]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)),
            None,
        )
        assert pending is not None
        assert 'Advocate' in pending.options

    def test_defend_success_continues_career(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_3', choice='defend'),
            SkillRollEvent(id=8, fulfills='7.0', context='rogue_event_3_skill', skill=Streetwise(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Rogue'

    def test_defend_success_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_3', choice='defend'),
            SkillRollEvent(id=8, fulfills='7.0', context='rogue_event_3_skill', skill=Streetwise(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_defend_failure_ends_career(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_3', choice='defend'),
            SkillRollEvent(id=8, fulfills='7.0', context='rogue_event_3_skill', skill=Streetwise(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_defend_failure_forces_prisoner_as_only_career_choice(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_3', choice='defend'),
            SkillRollEvent(id=8, fulfills='7.0', context='rogue_event_3_skill', skill=Streetwise(), modified_roll=7),
        ]
        projection = replay(1, events)
        # forced_next_career is consumed into PendingCareerChoice(options=['Prisoner'])
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert pending.options == ['Prisoner']


# ── event 6: backstab fellow rogue ───────────────────────────────────────────


class TestRogueEvent6:
    def _setup_to_event(self) -> list:
        return [*_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=6)]

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 6),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'backstab', 'refuse'}

    def test_backstab_adds_enemy(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_6', choice='backstab'),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_backstab_schedules_advancement_dm(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_6', choice='backstab'),
        ]
        projection = replay(1, events)
        dm_effects = [se for se in projection.scheduled_effects if se.trigger == 'advancement']
        assert any(se.effect.get('amount') == 2 for se in dm_effects)

    def test_refuse_adds_contact(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_6', choice='refuse'),
        ]
        projection = replay(1, events)
        contacts = [c for c in projection.summary.connections if isinstance(c, Contact)]
        assert len(contacts) >= 1

    def test_refuse_no_enemy(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_6', choice='refuse'),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 0

    def test_both_choices_queue_advancement(self):
        for choice in ('backstab', 'refuse'):
            events = [
                *self._setup_to_event(),
                CareerChoiceEvent(id=7, fulfills='6.0', context='rogue_event_6', choice=choice),
            ]
            projection = replay(1, events)
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs), choice


# ── event 9: feud with rival organisation ────────────────────────────────────


class TestRogueEvent9:
    def _setup_to_event(self) -> list:
        return [*_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=9)]

    def test_creates_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 9),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'Stealth', 'Gun Combat'}

    def test_success_schedules_extra_benefit_roll(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='rogue_event_9', skill=Streetwise(), modified_roll=9),
        ]
        projection = replay(1, events)
        add_effects = [se for se in projection.scheduled_effects if se.trigger == 'muster_out_add']
        assert len(add_effects) == 1

    def test_failure_adds_injury_problem(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='rogue_event_9', skill=Streetwise(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() for p in projection.summary.problems)

    def test_success_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='rogue_event_9', skill=Streetwise(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='rogue_event_9', skill=Streetwise(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
