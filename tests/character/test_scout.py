"""Tests for Scout career events, mishaps, and assignment table corrections."""

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.career import SCOUT
from ceres.character.domain.career.career_data import AdvancementDmOption
from ceres.character.domain.career.career_events import (
    AdvancementDmChoiceHandler,
    AdvancementHandler,
    CareerEntryHandler,
    CharacteristicChoiceHandler,
    ConnectionsRollHandler,
    MishapHandler,
    PendingAdvancement,
    PendingChoices,
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
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.scout import (
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
    Astrogation,
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
from ceres.character.input_specs import Select
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD, CharacterDriver

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

    def _setup_to_ambush(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(7)
            .term_event(3)
        )

    def test_creates_ambush_pending_with_skill_options(self):
        driver = self._setup_to_ambush()

        assert driver.available_skill_roll_options() == [Pilot(), Persuade()]

    def test_gain_enemy_applied_immediately_before_roll(self):
        projection = self._setup_to_ambush().projection

        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_success_pilot_grants_electronics(self):
        # Pilot 8+, roll 9 → success
        projection = self._setup_to_ambush().skill_roll(Pilot(), 9).projection

        assert projection.summary.skill_level(Electronics, -1) >= 1

    def test_success_persuade_grants_electronics(self):
        # Persuade 10+, roll 11 → success
        projection = self._setup_to_ambush().skill_roll(Persuade(), 11).projection

        assert projection.summary.skill_level(Electronics, -1) >= 1

    def test_failure_pilot_adds_problem(self):
        # Pilot 8+, roll 6 → failure
        projection = self._setup_to_ambush().skill_roll(Pilot(), 6).projection

        assert any('re-enlist' in p.lower() or 'destroyed' in p.lower() for p in projection.summary.problems)

    def test_failure_persuade_adds_problem(self):
        # Persuade 10+, roll 8 → failure
        projection = self._setup_to_ambush().skill_roll(Persuade(), 8).projection

        assert any('re-enlist' in p.lower() or 'destroyed' in p.lower() for p in projection.summary.problems)

    def test_failure_forces_scout_career_to_end_after_advancement(self):
        driver = self._setup_to_ambush().skill_roll(Pilot(), 6).advancement(3)
        projection = driver.projection

        assert projection.summary.current_career is None
        driver.muster_out('cash', 1)

    def test_skill_roll_creates_advancement_pending(self):
        self._setup_to_ambush().skill_roll(Pilot(), 9).advancement(3)


class TestScoutEvent6:
    def _setup(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=6)),
        ]

    def test_text_matches_core(self):
        assert SCOUT.events[6].text == (
            'You spend several years jumping from world to world in your scout ship. Gain one of Astrogation 1, '
            'Electronics 1, Navigation 1, Pilot (small craft) 1 or Mechanic 1.'
        )

    def test_offers_level_1_choices_with_only_pilot_small_craft(self):
        projection = replay(1, self._setup())
        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice))

        assert pending.instruction == 'Choose one skill at level 1'
        assert pending.level == 1
        [spec] = pending.input_specs(projection)
        assert isinstance(spec, Select)
        assert [label for label, _ in spec.options] == [
            'Astrogation',
            'Electronics (Comms)',
            'Electronics (Computers)',
            'Electronics (Remote Ops)',
            'Electronics (Sensors)',
            'Navigation',
            'Pilot (Small Craft)',
            'Mechanic',
        ]

    def test_does_not_offer_choices_already_at_level_1(self):
        projection = replay(1, self._setup())
        projection.grant_skill(Astrogation(level=Level(value=1)))
        projection.grant_skill(Electronics(sensors=Level(value=1)))
        projection.grant_skill(Pilot(small_craft=Level(value=1)))
        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice))

        [spec] = pending.input_specs(projection)
        assert isinstance(spec, Select)
        labels = [label for label, _ in spec.options]
        assert 'Astrogation' not in labels
        assert 'Electronics (Sensors)' not in labels
        assert not any(label.startswith('Pilot') for label in labels)


