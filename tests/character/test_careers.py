"""Tests for career flow: complete Scout Courier term, scripted with deterministic rolls."""

import pytest

from ceres.character.events import (
    AdvancementEvent,
    BackgroundSkillsEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    ConnectionsRollEvent,
    MishapEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import ReplayError, replay


def _full_setup(character_id: int = 1) -> list:
    """Return events that get a character through setup: started → ucp → background skills."""
    # STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 → 4 background skills
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=['Admin', 'Athletics', 'Carouse', 'Drive']),
    ]


class TestCareerEntry:
    def test_career_event_creates_survive_pending(self):
        events = [*_full_setup(), CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier')]

        projection = replay(1, events)

        assert any(p.kind == 'survive' for p in projection.pending_inputs)

    def test_career_event_sets_current_career_in_summary(self):
        events = [*_full_setup(), CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier')]

        projection = replay(1, events)

        assert projection.summary.current_career == 'Scout'
        assert projection.summary.current_assignment == 'Courier'

    def test_career_event_grants_initial_training_service_skills(self):
        events = [*_full_setup(), CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier')]

        projection = replay(1, events)

        # First term: all service skills at level 0
        assert projection.summary.skills.get('Pilot') == 0
        assert projection.summary.skills.get('Survival') == 0
        assert projection.summary.skills.get('Mechanic') == 0
        assert projection.summary.skills.get('Astrogation') == 0
        assert projection.summary.skills.get('Vacc Suit') == 0
        assert projection.summary.skills.get('Gun Combat') == 0

    def test_career_event_rejects_unknown_career(self):
        with pytest.raises(ReplayError):
            replay(1, [*_full_setup(), CareerEvent(id=4, fulfills='3.0', career='Pirate', assignment='Freebooter')])

    def test_career_event_rejects_unknown_assignment(self):
        with pytest.raises(ReplayError):
            replay(1, [*_full_setup(), CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Admiral')])

    def test_career_pending_id_derived_from_background_skills_event_id(self):
        events = [*_full_setup(), CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier')]

        projection = replay(1, events)

        survive_pending = next(p for p in projection.pending_inputs if p.kind == 'survive')
        # The survive pending is created by the career event (id=4), so it's 4.0
        assert survive_pending.id == '4.0'

    def test_survive_pending_instruction_mentions_target(self):
        events = [*_full_setup(), CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier')]

        projection = replay(1, events)

        survive_pending = next(p for p in projection.pending_inputs if p.kind == 'survive')
        # Courier survival: END 5+
        assert 'END' in survive_pending.instruction
        assert '5' in survive_pending.instruction

    def test_scholar_career_event_grants_scholar_service_skills(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher'),
        ]

        projection = replay(1, events)

        # Scholar service skills
        assert 'Electronics' in projection.summary.skills
        assert 'Medic' in projection.summary.skills
        assert 'Investigate' in projection.summary.skills


class TestSurvive:
    def _setup_with_career(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
        ]

    def test_survive_success_creates_term_event_pending(self):
        # END=6 (DM+0), need 5+, roll 7 → success
        events = [*self._setup_with_career(), SurviveEvent(id=5, fulfills='4.0', roll=7)]

        projection = replay(1, events)

        assert any(p.kind == 'term_event' for p in projection.pending_inputs)

    def test_survive_failure_creates_mishap_pending(self):
        # END=6 (DM+0), need 5+, roll 3 → failure
        events = [*self._setup_with_career(), SurviveEvent(id=5, fulfills='4.0', roll=3)]

        projection = replay(1, events)

        assert any(p.kind == 'mishap' for p in projection.pending_inputs)

    def test_natural_2_always_fails(self):
        # Natural 2 always fails regardless of characteristic DMs
        events = [*self._setup_with_career(), SurviveEvent(id=5, fulfills='4.0', roll=2)]

        projection = replay(1, events)

        assert any(p.kind == 'mishap' for p in projection.pending_inputs)

    def test_survive_success_at_exact_target(self):
        # END=6 (DM+0), need 5+, roll 5 → success
        events = [*self._setup_with_career(), SurviveEvent(id=5, fulfills='4.0', roll=5)]

        projection = replay(1, events)

        assert any(p.kind == 'term_event' for p in projection.pending_inputs)


class TestMishap:
    def _setup_through_failed_survive(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
        ]

    def test_mishap_resolves_mishap_pending(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=5)]

        projection = replay(1, events)

        assert not any(p.kind == 'mishap' for p in projection.pending_inputs)

    def test_mishap_ends_career(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=5)]

        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_mishap_records_mishap_text_in_problems(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=5)]

        projection = replay(1, events)

        assert len(projection.summary.problems) > 0


class TestScoutAmbush:
    """Scout event 3: ambush — choose Pilot 8+ or Persuade 10+, conditional outcomes."""

    def _setup_to_ambush(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=3),
        ]

    def test_creates_ambush_pending_with_skill_options(self):
        projection = replay(1, self._setup_to_ambush())

        pending = next((p for p in projection.pending_inputs if p.kind == 'scout_event_3'), None)
        assert pending is not None
        assert set(pending.options) == {'Pilot', 'Persuade'}

    def test_gain_enemy_applied_immediately_before_roll(self):
        projection = replay(1, self._setup_to_ambush())

        enemies = [c for c in projection.summary.connections if c.kind == 'enemy']
        assert len(enemies) == 1

    def test_success_pilot_grants_electronics(self):
        # Pilot 8+, roll 9 → success
        events = [
            *self._setup_to_ambush(),
            SkillRollEvent(id=7, fulfills='6.0', context='scout_event_3', skill='Pilot', modified_roll=9),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Electronics', -1) >= 1

    def test_success_persuade_grants_electronics(self):
        # Persuade 10+, roll 11 → success
        events = [
            *self._setup_to_ambush(),
            SkillRollEvent(id=7, fulfills='6.0', context='scout_event_3', skill='Persuade', modified_roll=11),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Electronics', -1) >= 1

    def test_failure_pilot_adds_problem(self):
        # Pilot 8+, roll 6 → failure
        events = [
            *self._setup_to_ambush(),
            SkillRollEvent(id=7, fulfills='6.0', context='scout_event_3', skill='Pilot', modified_roll=6),
        ]
        projection = replay(1, events)

        assert any('re-enlist' in p.lower() or 'destroyed' in p.lower() for p in projection.summary.problems)

    def test_failure_persuade_adds_problem(self):
        # Persuade 10+, roll 8 → failure
        events = [
            *self._setup_to_ambush(),
            SkillRollEvent(id=7, fulfills='6.0', context='scout_event_3', skill='Persuade', modified_roll=8),
        ]
        projection = replay(1, events)

        assert any('re-enlist' in p.lower() or 'destroyed' in p.lower() for p in projection.summary.problems)

    def test_skill_roll_creates_advancement_pending(self):
        events = [
            *self._setup_to_ambush(),
            SkillRollEvent(id=7, fulfills='6.0', context='scout_event_3', skill='Pilot', modified_roll=9),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestScoutEvent8:
    """Roll Electronics 8+ or Deception 8+. Success: Ally + DM+2. Failure: mishap, stay in career."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=8),
        ]

    def test_creates_pending_with_electronics_and_deception_options(self):
        projection = replay(1, self._setup())

        pending = next(p for p in projection.pending_inputs if p.kind == 'scout_event_8')
        assert set(pending.options) == {'Electronics', 'Deception'}

    def test_success_gains_ally(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_8', skill='Electronics', modified_roll=9)
        projection = replay(1, [*self._setup(), roll])

        assert any(c.kind == 'ally' for c in projection.summary.connections)

    def test_success_creates_advancement_pending(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_8', skill='Electronics', modified_roll=9)
        projection = replay(1, [*self._setup(), roll])

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_failure_creates_mishap_pending(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_8', skill='Electronics', modified_roll=5)
        events = [*self._setup(), roll]
        projection = replay(1, events)

        assert any(p.kind == 'mishap' for p in projection.pending_inputs)

    def test_failure_mishap_stay_keeps_career_active(self):
        events = [
            *self._setup(),
            SkillRollEvent(id=7, fulfills='6.0', context='scout_event_8', skill='Electronics', modified_roll=5),
            MishapEvent(id=8, fulfills='7.0', roll=5, stay_in_career=True),
        ]

        projection = replay(1, events)

        assert projection.summary.current_career == 'Scout'
        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestScoutEvent9:
    """Roll Medic 8+ or Engineer 8+. Success: Contact + DM+2. Failure: Enemy."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=9),
        ]

    def test_creates_pending_with_medic_and_engineer_options(self):
        projection = replay(1, self._setup())

        pending = next(p for p in projection.pending_inputs if p.kind == 'scout_event_9')
        assert set(pending.options) == {'Medic', 'Engineer'}

    def test_success_gains_contact(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_9', skill='Medic', modified_roll=9)
        projection = replay(1, [*self._setup(), roll])

        assert any(c.kind == 'contact' for c in projection.summary.connections)

    def test_failure_gains_enemy(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_9', skill='Medic', modified_roll=5)
        projection = replay(1, [*self._setup(), roll])

        assert any(c.kind == 'enemy' for c in projection.summary.connections)

    def test_success_creates_advancement_pending(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_9', skill='Medic', modified_roll=9)
        projection = replay(1, [*self._setup(), roll])

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_9', skill='Medic', modified_roll=5)
        projection = replay(1, [*self._setup(), roll])

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestScoutEvent10:
    """Roll Survival 8+ or Pilot 8+. Success: alien Contact + any skill +1. Failure: mishap, stay."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=10),
        ]

    def test_creates_pending_with_survival_and_pilot_options(self):
        projection = replay(1, self._setup())

        pending = next(p for p in projection.pending_inputs if p.kind == 'scout_event_10')
        assert set(pending.options) == {'Survival', 'Pilot'}

    def test_success_gains_contact(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_10', skill='Pilot', modified_roll=9)
        projection = replay(1, [*self._setup(), roll])

        assert any(c.kind == 'contact' for c in projection.summary.connections)

    def test_success_creates_skill_choice_pending(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_10', skill='Pilot', modified_roll=9)
        projection = replay(1, [*self._setup(), roll])

        assert any(p.kind == 'skill_choice' for p in projection.pending_inputs)

    def test_success_skill_choice_grants_skill_and_creates_advancement(self):
        events = [
            *self._setup(),
            SkillRollEvent(id=7, fulfills='6.0', context='scout_event_10', skill='Pilot', modified_roll=9),
            SkillChoiceEvent(id=8, fulfills='7.0', skill='Navigation'),
        ]

        projection = replay(1, events)

        assert projection.summary.skills.get('Navigation', -1) >= 1
        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_failure_creates_mishap_pending(self):
        roll = SkillRollEvent(id=7, fulfills='6.0', context='scout_event_10', skill='Pilot', modified_roll=5)
        projection = replay(1, [*self._setup(), roll])

        assert any(p.kind == 'mishap' for p in projection.pending_inputs)

    def test_failure_mishap_stay_keeps_career_active(self):
        events = [
            *self._setup(),
            SkillRollEvent(id=7, fulfills='6.0', context='scout_event_10', skill='Pilot', modified_roll=5),
            MishapEvent(id=8, fulfills='7.0', roll=5, stay_in_career=True),
        ]

        projection = replay(1, events)

        assert projection.summary.current_career == 'Scout'
        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestConnections:
    """Mishap and event effects that produce connections on the character sheet."""

    def _setup_through_failed_survive(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
        ]

    def test_mishap_4_adds_rival_immediately(self):
        # Mishap 4: gain Diplomat 1 + Rival
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=4)]

        projection = replay(1, events)

        rivals = [c for c in projection.summary.connections if c.kind == 'rival']
        assert len(rivals) == 1

    def test_mishap_4_rival_source_is_mishap_text(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=4)]

        projection = replay(1, events)

        rival = next(c for c in projection.summary.connections if c.kind == 'rival')
        assert 'conflict' in rival.source.lower() or 'rival' in rival.source.lower()

    def test_mishap_3_creates_pending_for_contacts_roll(self):
        # Mishap 3: Gain 1D Contacts and D3 Enemies
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=3)]

        projection = replay(1, events)

        pending_kinds = [p.kind for p in projection.pending_inputs]
        assert pending_kinds.count('connections_roll') == 2

    def test_mishap_3_connections_roll_contact_adds_connections(self):
        events = [
            *self._setup_through_failed_survive(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            ConnectionsRollEvent(id=7, fulfills='6.0', connection_type='contact', count=3),
            ConnectionsRollEvent(id=8, fulfills='6.1', connection_type='enemy', count=1),
        ]

        projection = replay(1, events)

        contacts = [c for c in projection.summary.connections if c.kind == 'contact']
        enemies = [c for c in projection.summary.connections if c.kind == 'enemy']
        assert len(contacts) == 3
        assert len(enemies) == 1

    def test_event_3_scout_adds_enemy_unconditionally(self):
        # Scout event 3: ambush, always gain an Enemy regardless of skill roll outcome
        setup = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=3),
        ]

        projection = replay(1, setup)

        enemies = [c for c in projection.summary.connections if c.kind == 'enemy']
        assert len(enemies) == 1


class TestMishapWithChoice:
    """Mishap #2 for Scout: 'Reduce your INT or SOC by 1' — player chooses."""

    def _setup_through_failed_survive(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
        ]

    def test_mishap_2_creates_characteristic_choice_pending(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=2)]

        projection = replay(1, events)

        choice_pending = next((p for p in projection.pending_inputs if p.kind == 'characteristic_choice'), None)
        assert choice_pending is not None
        assert set(choice_pending.options) == {'INT', 'SOC'}

    def test_mishap_2_characteristic_choice_int_decreases_int(self):
        events = [
            *self._setup_through_failed_survive(),
            MishapEvent(id=6, fulfills='5.0', roll=2),
            CharacteristicChoiceEvent(id=7, fulfills='6.0', characteristic='INT'),
        ]

        projection = replay(1, events)

        # INT was 9 (from UCP '7869A5': STR=7, DEX=8, END=6, INT=9, EDU=10, SOC=5)
        assert projection.summary.characteristics['INT'] == 8

    def test_mishap_2_characteristic_choice_soc_decreases_soc(self):
        events = [
            *self._setup_through_failed_survive(),
            MishapEvent(id=6, fulfills='5.0', roll=2),
            CharacteristicChoiceEvent(id=7, fulfills='6.0', characteristic='SOC'),
        ]

        projection = replay(1, events)

        # SOC was 5
        assert projection.summary.characteristics['SOC'] == 4
        assert projection.summary.characteristics['INT'] == 9  # unchanged


class TestTermEvent:
    def _setup_through_survive(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),  # success
        ]

    def test_term_event_resolves_pending_creates_advancement_pending(self):
        events = [*self._setup_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=7)]

        projection = replay(1, events)

        assert not any(p.kind == 'term_event' for p in projection.pending_inputs)
        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_event_7_life_event_creates_advancement_and_no_immediate_pending(self):
        # Life event (7) — deferred for now, just advances to advancement
        events = [*self._setup_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=7)]

        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_event_4_skill_choice_creates_skill_choice_pending(self):
        # Event 4 for Scout: gain one of Animals, Survival, Recon, Science
        events = [*self._setup_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=4)]

        projection = replay(1, events)

        # Should have both a skill_choice pending and the advancement pending
        assert any(p.kind == 'skill_choice' for p in projection.pending_inputs)


class TestAdvancement:
    def _setup_through_term_event(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),  # life event, simple
        ]

    def test_advancement_success_increases_rank(self):
        # EDU=10 (DM+1), need 9+, roll 9 → success (9+1=10 >= 9)
        events = [*self._setup_through_term_event(), AdvancementEvent(id=7, fulfills='6.0', roll=9)]

        projection = replay(1, events)

        assert projection.summary.rank == 1  # Scout rank 1

    def test_advancement_success_grants_rank_bonus_skill(self):
        # Rank 1 Scout gets Vacc Suit 1
        events = [*self._setup_through_term_event(), AdvancementEvent(id=7, fulfills='6.0', roll=9)]

        projection = replay(1, events)

        assert projection.summary.skills.get('Vacc Suit') == 1

    def test_advancement_failure_keeps_rank(self):
        events = [*self._setup_through_term_event(), AdvancementEvent(id=7, fulfills='6.0', roll=5)]

        projection = replay(1, events)

        assert projection.summary.rank == 0

    def test_advancement_creates_reenlist_pending(self):
        events = [*self._setup_through_term_event(), AdvancementEvent(id=7, fulfills='6.0', roll=9)]

        projection = replay(1, events)

        assert any(p.kind == 'reenlist' for p in projection.pending_inputs)

    def test_advancement_instruction_mentions_target(self):
        setup = self._setup_through_term_event()
        projection = replay(1, setup)

        adv_pending = next(p for p in projection.pending_inputs if p.kind == 'advancement')
        # Courier advancement: EDU 9+
        assert 'EDU' in adv_pending.instruction
        assert '9' in adv_pending.instruction


class TestReenlist:
    def _setup_through_advancement(self, advancement_roll: int = 9) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),
            AdvancementEvent(id=7, fulfills='6.0', roll=advancement_roll),
        ]

    def test_reenlist_true_increments_term_count(self):
        events = [*self._setup_through_advancement(), ReenlistEvent(id=8, fulfills='7.0', reenlist=True)]

        projection = replay(1, events)

        assert projection.summary.term_count == 2

    def test_reenlist_true_creates_skill_table_pending(self):
        events = [*self._setup_through_advancement(), ReenlistEvent(id=8, fulfills='7.0', reenlist=True)]

        projection = replay(1, events)

        assert any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_reenlist_false_ends_career(self):
        events = [*self._setup_through_advancement(), ReenlistEvent(id=8, fulfills='7.0', reenlist=False)]

        projection = replay(1, events)

        assert projection.summary.current_career is None
        assert not any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_reenlist_pending_options_include_true_false(self):
        setup = self._setup_through_advancement()
        projection = replay(1, setup)

        reenlist_pending = next(p for p in projection.pending_inputs if p.kind == 'reenlist')
        assert reenlist_pending.options == ['true', 'false']


