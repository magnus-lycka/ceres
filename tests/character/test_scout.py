"""Tests for Scout career events, mishaps, and assignment table corrections."""

from ceres.character.domain.career.career_data import AdvancementDmOption
from ceres.character.domain.career.career_events import (
    AdvancementDmChoiceHandler,
    AdvancementHandler,
    CareerEntryHandler,
    CharacteristicChoiceHandler,
    ConnectionsRollHandler,
    MishapHandler,
    PendingAdvancement,
    PendingConnectionsRoll,
    PendingMishap,
    PendingSkillChoice,
    PendingSkillTableChoice,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillRollHandler,
    SkillTableHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.scout import (
    PendingScoutEvent3SkillRoll,
    PendingScoutEvent8SkillRoll,
    PendingScoutEvent9SkillRoll,
    PendingScoutEvent10SkillRoll,
    PendingScoutEvent11,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.connection import (
    Ally,
    Contact,
    Enemy,
    Rival,
)
from ceres.character.domain.health.health_events import (
    PendingCharacteristicChoice,
    PendingInjuryTable,
)
from ceres.character.domain.skills import (
    Admin,
    Athletics,
    Carouse,
    Deception,
    Diplomat,
    Drive,
    Electronics,
    Engineer,
    Flyer,
    Level,
    Medic,
    Navigation,
    Persuade,
    Pilot,
    Sciences,
    Survival,
    _skill_classes,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD

_SCIENCE_CLASSES = set(_skill_classes(Sciences))


def _full_setup(character_id: int = 1) -> list:
    """Return events that get a character through setup: started → ucp → background skills."""
    # STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 → 4 background skills
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
    ]


class TestScoutAmbush:
    """Scout event 3: ambush — choose Pilot 8+ or Persuade 10+, conditional outcomes."""

    def _setup_to_ambush(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=3)),
        ]

    def test_creates_ambush_pending_with_skill_options(self):
        projection = replay(1, self._setup_to_ambush())

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingScoutEvent3SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [Pilot(), Persuade()]

    def test_gain_enemy_applied_immediately_before_roll(self):
        projection = replay(1, self._setup_to_ambush())

        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_success_pilot_grants_electronics(self):
        # Pilot 8+, roll 9 → success
        events = [
            *self._setup_to_ambush(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Pilot(), modified_roll=9)),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Electronics, -1) >= 1

    def test_success_persuade_grants_electronics(self):
        # Persuade 10+, roll 11 → success
        events = [
            *self._setup_to_ambush(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Persuade(), modified_roll=11)),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Electronics, -1) >= 1

    def test_failure_pilot_adds_problem(self):
        # Pilot 8+, roll 6 → failure
        events = [
            *self._setup_to_ambush(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Pilot(), modified_roll=6)),
        ]
        projection = replay(1, events)

        assert any('re-enlist' in p.lower() or 'destroyed' in p.lower() for p in projection.summary.problems)

    def test_failure_persuade_adds_problem(self):
        # Persuade 10+, roll 8 → failure
        events = [
            *self._setup_to_ambush(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Persuade(), modified_roll=8)),
        ]
        projection = replay(1, events)

        assert any('re-enlist' in p.lower() or 'destroyed' in p.lower() for p in projection.summary.problems)

    def test_skill_roll_creates_advancement_pending(self):
        events = [
            *self._setup_to_ambush(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Pilot(), modified_roll=9)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestScoutEvent8:
    """Roll Electronics 8+ or Deception 8+. Success: Ally + DM+2. Failure: mishap, stay in career."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=8)),
        ]

    def test_creates_pending_with_electronics_and_deception_options(self):
        projection = replay(1, self._setup())

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingScoutEvent8SkillRoll))
        assert pending.options == [Electronics(), Deception()]

    def test_success_gains_ally(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Electronics(), modified_roll=9))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(c, Ally) for c in projection.summary.connections)

    def test_success_creates_advancement_pending(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Electronics(), modified_roll=9))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_failure_creates_mishap_pending(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Electronics(), modified_roll=5))
        events = [*self._setup(), roll]
        projection = replay(1, events)

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_failure_mishap_stay_keeps_career_active(self):
        events = [
            *self._setup(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Electronics(), modified_roll=5)),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=5, stay_in_career=True)),
        ]

        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestScoutEvent9:
    """Roll Medic 8+ or Engineer 8+. Success: Contact + DM+2. Failure: Enemy."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=9)),
        ]

    def test_creates_pending_with_medic_and_engineer_options(self):
        projection = replay(1, self._setup())

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingScoutEvent9SkillRoll))
        assert pending.options == [Medic(), Engineer()]

    def test_success_gains_contact(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Medic(), modified_roll=9))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(c, Contact) for c in projection.summary.connections)

    def test_failure_gains_enemy(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Medic(), modified_roll=5))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_success_creates_advancement_pending(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Medic(), modified_roll=9))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Medic(), modified_roll=5))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestScoutEvent10:
    """Roll Survival 8+ or Pilot 8+. Success: alien Contact + any skill +1. Failure: mishap, stay."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=10)),
        ]

    def test_creates_pending_with_survival_and_pilot_options(self):
        projection = replay(1, self._setup())

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingScoutEvent10SkillRoll))
        assert pending.options == [Survival(), Pilot()]

    def test_success_gains_contact(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Pilot(), modified_roll=9))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(c, Contact) for c in projection.summary.connections)

    def test_success_creates_skill_choice_pending(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Pilot(), modified_roll=9))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_success_skill_choice_grants_skill_and_creates_advancement(self):
        events = [
            *self._setup(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Pilot(), modified_roll=9)),
            Event(id=8, fulfills=(7, 0), handler=SkillChoiceHandler(skill=Navigation(level=Level(value=1)))),
        ]

        projection = replay(1, events)

        assert projection.summary.skill_level(Navigation, -1) >= 1
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_failure_creates_mishap_pending(self):
        roll = Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Pilot(), modified_roll=5))
        projection = replay(1, [*self._setup(), roll])

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_failure_mishap_stay_keeps_career_active(self):
        events = [
            *self._setup(),
            Event(id=7, fulfills=(6, 0), handler=SkillRollHandler(skill=Pilot(), modified_roll=5)),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=5, stay_in_career=True)),
        ]

        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestConnections:
    """Mishap and event effects that produce connections on the character sheet."""

    def _setup_through_failed_survive(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),  # fail
        ]

    def test_mishap_4_adds_rival_immediately(self):
        # Mishap 4: gain Diplomat 1 + Rival
        events = [*self._setup_through_failed_survive(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4))]

        projection = replay(1, events)

        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_mishap_4_rival_source_is_mishap_text(self):
        events = [*self._setup_through_failed_survive(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4))]

        projection = replay(1, events)

        rival = next(c for c in projection.summary.connections if isinstance(c, Rival))
        assert 'conflict' in rival.source.lower() or 'rival' in rival.source.lower()

    def test_mishap_3_creates_pending_for_contacts_roll(self):
        # Mishap 3: Gain 1D Contacts and D3 Enemies
        events = [*self._setup_through_failed_survive(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3))]

        projection = replay(1, events)

        assert sum(isinstance(p, PendingConnectionsRoll) for p in projection.pending_inputs) == 2

    def test_mishap_3_connections_roll_contact_adds_connections(self):
        events = [
            *self._setup_through_failed_survive(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=3)),
            Event(
                id=7, fulfills=(6, 0), handler=ConnectionsRollHandler(connection_type=ConnectionKind.CONTACT, count=3)
            ),
            Event(id=8, fulfills=(6, 1), handler=ConnectionsRollHandler(connection_type=ConnectionKind.ENEMY, count=1)),
        ]

        projection = replay(1, events)

        contacts = [c for c in projection.summary.connections if isinstance(c, Contact)]
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(contacts) == 3
        assert len(enemies) == 1

    def test_event_3_scout_adds_enemy_unconditionally(self):
        # Scout event 3: ambush, always gain an Enemy regardless of skill roll outcome
        setup = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=3)),
        ]

        projection = replay(1, setup)

        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1


class TestMishapWithChoice:
    """Mishap #2 for Scout: 'Reduce your INT or SOC by 1' — player chooses."""

    def _setup_through_failed_survive(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),  # fail
        ]

    def test_mishap_2_creates_characteristic_choice_pending(self):
        events = [*self._setup_through_failed_survive(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=2))]

        projection = replay(1, events)

        choice_pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice)), None
        )
        assert choice_pending is not None
        assert set(choice_pending.options) == {'INT', 'SOC'}

    def test_mishap_2_characteristic_choice_int_decreases_int(self):
        events = [
            *self._setup_through_failed_survive(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=2)),
            Event(id=7, fulfills=(6, 0), handler=CharacteristicChoiceHandler(characteristic=Chars.INT)),
        ]

        projection = replay(1, events)

        # INT was 9 (from UCP '7869A5': STR=7, DEX=8, END=6, INT=9, EDU=10, SOC=5)
        assert projection.summary.characteristics[Chars.INT] == 8

    def test_mishap_2_characteristic_choice_soc_decreases_soc(self):
        events = [
            *self._setup_through_failed_survive(),
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=2)),
            Event(id=7, fulfills=(6, 0), handler=CharacteristicChoiceHandler(characteristic=Chars.SOC)),
        ]

        projection = replay(1, events)

        # SOC was 5
        assert projection.summary.characteristics[Chars.SOC] == 4
        assert projection.summary.characteristics[Chars.INT] == 9  # unchanged