class TestScoutEvent8:
    """Roll Electronics 8+ or Deception 8+. Success: Ally + DM+2. Failure: mishap, stay in career."""

    def _setup(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(7)
            .term_event(8)
        )

    def test_creates_pending_with_electronics_and_deception_options(self):
        assert self._setup().available_skill_roll_options() == [Electronics(), Deception()]

    def test_success_gains_ally(self):
        projection = self._setup().skill_roll(Electronics(), 9).projection

        assert any(isinstance(c, Ally) for c in projection.summary.connections)

    def test_success_creates_advancement_pending(self):
        self._setup().skill_roll(Electronics(), 9).advancement(3)

    def test_failure_creates_mishap_pending(self):
        self._setup().skill_roll(Electronics(), 5).mishap(5, stay_in_career=True)

    def test_failure_mishap_stay_keeps_career_active(self):
        projection = self._setup().skill_roll(Electronics(), 5).mishap(5, stay_in_career=True).projection

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
        self._setup().skill_roll(Electronics(), 5).mishap(5, stay_in_career=True).advancement(3)


class TestScoutEvent9:
    """Roll Medic 8+ or Engineer 8+. Success: Contact + DM+2. Failure: Enemy."""

    def _setup(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(7)
            .term_event(9)
        )

    def test_creates_pending_with_medic_and_engineer_options(self):
        assert self._setup().available_skill_roll_options() == [Medic(), Engineer()]

    def test_success_gains_contact(self):
        projection = self._setup().skill_roll(Medic(), 9).projection

        assert any(isinstance(c, Contact) for c in projection.summary.connections)

    def test_failure_gains_enemy(self):
        projection = self._setup().skill_roll(Medic(), 5).projection

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_success_creates_advancement_pending(self):
        self._setup().skill_roll(Medic(), 9).advancement(3)

    def test_failure_creates_advancement_pending(self):
        self._setup().skill_roll(Medic(), 5).advancement(3)