class TestSkillTable:
    def _setup_in_term_2(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),
            AdvancementEvent(id=7, fulfills='6.0', roll=9),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
        ]

    def test_skill_table_courier_roll_grants_new_skill_at_level_0(self):
        # Courier table roll 1: Electronics — not in Scout service skills → first gain at level 0
        events = [*self._setup_in_term_2(), SkillTableEvent(id=9, fulfills='8.0', table='courier', roll=1)]

        projection = replay(1, events)

        assert projection.summary.skills.get('Electronics') == 0

    def test_skill_table_personal_development_characteristic_increase(self):
        # Personal development roll 1: STR +1 (STR was 7, should be 8)
        events = [
            *self._setup_in_term_2(),
            SkillTableEvent(id=9, fulfills='8.0', table='personal_development', roll=1),
        ]

        projection = replay(1, events)

        assert projection.summary.characteristics.get('STR') == 8

    def test_skill_table_creates_survive_pending(self):
        events = [*self._setup_in_term_2(), SkillTableEvent(id=9, fulfills='8.0', table='courier', roll=1)]

        projection = replay(1, events)

        assert any(p.kind == 'survive' for p in projection.pending_inputs)

    def test_skill_table_rejects_advanced_education_when_edu_too_low(self):
        # EDU=10 meets Scout advanced education min EDU 8
        # Make a character with EDU=6 to fail the advanced education requirement
        low_edu_events = [
            CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
            UcpEvent(id=2, fulfills='1.0', ucp='786600'),  # EDU=6
            BackgroundSkillsEvent(id=3, fulfills='2.0', skills=['Admin', 'Athletics', 'Drive']),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),
            AdvancementEvent(id=7, fulfills='6.0', roll=9),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
        ]
        with pytest.raises(ReplayError):
            replay(
                1,
                [*low_edu_events, SkillTableEvent(id=9, fulfills='8.0', table='advanced_education', roll=1)],
            )


