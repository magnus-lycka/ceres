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
    PendingRogueBetrayal,
    PendingRogueEvent9SkillRoll,
    RogueBetrayalHandler,
    RogueEvent3Defend,
    RogueEvent3Lawyer,
    RogueEvent3SkillRoll,
    RogueEvent6Backstab,
    RogueEvent6Refuse,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, UcpHandler
from ceres.character.domain.connection import Contact, Enemy
from ceres.character.domain.skills import (
    Admin,
    Advocate,
    Athletics,
    Carouse,
    Drive,
    Gambler,
    GunCombat,
    Level,
    Stealth,
    Streetwise,
    Tactics,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver, _creation_events


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — DEX DM+1."""
    c = _creation_events(VILANI, MOCK_WORLD, 'NPC', 'Riv')
    ucp = Event(fulfills=(c[-1].id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(
        fulfills=(ucp.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    return [*c, ucp, background]


def _enter_rogue(assignment: str = 'Thief', qual_roll: int = 6) -> list:
    """Through qualification — DEX 6+, DEX=8 DM+0, roll 6 → 6 ≥ 6."""
    base = _setup()
    entry = Event(
        fulfills=(base[-1].id, 0),
        handler=CareerEntryHandler(career=ROGUE, assignment=ROGUE.assignment(assignment), qualification_roll=qual_roll),
    )
    return [
        *base,
        entry,
    ]


def _through_survive(assignment: str = 'Thief', survive_roll: int = 5) -> list:
    """Through survival — Thief DEX 6+, DM+1, roll 5 → 6 ≥ 6."""
    base = _enter_rogue(assignment)
    return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int) -> list:
    base = _through_survive()
    return [*base, Event(fulfills=(base[-1].id, 0), handler=TermEventHandler(roll=event_roll))]


class TestRogueDirectOutcomeRows:
    def test_mishap_5_adds_enemy_and_ends_career(self):
        base = _enter_rogue()
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=4))
        projection = replay(1, [*base, survive, Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=5))])

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)
        assert projection.summary.current_career is None

    def test_event_10_grants_gambler_1(self):
        projection = replay(1, _through_term_event(10))

        assert projection.summary.skill_level(Gambler) == 1


# ── mishap 2: arrested → Prisoner ────────────────────────────────────────────


class TestRogueMishap2:
    def _setup_to_mishap(self) -> list:
        base = _enter_rogue()
        return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=4))]

    def test_mishap_2_creates_mishap_pending(self):
        projection = replay(1, self._setup_to_mishap())
        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_mishap_2_forces_prisoner_as_only_career_choice(self):
        base = self._setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=2))]
        projection = replay(1, events)
        # forced_next_career is immediately consumed into PendingCareerChoice with Prisoner as only option
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert [c.name for c in pending.options] == ['Prisoner']

    def test_mishap_2_ends_career(self):
        base = self._setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=2))]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_mishap_2_no_muster_out_in_first_term(self):
        # Mishap in first term with lose_current_term=True → term_count(1) + rank(0) - 1 = 0 rolls
        base = self._setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=2))]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── mishap 3: betrayed by a friend ───────────────────────────────────────────


class TestRogueMishap3:
    def test_form_captures_relationship_identity_and_raw_prison_roll(self):
        pending = PendingRogueBetrayal(pending_id=(5, 0))
        event = pending.event_from_form({'relationship': 'enemy', 'connection_index': '1', 'roll': '2'})
        assert event.fulfills == (5, 0)
        assert event.handler == RogueBetrayalHandler(relationship='enemy', connection_index=1, roll=2)


# ── event 3: arrested and charged ────────────────────────────────────────────


class TestRogueEvent3:
    def _setup_to_event(self) -> list:
        return _through_term_event(3)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {RogueEvent3Defend, RogueEvent3Lawyer}

    def test_lawyer_queues_advancement_and_schedules_benefit_reduction(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Lawyer.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        assert projection.summary.career_terms[-1].require_muster_out().lost_rolls == 1

    def test_lawyer_queues_advancement(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=RogueEvent3Lawyer.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_defend_creates_advocate_skill_roll(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
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
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Rogue'

    def test_defend_success_creates_advancement_pending(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_defend_failure_ends_career(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_defend_failure_forces_prisoner_as_only_career_choice(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=RogueEvent3Defend.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
        ]
        projection = replay(1, events)
        # forced_next_career is consumed into PendingCareerChoice(options=['Prisoner'])
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert [c.name for c in pending.options] == ['Prisoner']


# ── event 6: backstab fellow rogue ───────────────────────────────────────────


class TestRogueEvent6:
    def _setup_to_event(self) -> list:
        return _through_term_event(6)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {RogueEvent6Backstab, RogueEvent6Refuse}

    def test_backstab_adds_enemy(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=RogueEvent6Backstab.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_backstab_schedules_advancement_dm(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=RogueEvent6Backstab.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 2

    def test_refuse_adds_contact(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=RogueEvent6Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        contacts = [c for c in projection.summary.connections if isinstance(c, Contact)]
        assert len(contacts) >= 1

    def test_refuse_no_enemy(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=RogueEvent6Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 0

    def test_both_choices_queue_advancement(self):
        for choice_cls in (RogueEvent6Backstab, RogueEvent6Refuse):
            base = self._setup_to_event()
            events = [
                *base,
                Event(
                    fulfills=(base[-1].id, 0),
                    handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default),
                ),
            ]
            projection = replay(1, events)
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs), choice_cls


# ── event 9: feud with rival organisation ────────────────────────────────────


class TestRogueEvent9:
    def _setup_to_event(self) -> list:
        return _through_term_event(9)

    def test_creates_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingRogueEvent9SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [Stealth(), GunCombat()]

    def test_success_schedules_extra_benefit_roll(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_failure_adds_injury_problem(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() for p in projection.summary.problems)

    def test_success_creates_advancement_pending(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
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


def _pirate_after_event(event_roll: int) -> CharacterDriver:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5. Pirate: survival DEX 6+, advancement INT 6+ (INT DM+1)."""
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('7869A5')
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    d.career('Rogue', 'Pirate', roll=12)
    d.survive(9)
    d.term_event(event_roll)
    return d


def _pirate_after_event_11() -> CharacterDriver:
    return _pirate_after_event(11)


class TestRogueEvent6History:
    """The history says which way the Traveller chose, and who they gained by it."""

    _STORY = 'Term 1 event (Rogue): You have the opportunity to backstab a fellow rogue for personal gain.'

    def test_refusing_is_told_with_the_contact_gained(self):
        d = _pirate_after_event(6)
        d.career_choice(RogueEvent6Refuse)
        d.name_connection('Mara Voss')
        assert d.projection.creation_history[-1].startswith(f'{self._STORY} You refuse. Contact: Mara Voss.')

    def test_backstabbing_is_told_with_the_enemy_made(self):
        d = _pirate_after_event(6)
        d.career_choice(RogueEvent6Backstab)
        d.name_connection('Mara Voss')
        assert d.projection.creation_history[-1].startswith(
            f'{self._STORY} You backstab them. Gained DM+2 to the next advancement roll. Enemy: Mara Voss.'
        )


class TestRogueEvent11:
    """A crime lord considers you his protégé.

    "Either gain Tactics (military) 1 or DM+4 to your next advancement roll thanks to their aid."
    """

    _STORY = 'Term 1 event (Rogue): A crime lord considers you his protégé'

    def test_offers_tactics_military_or_the_advancement_dm(self):
        d = _pirate_after_event_11()
        assert d.skill_choice_labels() == ['Tactics (Military)', 'DM+4 to next advancement roll']

    def test_history_before_the_choice_tells_only_the_story(self):
        d = _pirate_after_event_11()
        assert d.projection.creation_history[-1].startswith(f'{self._STORY}. In progress: ')

    def test_history_when_tactics_is_chosen(self):
        d = _pirate_after_event_11()
        d.choose_skill(Tactics(military=Level(value=1)))
        assert d.projection.creation_history[-1] == (
            f'{self._STORY} and teaches you tactics. Tactics (Military) increased from 0 to 1.'
        )

    def test_history_when_the_advancement_dm_is_chosen(self):
        d = _pirate_after_event_11()
        d.choose_advancement_dm()
        assert d.projection.creation_history[-1] == f'{self._STORY} and tries to get you promoted.'

    def test_tactics_military_1_can_be_gained(self):
        d = _pirate_after_event_11()
        d.choose_skill(Tactics(military=Level(value=1)))
        tactics = next(skill for skill in d.projection.summary.skills if isinstance(skill, Tactics))
        assert tactics.military.value == 1

    def test_dm_plus_4_makes_a_low_advancement_roll_succeed(self):
        d = _pirate_after_event_11()
        d.choose_advancement_dm()
        d.advancement(3)  # INT 6+: 3 + 1 + 4 = 8
        assert d.projection.summary.rank == 1

    def test_without_the_dm_the_same_roll_fails(self):
        d = _pirate_after_event_11()
        d.choose_skill(Tactics(military=Level(value=1)))
        d.advancement(3)  # INT 6+: 3 + 1 = 4
        assert not d.projection.summary.rank