class TestScoutEvent10:
    """Roll Survival 8+ or Pilot 8+. Success: alien Contact + any skill +1. Failure: mishap, stay."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
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
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
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
        assert 'conflict' in rival.origin.lower() or 'rival' in rival.origin.lower()

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
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
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
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
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
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
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
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
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
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
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
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment(assignment), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=9)),
            Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),
        ]

    def test_service_skills_roll_1_offers_only_small_craft_or_spacecraft_pilot(self):
        events = [
            *self._setup_in_term_2('Courier'),
            Event(fulfills=(8, 0), handler=SkillTableHandler(table='service_skills', roll=1)),
        ]

        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice))
        assert pending.options == [
            Pilot(small_craft=Level(value=1)),
            Pilot(spacecraft=Level(value=1)),
        ]

    def test_courier_roll_2_offers_flyer(self):
        # Courier roll 2 is Flyer (specialised) — player must choose a specialisation
        events = [
            *self._setup_in_term_2('Courier'),
            Event(fulfills=(8, 0), handler=SkillTableHandler(table='assignment1', roll=2)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert Flyer() in pending.options

    def test_surveyor_roll_2_gives_persuade(self):
        events = [
            *self._setup_in_term_2('Surveyor'),
            Event(fulfills=(8, 0), handler=SkillTableHandler(table='assignment2', roll=2)),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Persuade) is not None

    def test_surveyor_roll_4_gives_navigation(self):
        events = [
            *self._setup_in_term_2('Surveyor'),
            Event(fulfills=(8, 0), handler=SkillTableHandler(table='assignment2', roll=4)),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Navigation) is not None

    def test_explorer_roll_2_offers_pilot(self):
        # Explorer roll 2 is Pilot (specialised) — player must choose a specialisation
        events = [
            *self._setup_in_term_2('Explorer'),
            Event(fulfills=(8, 0), handler=SkillTableHandler(table='assignment3', roll=2)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert Pilot() in pending.options

    def test_explorer_roll_4_creates_science_choice_pending(self):
        events = [
            *self._setup_in_term_2('Explorer'),
            Event(fulfills=(8, 0), handler=SkillTableHandler(table='assignment3', roll=4)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES

    def test_advanced_edu_roll_5_creates_science_choice_pending(self):
        # EDU=10 ≥ 8 → can access advanced_education table
        events = [
            *self._setup_in_term_2('Courier'),
            Event(fulfills=(8, 0), handler=SkillTableHandler(table='advanced_education', roll=5)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES


# ── Homeworld trigger (RIC-006) ───────────────────────────────────────────────

_WORLD_NO_SCOUT_BASE = TravellerMapWorld.model_validate(
    {**MOCK_WORLD.model_dump(), 'Bases': 'N', 'LegacyBaseCode': 'N'}
)
_WORLD_WITH_SCOUT_BASE = TravellerMapWorld.model_validate(
    {**MOCK_WORLD.model_dump(), 'Bases': 'S', 'LegacyBaseCode': 'S'}
)
_WORLD_WITH_WAY_STATION = TravellerMapWorld.model_validate(
    {**MOCK_WORLD.model_dump(), 'Bases': 'W', 'LegacyBaseCode': 'W'}
)


def _scout_entry_events(homeworld: TravellerMapWorld) -> list:
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=homeworld, player='NPC', name='X')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
        ),
    ]


class TestScoutHomeworldTrigger:
    def test_non_scout_base_homeworld_produces_blocking_required_pending(self):
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeRequired

        projection = replay(1, _scout_entry_events(_WORLD_NO_SCOUT_BASE))

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired)), None)
        assert pending is not None
        assert pending.blocking is True
        assert pending.source_career == 'Scout'
        assert pending.target_constraints == 'world_with_scout_base'

    def test_scout_base_homeworld_produces_non_blocking_offered_pending(self):
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeOffered

        projection = replay(1, _scout_entry_events(_WORLD_WITH_SCOUT_BASE))

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeOffered)), None)
        assert pending is not None
        assert pending.blocking is False
        assert pending.source_career == 'Scout'

    def test_way_station_homeworld_produces_non_blocking_offered_pending(self):
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeOffered

        projection = replay(1, _scout_entry_events(_WORLD_WITH_WAY_STATION))

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeOffered)), None)
        assert pending is not None
        assert pending.blocking is False

    def test_homeworld_not_mutated_until_fulfilled(self):

        projection = replay(1, _scout_entry_events(_WORLD_NO_SCOUT_BASE))

        assert projection.summary.homeworld == _WORLD_NO_SCOUT_BASE

    def test_fulfilling_required_pending_updates_homeworld_not_birthworld(self):
        from ceres.character.domain.homeworld.homeworld_events import (
            HomeworldChangedHandler,
            PendingHomeworldChangeRequired,
        )

        events = _scout_entry_events(_WORLD_NO_SCOUT_BASE)
        projection = replay(1, events)
        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))

        events = [
            *events,
            Event(
                id=5, fulfills=pending.pending_id, handler=HomeworldChangedHandler(new_homeworld=_WORLD_WITH_SCOUT_BASE)
            ),
        ]
        projection = replay(1, events)

        assert projection.summary.homeworld == _WORLD_WITH_SCOUT_BASE
        assert projection.summary.birthworld == _WORLD_NO_SCOUT_BASE

    def test_reenlistment_triggers_homeworld_check_again(self):
        """After changing to a Scout base world and reenlisting, a new homeworld check fires."""
        from ceres.character.domain.homeworld.homeworld_events import (
            HomeworldChangedHandler,
            PendingHomeworldChangeOffered,
            PendingHomeworldChangeRequired,
        )

        events = _scout_entry_events(_WORLD_NO_SCOUT_BASE)
        projection = replay(1, events)
        hw_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))

        # Resolve term 1: change homeworld then proceed through term
        events = [
            *events,
            Event(
                id=5,
                fulfills=hw_pending.pending_id,
                handler=HomeworldChangedHandler(new_homeworld=_WORLD_WITH_SCOUT_BASE),
            ),
            Event(id=6, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=7, fulfills=(6, 0), handler=TermEventHandler(roll=5)),
            Event(id=8, fulfills=(7, 0), handler=AdvancementHandler(roll=3)),
            Event(fulfills=(8, 0), handler=ReenlistHandler(reenlist=True)),
        ]
        projection = replay(1, events)

        # Homeworld is now a Scout base world → second term produces offered (non-blocking)
        hw_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeOffered)]
        assert len(hw_pendings) == 1
        assert hw_pendings[0].source_career == 'Scout'


# ── mishap 1: severely injured ────────────────────────────────────────────────


class TestScoutMishap1:
    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Scout', 'Courier', roll=7)
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}