class TestTermEventRollMishap:
    """Event 2 Disaster! — creates mishap pending; character stays in career."""

    def _setup_to_disaster(self, career: str = 'Scout', assignment: str = 'Courier') -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career=career, assignment=assignment),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=2),
        ]

    def test_creates_mishap_pending(self):
        projection = replay(1, self._setup_to_disaster())

        assert any(p.kind == 'mishap' for p in projection.pending_inputs)

    def test_mishap_stay_keeps_career(self):
        events = [
            *self._setup_to_disaster(),
            MishapEvent(id=7, fulfills='6.0', roll=5, stay_in_career=True),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career == 'Scout'

    def test_mishap_stay_creates_advancement_pending(self):
        events = [
            *self._setup_to_disaster(),
            MishapEvent(id=7, fulfills='6.0', roll=5, stay_in_career=True),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_works_for_scholar_too(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=2),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'mishap' for p in projection.pending_inputs)


class TestTermEventAutoAdvance:
    """Event 12 — automatic promotion, no advancement roll needed."""

    def test_scout_event_12_promotes_rank(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=12),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 1

    def test_scout_event_12_applies_rank_1_vacc_suit_bonus(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=12),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Vacc Suit') == 1

    def test_creates_reenlist_pending_not_advancement(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=12),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'reenlist' for p in projection.pending_inputs)
        assert not any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_scholar_event_12_promotes_with_space_science(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=12),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 1
        assert projection.summary.skills.get('Space Science') == 1