class TestScoutEvent11:
    """Scout event 11: gain Diplomat 1 OR DM+4 to next advancement roll."""

    def _setup_to_event_11(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=11)),
        ]

    def test_creates_scout_event_11_pending_with_two_options(self):
        projection = replay(1, self._setup_to_event_11())

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingScoutEvent11))
        assert pending.options == [Diplomat(), AdvancementDmOption()]

    def test_choose_diplomat_grants_diplomat_1(self):
        diplomat_choice = Event(id=7, fulfills=(6, 0), handler=SkillChoiceHandler(skill=Diplomat(level=Level(value=1))))
        events = [*self._setup_to_event_11(), diplomat_choice]
        projection = replay(1, events)

        assert projection.summary.skill_level(Diplomat, -1) >= 1

    def test_choose_advancement_dm_adds_pending_advancement_dm(self):
        events = [*self._setup_to_event_11(), Event(id=7, fulfills=(6, 0), handler=AdvancementDmChoiceHandler())]
        projection = replay(1, events)

        assert projection.pending_advancement_dm == 4

    def test_diplomat_choice_creates_advancement_pending(self):
        diplomat_choice = Event(id=7, fulfills=(6, 0), handler=SkillChoiceHandler(skill=Diplomat(level=Level(value=1))))
        events = [*self._setup_to_event_11(), diplomat_choice]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_advancement_dm_choice_creates_advancement_pending(self):
        events = [*self._setup_to_event_11(), Event(id=7, fulfills=(6, 0), handler=AdvancementDmChoiceHandler())]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestNormalInjury:
    """Scout mishap 6: Injured — roll on Injury table (Core p.47)."""

    def _setup_through_failed_survive(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),  # fail
        ]

    def test_mishap_6_creates_injury_table_pending(self):
        events = [*self._setup_through_failed_survive(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=6))]
        projection = replay(1, events)

        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_mishap_6_still_ends_career(self):
        events = [*self._setup_through_failed_survive(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=6))]
        projection = replay(1, events)

        assert projection.summary.current_career is None


