"""Tests for the Rogue career — thief, enforcer, and pirate assignments."""

from ceres.character.domain.career import ROGUE
from ceres.character.domain.career.career_events import (
    CareerChoiceHandler,
    CareerEntryHandler,
    MishapHandler,
    PendingAdvancement,
    PendingCareerChoice,
    PendingChoices,
    PendingMishap,
    PendingMusterOut,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.rogue import (
    PendingRogueEvent9SkillRoll,
    RogueEvent3Defend,
    RogueEvent3Lawyer,
    RogueEvent3SkillRoll,
    RogueEvent6Backstab,
    RogueEvent6Refuse,
    RogueMishap3RollOther,
    RogueMishap3RollTwo,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.connection import Contact, Enemy, Rival
from ceres.character.domain.skills import Admin, Advocate, Athletics, Carouse, Drive, GunCombat, Stealth, Streetwise
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD, CharacterDriver


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — DEX DM+1."""
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Riv')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
    ]


def _enter_rogue(assignment: str = 'Thief', qual_roll: int = 6) -> list:
    """Through qualification — DEX 6+, DEX=8 DM+0, roll 6 → 6 ≥ 6."""
    return [
        *_setup(),
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(
                career=ROGUE, assignment=ROGUE.assignment(assignment), qualification_roll=qual_roll
            ),
        ),
    ]


def _through_survive(assignment: str = 'Thief', survive_roll: int = 5) -> list:
    """Through survival — Thief DEX 6+, DM+1, roll 5 → 6 ≥ 6."""
    return [*_enter_rogue(assignment), Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int) -> list:
    return [*_through_survive(), Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=event_roll))]


# ── mishap 2: arrested → Prisoner ────────────────────────────────────────────


class TestRogueMishap2:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_rogue(),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=4)),  # DEX 6+, DM+1, 4 → 5 < 6 — fail
        ]

    def test_mishap_2_creates_mishap_pending(self):
        projection = replay(1, self._setup_to_mishap())
        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_mishap_2_forces_prisoner_as_only_career_choice(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=2))]
        projection = replay(1, events)
        # forced_next_career is immediately consumed into PendingCareerChoice with Prisoner as only option
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert [c.name for c in pending.options] == ['Prisoner']

    def test_mishap_2_ends_career(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=2))]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_mishap_2_no_muster_out_in_first_term(self):
        # Mishap in first term with lose_current_term=True → term_count(1) + rank(0) - 1 = 0 rolls
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=2))]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── mishap 3: betrayed by a friend ───────────────────────────────────────────


class TestRogueMishap3:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_rogue(),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=4)),  # Thief INT 6+, DM+1, 4→5 < 6 — fail
        ]

    def test_mishap_3_queues_prisoner_roll_pending(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3))]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None

    def test_mishap_3_no_contacts_adds_rival(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3))]
        projection = replay(1, events)
        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_mishap_3_prisoner_roll_2_forces_prisoner(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueMishap3RollTwo.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert [c.name for c in pending.options] == ['Prisoner']

    def test_mishap_3_prisoner_roll_other_no_forced_prisoner(self):
        events = [
            *self._setup_to_mishap(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueMishap3RollOther.model_fields['kind'].default),
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
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueMishap3RollOther.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_mishap_3_existing_contact_is_converted_to_rival(self):
        from ceres.character.domain.career.rogue import RogueMishap3Handler
        from ceres.character.domain.sophont import VILANI
        from tests.character.helpers import MOCK_WORLD

        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        proj.summary.connections.append(Contact(source='Old friend'))
        RogueMishap3Handler.handle(proj, event_id=5, pending_idx=0)

        contacts = [c for c in proj.summary.connections if isinstance(c, Contact)]
        rivals = [c for c in proj.summary.connections if isinstance(c, Rival)]
        assert len(contacts) == 0
        assert len(rivals) == 1
        assert 'contact' in rivals[0].source.lower()


# ── event 3: arrested and charged ────────────────────────────────────────────


class TestRogueEvent3:
    def _setup_to_event(self) -> list:
        return [*_through_survive(), Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=3))]

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {RogueEvent3Defend, RogueEvent3Lawyer}

    def test_lawyer_queues_advancement_and_schedules_benefit_reduction(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Lawyer.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        assert projection.summary.career_terms[-1].require_muster_out().lost_rolls == 1

    def test_lawyer_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Lawyer.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_defend_creates_advocate_skill_roll(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, RogueEvent3SkillRoll)),
            None,
        )
        assert pending is not None
        assert Advocate() in pending.options

    def test_defend_success_continues_career(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Rogue'

    def test_defend_success_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_defend_failure_ends_career(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_defend_failure_forces_prisoner_as_only_career_choice(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
        ]
        projection = replay(1, events)
        # forced_next_career is consumed into PendingCareerChoice(options=['Prisoner'])
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert [c.name for c in pending.options] == ['Prisoner']


# ── event 6: backstab fellow rogue ───────────────────────────────────────────


class TestRogueEvent6:
    def _setup_to_event(self) -> list:
        return [*_through_survive(), Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=6))]

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {RogueEvent6Backstab, RogueEvent6Refuse}

    def test_backstab_adds_enemy(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent6Backstab.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_backstab_schedules_advancement_dm(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent6Backstab.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 2

    def test_refuse_adds_contact(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent6Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        contacts = [c for c in projection.summary.connections if isinstance(c, Contact)]
        assert len(contacts) >= 1

    def test_refuse_no_enemy(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=RogueEvent6Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 0

    def test_both_choices_queue_advancement(self):
        for choice_cls in (RogueEvent6Backstab, RogueEvent6Refuse):
            events = [
                *self._setup_to_event(),
                Event(
                    id=7, fulfills=(6, 0), handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default)
                ),
            ]
            projection = replay(1, events)
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs), choice_cls


# ── event 9: feud with rival organisation ────────────────────────────────────


class TestRogueEvent9:
    def _setup_to_event(self) -> list:
        return [*_through_survive(), Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=9))]

    def test_creates_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingRogueEvent9SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [Stealth(), GunCombat()]

    def test_success_schedules_extra_benefit_roll(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_failure_adds_injury_problem(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() for p in projection.summary.problems)

    def test_success_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── mishap 1: severely injured ────────────────────────────────────────────────


class TestRogueMishap1:
    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Rogue', 'Thief', roll=6)
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}