class TestScholarTerm:
    """Basic Scholar Field Researcher term: survival, events, advancement, reenlist."""

    def _setup_with_scholar(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher'),
        ]

    def test_survive_pending_is_end_6(self):
        projection = replay(1, self._setup_with_scholar())

        survive_pending = next(p for p in projection.pending_inputs if p.kind == 'survive')
        assert 'END' in survive_pending.instruction and '6' in survive_pending.instruction

    def test_advancement_pending_is_int_6(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),
        ]
        projection = replay(1, events)

        adv_pending = next(p for p in projection.pending_inputs if p.kind == 'advancement')
        assert 'INT' in adv_pending.instruction and '6' in adv_pending.instruction

    def test_rank_1_bonus_is_space_science(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),
            AdvancementEvent(id=7, fulfills='6.0', roll=7),  # INT=9 DM+1 → 8 >= 6
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Space Science') == 1

    def test_event_4_skill_choice_options(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=4),
        ]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if p.kind == 'skill_choice')
        assert set(pending.options) == {'Medic', 'Space Science', 'Engineer', 'Electronics', 'Investigate'}

    def test_event_9_stores_advancement_dm_in_scheduled_effects(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=9),
        ]
        projection = replay(1, events)

        adv_dm = next((se for se in projection.scheduled_effects if se.trigger == 'advancement'), None)
        assert adv_dm is not None
        assert adv_dm.effect.get('amount') == 2

    def test_event_9_still_creates_advancement_pending(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=9),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_event_10_skill_choice_options(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=10),
        ]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if p.kind == 'skill_choice')
        assert set(pending.options) == {'Admin', 'Advocate', 'Persuade', 'Diplomat'}

    def test_event_11_gains_ally_and_creates_advancement_pending(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=11),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'ally' for c in projection.summary.connections)
        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_mishap_4_grants_skill_choice_before_ejection(self):
        # Scholar mishap 4: skill_choice [Survival, Athletics], character still leaves career
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
            MishapEvent(id=6, fulfills='5.0', roll=4),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if p.kind == 'skill_choice'), None)
        assert pending is not None
        assert set(pending.options) == {'Survival', 'Athletics'}

    def test_mishap_4_skill_choice_grants_skill_and_no_advancement_pending(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=3),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='Survival'),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Survival', -1) >= 1
        assert projection.summary.current_career is None
        assert not any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_scholar_mishap_6_stays_in_career_and_gains_rival(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=3),
            MishapEvent(id=6, fulfills='5.0', roll=6),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career == 'Scholar'
        assert any(p.kind == 'advancement' for p in projection.pending_inputs)
        assert any(c.kind == 'rival' for c in projection.summary.connections)

    def test_scholar_mishap_6_stays_even_without_explicit_flag(self):
        # MishapEntry.stay_in_career overrides player's default stay_in_career=False
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=3),
            MishapEvent(id=6, fulfills='5.0', roll=6, stay_in_career=False),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career == 'Scholar'