class TestScoutMishap6InjuryTable:
    """Scout mishap 6: Injured — roll on Injury table (Core p.47), not a fixed normal injury."""

    def _setup_to_mishap(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment='Courier', qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),  # fail survive
        ]

    def test_mishap_6_creates_injury_table_pending(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=6))]
        projection = replay(1, events)

        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_mishap_6_does_not_create_characteristic_choice_directly(self):
        events = [*self._setup_to_mishap(), Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=6))]
        projection = replay(1, events)

        assert not any(isinstance(p, PendingCharacteristicChoice) for p in projection.pending_inputs)


class TestScoutAssignmentTableCorrections:
    """Scout assignment skill table entries corrected vs Core p.48."""

    def _setup_in_term_2(self, assignment: str) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career='Scout', assignment=assignment, qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=9)),
            Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),
        ]

    def test_courier_roll_2_offers_flyer(self):
        # Courier roll 2 is Flyer (specialised) — player must choose a specialisation
        events = [
            *self._setup_in_term_2('Courier'),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='assignment1', roll=2)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert Flyer() in pending.options

    def test_surveyor_roll_2_gives_persuade(self):
        events = [
            *self._setup_in_term_2('Surveyor'),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='assignment2', roll=2)),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Persuade) is not None

    def test_surveyor_roll_4_gives_navigation(self):
        events = [
            *self._setup_in_term_2('Surveyor'),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='assignment2', roll=4)),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Navigation) is not None

    def test_explorer_roll_2_offers_pilot(self):
        # Explorer roll 2 is Pilot (specialised) — player must choose a specialisation
        events = [
            *self._setup_in_term_2('Explorer'),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='assignment3', roll=2)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert Pilot() in pending.options

    def test_explorer_roll_4_creates_science_choice_pending(self):
        events = [
            *self._setup_in_term_2('Explorer'),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='assignment3', roll=4)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES

    def test_advanced_edu_roll_5_creates_science_choice_pending(self):
        # EDU=10 ≥ 8 → can access advanced_education table
        events = [
            *self._setup_in_term_2('Courier'),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='advanced_education', roll=5)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES
