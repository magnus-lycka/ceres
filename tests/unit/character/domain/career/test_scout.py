"""Tests for Scout career events, mishaps, and assignment table corrections."""

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.career import SCOUT
from ceres.character.domain.career.career_data import AdvancementDmOption
from ceres.character.domain.career.career_events import (
    AdvancementHandler,
    CareerEntryHandler,
    MishapHandler,
    PendingChoices,
    PendingSkillChoice,
    PendingSkillTableChoice,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillTableHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.character_start import BackgroundSkillsHandler, UcpHandler
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
    AnySkill,
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
from tests.unit.character.helpers import (
    MOCK_WORLD,
    CharacterDriver,
    _creation_events,
    pending_id as _pending,
    scripted_event as _event,
)

_SCIENCE_CLASSES = set(_skill_classes(Sciences))


def _full_setup(character_id: int = 1) -> list:
    """Return events that get a character through setup: started → ucp → background skills."""
    # STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 → 4 background skills
    c = _creation_events(VILANI, MOCK_WORLD, 'NPC', 'Boss')
    ucp = _event(fulfills=_pending(c[-1], 0), handler=UcpHandler(ucp='7869A5'))
    background = _event(
        fulfills=_pending(ucp, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    return [*c, ucp, background]


def _enter_scout(assignment: str = 'Courier', qualification_roll: int = 7) -> list:
    base = _full_setup()
    entry = _event(
        fulfills=_pending(base[-1], 0),
        handler=CareerEntryHandler(
            career=SCOUT, assignment=SCOUT.assignment(assignment), qualification_roll=qualification_roll
        ),
    )
    return [*base, entry]


def _through_survive(assignment: str = 'Courier', survive_roll: int = 7) -> list:
    base = _enter_scout(assignment)
    return [*base, _event(fulfills=_pending(base[-1], 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Courier') -> list:
    base = _through_survive(assignment)
    return [*base, _event(fulfills=_pending(base[-1], 0), handler=TermEventHandler(roll=event_roll))]


def _failed_survive(assignment: str = 'Courier') -> list:
    base = _enter_scout(assignment)
    return [*base, _event(fulfills=_pending(base[-1], 0), handler=SurviveHandler(roll=3))]


def _mishap_event(source: Event, roll: int, stay_in_career: bool = False) -> Event:
    return _event(fulfills=_pending(source, 0), handler=MishapHandler(roll=roll, stay_in_career=stay_in_career))


def _skill_choice_event(source: Event, skill: AnySkill) -> Event:
    return _event(fulfills=_pending(source, 0), handler=SkillChoiceHandler(skill=skill))


def _skill_table_event(source: Event, table: str, roll: int) -> Event:
    return _event(fulfills=_pending(source, 0), handler=SkillTableHandler(table=table, roll=roll))


def _advancement_event(source: Event, roll: int) -> Event:
    return _event(fulfills=_pending(source, 0), handler=AdvancementHandler(roll=roll))


def _reenlist_event(source: Event, reenlist: bool) -> Event:
    return _event(fulfills=_pending(source, 0), handler=ReenlistHandler(reenlist=reenlist))


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
        return _through_term_event(6)

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

    def _setup(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(7)
            .term_event(10)
        )

    def test_creates_pending_with_survival_and_pilot_options(self):
        assert self._setup().available_skill_roll_options() == [Survival(), Pilot()]

    def test_success_gains_contact(self):
        projection = self._setup().skill_roll(Pilot(), 9).projection

        assert any(isinstance(c, Contact) for c in projection.summary.connections)

    def test_success_skill_choice_grants_skill_and_creates_advancement(self):
        driver = self._setup().skill_roll(Pilot(), 9).choose_skill(Navigation(level=Level(value=1)))
        projection = driver.projection

        assert projection.summary.skill_level(Navigation, -1) >= 1
        driver.advancement(3)

    def test_failure_creates_mishap_pending(self):
        self._setup().skill_roll(Pilot(), 5).mishap(5, stay_in_career=True)

    def test_failure_mishap_stay_keeps_career_active(self):
        driver = self._setup().skill_roll(Pilot(), 5).mishap(5, stay_in_career=True)
        projection = driver.projection

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
        driver.advancement(3)


class TestConnections:
    """Mishap and event effects that produce connections on the character sheet."""

    def _failed_survive_driver(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(2)
        )

    def test_mishap_4_adds_rival_immediately(self):
        d = self._failed_survive_driver().mishap(4)
        assert len([c for c in d.projection.summary.connections if isinstance(c, Rival)]) == 1

    def test_mishap_4_rival_source_is_mishap_text(self):
        d = self._failed_survive_driver().mishap(4)
        rival = next(c for c in d.projection.summary.connections if isinstance(c, Rival))
        assert 'conflict' in rival.origin.lower() or 'rival' in rival.origin.lower()

    def test_mishap_3_creates_two_connection_roll_pendings(self):
        d = self._failed_survive_driver().mishap(3)
        assert d.pending_connections_roll_count() == 2

    def test_mishap_3_connections_roll_adds_contacts_and_enemies(self):
        d = self._failed_survive_driver().mishap(3)
        d.connections_roll(3)
        d.connections_roll(1)
        contacts = [c for c in d.projection.summary.connections if isinstance(c, Contact)]
        enemies = [c for c in d.projection.summary.connections if isinstance(c, Enemy)]
        assert len(contacts) == 3
        assert len(enemies) == 1

    def test_mishap_3_enemy_roll_has_d3_options(self):
        d = self._failed_survive_driver().mishap(3)
        assert d.connections_roll_options(ConnectionKind.ENEMY) == [1, 2, 3]

    def test_event_3_scout_adds_enemy_unconditionally(self):
        d = (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(7)
            .term_event(3)
        )
        assert len([c for c in d.projection.summary.connections if isinstance(c, Enemy)]) == 1


class TestMishapWithChoice:
    """Mishap #2 for Scout: 'Reduce your INT or SOC by 1' — player chooses."""

    def _failed_survive_driver(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(2)
        )

    def test_mishap_2_offers_int_and_soc_choice(self):
        d = self._failed_survive_driver().mishap(2)
        assert set(d.characteristic_choice_options()) == {Chars.INT, Chars.SOC}

    def test_mishap_2_characteristic_choice_int_decreases_int(self):
        # INT was 9 (from UCP '7869A5': STR=7, DEX=8, END=6, INT=9, EDU=10, SOC=5)
        d = self._failed_survive_driver().mishap(2).choose_characteristic(Chars.INT)
        assert d.projection.summary.characteristics[Chars.INT] == 8

    def test_mishap_2_characteristic_choice_soc_decreases_soc(self):
        # SOC was 5
        d = self._failed_survive_driver().mishap(2).choose_characteristic(Chars.SOC)
        assert d.projection.summary.characteristics[Chars.SOC] == 4
        assert d.projection.summary.characteristics[Chars.INT] == 9  # unchanged


class TestScoutEvent11:
    """Scout event 11: gain Diplomat 1 OR DM+4 to next advancement roll."""

    def _setup_to_event_11(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(7)
            .term_event(11)
        )

    def test_creates_scout_event_11_pending_with_two_options(self):
        assert self._setup_to_event_11().available_career_skill_options() == [Diplomat(), AdvancementDmOption()]

    def test_choose_diplomat_grants_diplomat_1(self):
        projection = self._setup_to_event_11().choose_career_skill(Diplomat(level=Level(value=1))).projection

        assert projection.summary.skill_level(Diplomat, -1) >= 1

    def test_choose_advancement_dm_adds_pending_advancement_dm(self):
        projection = self._setup_to_event_11().choose_advancement_dm().projection

        assert projection.pending_advancement_dm == 4

    def test_diplomat_choice_creates_advancement_pending(self):
        self._setup_to_event_11().choose_career_skill(Diplomat(level=Level(value=1))).advancement(3)

    def test_advancement_dm_choice_creates_advancement_pending(self):
        self._setup_to_event_11().choose_advancement_dm().advancement(3)


class TestScoutMishap6:
    """Scout mishap 6: Injured — roll on Injury table (Core p.47), not a fixed normal injury."""

    def _failed_survive_driver(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Boss')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Scout', 'Courier', roll=7)
            .survive(2)
        )

    def test_mishap_6_ends_career(self):
        d = self._failed_survive_driver().mishap(6)
        assert d.projection.summary.current_career is None

    def test_mishap_6_creates_injury_table_pending(self):
        base = _failed_survive()
        events = [*base, _mishap_event(base[-1], 6)]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_mishap_6_does_not_create_characteristic_choice_directly(self):
        base = _failed_survive()
        events = [*base, _mishap_event(base[-1], 6)]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingCharacteristicChoice) for p in projection.pending_inputs)


class TestScoutAssignmentTableCorrections:
    """Scout assignment skill table entries corrected vs Core p.48."""

    def _setup_in_term_2(self, assignment: str) -> list:
        base = _through_term_event(5, assignment)
        advancement = _advancement_event(base[-1], 9)
        reenlist = _reenlist_event(advancement, True)
        return [
            *base,
            advancement,
            reenlist,
        ]

    def test_service_skills_roll_1_offers_only_small_craft_or_spacecraft_pilot(self):
        base = self._setup_in_term_2('Courier')
        events = [
            *base,
            _skill_table_event(base[-1], 'service_skills', 1),
        ]

        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice))
        assert pending.options == [
            Pilot(small_craft=Level(value=1)),
            Pilot(spacecraft=Level(value=1)),
        ]

    def test_courier_roll_2_offers_flyer(self):
        # Courier roll 2 is Flyer (specialised) — player must choose a specialisation
        base = self._setup_in_term_2('Courier')
        events = [
            *base,
            _skill_table_event(base[-1], 'assignment1', 2),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert Flyer() in pending.options

    def test_surveyor_roll_2_gives_persuade(self):
        base = self._setup_in_term_2('Surveyor')
        events = [
            *base,
            _skill_table_event(base[-1], 'assignment2', 2),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Persuade) is not None

    def test_surveyor_roll_4_gives_navigation(self):
        base = self._setup_in_term_2('Surveyor')
        events = [
            *base,
            _skill_table_event(base[-1], 'assignment2', 4),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Navigation) is not None

    def test_explorer_roll_2_offers_pilot(self):
        # Explorer roll 2 is Pilot (specialised) — player must choose a specialisation
        base = self._setup_in_term_2('Explorer')
        events = [
            *base,
            _skill_table_event(base[-1], 'assignment3', 2),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert Pilot() in pending.options

    def test_explorer_roll_4_creates_science_choice_pending(self):
        base = self._setup_in_term_2('Explorer')
        events = [
            *base,
            _skill_table_event(base[-1], 'assignment3', 4),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES

    def test_advanced_edu_roll_5_creates_science_choice_pending(self):
        # EDU=10 ≥ 8 → can access advanced_education table
        base = self._setup_in_term_2('Courier')
        events = [
            *base,
            _skill_table_event(base[-1], 'advanced_education', 5),
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
    c = _creation_events(VILANI, homeworld, 'NPC', 'X')
    ucp = _event(fulfills=_pending(c[-1], 0), handler=UcpHandler(ucp='7869A5'))
    background = _event(
        fulfills=_pending(ucp, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    entry = _event(
        fulfills=_pending(background, 0),
        handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
    )
    return [*c, ucp, background, entry]


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
            _event(
                fulfills=pending.pending_id,
                handler=HomeworldChangedHandler(new_homeworld=_WORLD_WITH_SCOUT_BASE),
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
        homeworld_changed = _event(
            fulfills=hw_pending.pending_id,
            handler=HomeworldChangedHandler(new_homeworld=_WORLD_WITH_SCOUT_BASE),
        )
        survive = _event(fulfills=_pending(events[-1], 0), handler=SurviveHandler(roll=7))
        term_event = _event(fulfills=_pending(survive, 0), handler=TermEventHandler(roll=5))
        advancement = _event(fulfills=_pending(term_event, 0), handler=AdvancementHandler(roll=3))
        events = [
            *events,
            homeworld_changed,
            survive,
            term_event,
            advancement,
            _event(fulfills=_pending(advancement, 0), handler=ReenlistHandler(reenlist=True)),
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