class TestSkillTableIncrement:
    """Skill table rolls increment: gain at 0 if new, +1 if already possessed."""

    def _setup_in_term_2(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),
            AdvancementEvent(id=7, fulfills='6.0', roll=9),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
        ]

    def test_new_skill_gains_level_0(self):
        # Courier table roll 2: Persuade — not in Scout service skills → first gain at 0
        events = [*self._setup_in_term_2(), SkillTableEvent(id=9, fulfills='8.0', table='courier', roll=2)]
        projection = replay(1, events)

        assert projection.summary.skills.get('Persuade') == 0

    def test_existing_skill_at_0_increments_to_1(self):
        # Courier table roll 3: Pilot — Scout has Pilot 0 from initial training → 1
        events = [*self._setup_in_term_2(), SkillTableEvent(id=9, fulfills='8.0', table='courier', roll=3)]
        projection = replay(1, events)

        assert projection.summary.skills.get('Pilot') == 1

    def test_existing_skill_at_1_increments_to_2(self):
        # Scout rank 1 bonus: Vacc Suit 1. Roll service_skills 5 (Vacc Suit) in term 2 → 2
        events = [*self._setup_in_term_2(), SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=5)]
        projection = replay(1, events)

        assert projection.summary.skills.get('Vacc Suit') == 2


class TestSkillTableChoice:
    """Skill table entries with multiple options create a pending choice."""

    def _setup_scholar_term_2(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Scientist'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),
            AdvancementEvent(id=7, fulfills='6.0', roll=7),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
        ]

    def test_choice_entry_creates_skill_table_choice_pending(self):
        # Scholar service_skills roll 1: Drive/Flyer choice
        events = [*self._setup_scholar_term_2(), SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1)]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if p.kind == 'skill_table_choice'), None)
        assert pending is not None
        assert set(pending.options) == {'Drive', 'Flyer'}

    def test_choice_increments_chosen_skill(self):
        # Scholar has Drive 0 from initial training → choose Drive → Drive 1
        events = [
            *self._setup_scholar_term_2(),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SkillChoiceEvent(id=10, fulfills='9.0', skill='Drive'),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Drive') == 1

    def test_choice_creates_survive_pending_not_advancement(self):
        events = [
            *self._setup_scholar_term_2(),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SkillChoiceEvent(id=10, fulfills='9.0', skill='Flyer'),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'survive' for p in projection.pending_inputs)
        assert not any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestAdvancementDmFromScheduledEffects:
    """Scheduled advancement DMs are consumed and applied during the advancement check."""

    def test_breakthrough_dm_helps_marginal_roll_succeed(self):
        # Scholar Scientist: INT 9 (DM+1) needs INT 8+
        # Without event DM: roll 6 + DM+1 = 7 < 8 → fail
        # With Scholar event 9 DM+2: roll 6 + DM+1 + DM+2 = 9 >= 8 → success
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Scientist'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=9),  # breakthrough → DM+2
            AdvancementEvent(id=7, fulfills='6.0', roll=6),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 1

    def test_without_dm_same_roll_fails(self):
        # Same roll (6) without the breakthrough DM → 7 < 8 → fail
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Scientist'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),  # life event, no DM
            AdvancementEvent(id=7, fulfills='6.0', roll=6),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 0

    def test_breakthrough_dm_is_consumed_after_advancement(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Scientist'),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=9),
            AdvancementEvent(id=7, fulfills='6.0', roll=6),
        ]
        projection = replay(1, events)

        adv_dms = [se for se in projection.scheduled_effects if se.trigger == 'advancement']
        assert len(adv_dms) == 0
