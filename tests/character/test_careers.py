"""Tests for career flow: complete Scout Courier term, scripted with deterministic rolls."""

import pytest

from ceres.character.events import (
    AdvancementEvent,
    AgingRollEvent,
    BackgroundSkillsEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    ConnectionsRollEvent,
    InjuryTableEvent,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
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


class TestQualification:
    """Qualification roll on career entry."""

    def test_success_starts_career(self):
        # Scout: INT 5+, character has INT=9 (DM+1), roll 5 → 5+1=6 >= 5
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career == 'Scout'
        assert any(p.kind == 'survive' for p in projection.pending_inputs)

    def test_failure_clears_career_and_creates_retry_pending(self):
        # Scout: INT 5+, INT=9 (DM+1), roll 3 → 3+1=4 < 5
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None
        assert any(p.kind == 'career' for p in projection.pending_inputs)

    def test_failure_adds_problem_with_career_name(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=3),
        ]
        projection = replay(1, events)

        assert any('Scout' in p for p in projection.summary.problems)

    def test_scholar_failure(self):
        # Scholar: EDU 6+, EDU=10 (DM+1), roll 4 → 4+1=5 < 6
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=4),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_scholar_success(self):
        # EDU=10 (DM+1), roll 5 → 5+1=6 >= 6
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career == 'Scholar'

    def test_retry_after_failure_can_succeed(self):
        # Fail Scout, then succeed Scholar
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=3),
            CareerEvent(id=5, fulfills='4.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career == 'Scholar'


class TestCareerEntry:
    def test_career_event_creates_survive_pending(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        assert any(p.kind == 'survive' for p in projection.pending_inputs)

    def test_career_event_sets_current_career_in_summary(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        assert projection.summary.current_career == 'Scout'
        assert projection.summary.current_assignment == 'Courier'

    def test_career_event_grants_initial_training_service_skills(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]

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
            replay(
                1,
                [
                    *_full_setup(),
                    CareerEvent(id=4, fulfills='3.0', career='Pirate', assignment='Freebooter', qualification_roll=7),
                ],
            )

    def test_career_event_rejects_unknown_assignment(self):
        with pytest.raises(ReplayError):
            replay(
                1,
                [
                    *_full_setup(),
                    CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Admiral', qualification_roll=7),
                ],
            )

    def test_career_pending_id_derived_from_background_skills_event_id(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        survive_pending = next(p for p in projection.pending_inputs if p.kind == 'survive')
        # The survive pending is created by the career event (id=4), so it's 4.0
        assert survive_pending.id == '4.0'

    def test_survive_pending_instruction_mentions_target(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        survive_pending = next(p for p in projection.pending_inputs if p.kind == 'survive')
        # Courier survival: END 5+
        assert 'END' in survive_pending.instruction
        assert '5' in survive_pending.instruction

    def test_scholar_career_event_grants_scholar_service_skills(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),  # success
        ]

    def test_term_event_resolves_pending_creates_life_event_pending(self):
        events = [*self._setup_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=7)]

        projection = replay(1, events)

        assert not any(p.kind == 'term_event' for p in projection.pending_inputs)
        assert any(p.kind == 'life_event' for p in projection.pending_inputs)

    def test_event_7_life_event_blocks_advancement_until_resolved(self):
        # Life event (7) creates life_event pending; advancement is not visible until life event resolves
        events = [*self._setup_through_survive(), TermEventEvent(id=6, fulfills='5.0', roll=7)]

        projection = replay(1, events)

        assert any(p.kind == 'life_event' for p in projection.pending_inputs)
        assert not any(p.kind == 'advancement' for p in projection.pending_inputs)

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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
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

    def _setup_to_disaster(
        self, career: str = 'Scout', assignment: str = 'Courier', qualification_roll: int = 7
    ) -> list:
        return [
            *_full_setup(),
            CareerEvent(
                id=4, fulfills='3.0', career=career, assignment=assignment, qualification_roll=qualification_roll
            ),
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
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=12),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 1

    def test_scout_event_12_applies_rank_1_vacc_suit_bonus(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=12),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Vacc Suit') == 1

    def test_creates_reenlist_pending_not_advancement(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=12),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'reenlist' for p in projection.pending_inputs)
        assert not any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_scholar_event_12_promotes_with_space_science(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
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
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
        ]

    def test_survive_pending_is_end_6(self):
        projection = replay(1, self._setup_with_scholar())

        survive_pending = next(p for p in projection.pending_inputs if p.kind == 'survive')
        assert 'END' in survive_pending.instruction and '6' in survive_pending.instruction

    def test_advancement_pending_is_int_6(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
        ]
        projection = replay(1, events)

        adv_pending = next(p for p in projection.pending_inputs if p.kind == 'advancement')
        assert 'INT' in adv_pending.instruction and '6' in adv_pending.instruction

    def test_rank_1_bonus_is_space_science(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
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

    def test_event_11_gains_ally_and_creates_scholar_event_11_pending(self):
        events = [
            *self._setup_with_scholar(),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=11),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'ally' for c in projection.summary.connections)
        assert any(p.kind == 'scholar_event_11' for p in projection.pending_inputs)

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
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
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
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Scientist', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
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
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Scientist', qualification_roll=5),
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
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Scientist', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm (no advancement DM)
            AdvancementEvent(id=7, fulfills='6.0', roll=6),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 0

    def test_breakthrough_dm_is_consumed_after_advancement(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Scientist', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=9),
            AdvancementEvent(id=7, fulfills='6.0', roll=6),
        ]
        projection = replay(1, events)

        adv_dms = [se for se in projection.scheduled_effects if se.trigger == 'advancement']
        assert len(adv_dms) == 0


class TestAgeTracking:
    """Character age starts at 18 and increases by 4 per completed term."""

    def test_reenlist_false_increments_age_by_4(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills='6.0', roll=5),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 22

    def test_reenlist_true_also_increments_age_by_4(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills='6.0', roll=5),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 22

    def test_two_terms_adds_8_years(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills='6.0', roll=5),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=12, fulfills='11.0', roll=5),
            ReenlistEvent(id=13, fulfills='12.0', reenlist=False),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 26

    def test_mishap_that_ejects_increments_age_by_4(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=3),
            MishapEvent(id=6, fulfills='5.0', roll=5),  # Scout mishap 5: no effects, career ends
        ]
        projection = replay(1, events)

        assert projection.summary.age == 22

    def test_age_starts_at_18_before_any_career(self):
        projection = replay(1, _full_setup())

        assert projection.summary.age == 18


class TestScholarEvent6:
    """Scholar event 6: roll EDU 8+ to gain any one skill at level 1."""

    def _setup_to_event_6(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=6),
        ]

    def test_creates_scholar_event_6_pending(self):
        projection = replay(1, self._setup_to_event_6())

        assert any(p.kind == 'scholar_event_6' for p in projection.pending_inputs)

    def test_success_creates_skill_choice_pending(self):
        # EDU=10 (DM+1), need 8+, modified_roll=8 → success
        events = [
            *self._setup_to_event_6(),
            SkillRollEvent(id=7, fulfills='6.0', context='scholar_event_6', skill='EDU', modified_roll=8),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'skill_choice' for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending_not_skill_choice(self):
        # modified_roll=5 < 8 → failure
        events = [
            *self._setup_to_event_6(),
            SkillRollEvent(id=7, fulfills='6.0', context='scholar_event_6', skill='EDU', modified_roll=5),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)
        assert not any(p.kind == 'skill_choice' for p in projection.pending_inputs)

    def test_success_skill_choice_grants_skill_at_level_1(self):
        events = [
            *self._setup_to_event_6(),
            SkillRollEvent(id=7, fulfills='6.0', context='scholar_event_6', skill='EDU', modified_roll=8),
            SkillChoiceEvent(id=8, fulfills='7.0', skill='Navigation'),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Navigation', -1) >= 1

    def test_success_skill_choice_creates_advancement_pending(self):
        events = [
            *self._setup_to_event_6(),
            SkillRollEvent(id=7, fulfills='6.0', context='scholar_event_6', skill='EDU', modified_roll=8),
            SkillChoiceEvent(id=8, fulfills='7.0', skill='Navigation'),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestScoutEvent11:
    """Scout event 11: gain Diplomat 1 OR DM+4 to next advancement roll."""

    def _setup_to_event_11(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=11),
        ]

    def test_creates_scout_event_11_pending_with_two_options(self):
        projection = replay(1, self._setup_to_event_11())

        pending = next(p for p in projection.pending_inputs if p.kind == 'scout_event_11')
        assert set(pending.options) == {'Diplomat', 'advancement_dm_4'}

    def test_choose_diplomat_grants_diplomat_1(self):
        events = [*self._setup_to_event_11(), SkillChoiceEvent(id=7, fulfills='6.0', skill='Diplomat')]
        projection = replay(1, events)

        assert projection.summary.skills.get('Diplomat', -1) >= 1

    def test_choose_advancement_dm_adds_scheduled_effect(self):
        events = [*self._setup_to_event_11(), SkillChoiceEvent(id=7, fulfills='6.0', skill='advancement_dm_4')]
        projection = replay(1, events)

        adv_dm = next((se for se in projection.scheduled_effects if se.trigger == 'advancement'), None)
        assert adv_dm is not None
        assert adv_dm.effect.get('amount') == 4

    def test_diplomat_choice_creates_advancement_pending(self):
        events = [*self._setup_to_event_11(), SkillChoiceEvent(id=7, fulfills='6.0', skill='Diplomat')]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_advancement_dm_choice_creates_advancement_pending(self):
        events = [*self._setup_to_event_11(), SkillChoiceEvent(id=7, fulfills='6.0', skill='advancement_dm_4')]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestNormalInjury:
    """Scout mishap 6: Injured — creates characteristic choice for STR/DEX/END."""

    def _setup_through_failed_survive(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
        ]

    def test_mishap_6_creates_characteristic_choice_pending(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=6)]
        projection = replay(1, events)

        choice_pending = next((p for p in projection.pending_inputs if p.kind == 'characteristic_choice'), None)
        assert choice_pending is not None
        assert set(choice_pending.options) == {'STR', 'DEX', 'END'}

    def test_mishap_6_characteristic_choice_decreases_selected_stat(self):
        events = [
            *self._setup_through_failed_survive(),
            MishapEvent(id=6, fulfills='5.0', roll=6),
            CharacteristicChoiceEvent(id=7, fulfills='6.0', characteristic='STR'),
        ]
        projection = replay(1, events)

        # STR was 7 from UCP '7869A5'
        assert projection.summary.characteristics['STR'] == 6

    def test_mishap_6_still_ends_career(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=6)]
        projection = replay(1, events)

        assert projection.summary.current_career is None


class TestScholarMishap3:
    """Mishap 3: planetary government interference. Player chooses openly or secretly. Career continues."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
        ]

    def test_creates_choice_pending_openly_or_secretly(self):
        events = [*self._setup(), MishapEvent(id=6, fulfills='5.0', roll=3)]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if p.kind == 'scholar_mishap_3'), None)
        assert pending is not None
        assert set(pending.options) == {'openly', 'secretly'}

    def test_stays_in_career_before_choice(self):
        events = [*self._setup(), MishapEvent(id=6, fulfills='5.0', roll=3)]
        projection = replay(1, events)

        assert projection.summary.current_career == 'Scholar'

    def test_openly_grants_space_science_and_enemy(self):
        events = [
            *self._setup(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='openly'),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Space Science', -1) >= 1
        assert any(c.kind == 'enemy' for c in projection.summary.connections)

    def test_secretly_grants_space_science_and_decreases_soc_by_2(self):
        events = [
            *self._setup(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='secretly'),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Space Science', -1) >= 1
        # SOC was 5 from UCP '7869A5'
        assert projection.summary.characteristics['SOC'] == 3
        assert not any(c.kind == 'enemy' for c in projection.summary.connections)

    def test_choice_creates_advancement_pending(self):
        events = [
            *self._setup(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='openly'),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestScholarMishap5:
    """Mishap 5: work sabotaged. Give up (leave) or start again (stay, lose benefit rolls)."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
        ]

    def test_creates_give_up_or_start_again_pending(self):
        events = [*self._setup(), MishapEvent(id=6, fulfills='5.0', roll=5)]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if p.kind == 'scholar_mishap_5'), None)
        assert pending is not None
        assert set(pending.options) == {'give_up', 'start_again'}

    def test_give_up_ends_career(self):
        events = [
            *self._setup(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='give_up'),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_give_up_increments_age_by_4(self):
        events = [
            *self._setup(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='give_up'),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 22

    def test_start_again_stays_in_career(self):
        events = [
            *self._setup(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='start_again'),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career == 'Scholar'

    def test_start_again_creates_advancement_pending(self):
        events = [
            *self._setup(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='start_again'),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestScholarEvent3:
    """Event 3: research against conscience. Accept (2 Sciences, D3 Enemies) or Decline (nothing)."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=3),
        ]

    def test_creates_accept_decline_pending(self):
        projection = replay(1, self._setup())

        pending = next((p for p in projection.pending_inputs if p.kind == 'scholar_event_3'), None)
        assert pending is not None
        assert set(pending.options) == {'accept', 'decline'}

    def test_decline_creates_advancement_pending(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='decline')]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_accept_creates_connections_roll_pending_for_d3_enemies(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='accept')]
        projection = replay(1, events)

        conn = next((p for p in projection.pending_inputs if p.kind == 'connections_roll'), None)
        assert conn is not None
        assert conn.options == ['1', '2', '3']

    def test_accept_creates_two_science_choice_pendings(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='accept')]
        projection = replay(1, events)

        sciences = [p for p in projection.pending_inputs if p.kind == 'scholar_event_3_science']
        assert len(sciences) == 2

    def test_accept_science_choice_options_contain_sciences(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='accept')]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if p.kind == 'scholar_event_3_science')
        assert 'Space Science' in pending.options
        assert 'Life Science' in pending.options

    def test_accept_resolving_science_choices_grants_skills(self):
        events = [
            *self._setup(),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='accept'),
            SkillChoiceEvent(id=8, fulfills='7.1', skill='Space Science'),
            SkillChoiceEvent(id=9, fulfills='7.2', skill='Life Science'),
        ]
        projection = replay(1, events)

        assert projection.summary.skills.get('Space Science', -1) >= 1
        assert projection.summary.skills.get('Life Science', -1) >= 1

    def test_accept_creates_advancement_pending(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='accept')]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestScholarEvent8:
    """Event 8: opportunity to cheat. Refuse (nothing) or Accept (Deception/Admin 8+)."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=8),
        ]

    def test_creates_accept_refuse_pending(self):
        projection = replay(1, self._setup())

        pending = next((p for p in projection.pending_inputs if p.kind == 'scholar_event_8'), None)
        assert pending is not None
        assert set(pending.options) == {'accept', 'refuse'}

    def test_refuse_creates_advancement_pending(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='refuse')]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_accept_creates_skill_roll_pending_with_deception_admin(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='accept')]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if p.kind == 'scholar_event_8_roll'), None)
        assert pending is not None
        assert set(pending.options) == {'Deception', 'Admin'}

    def test_accept_success_gains_enemy(self):
        events = [
            *self._setup(),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='scholar_event_8_roll', skill='Deception', modified_roll=9),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'enemy' for c in projection.summary.connections)

    def test_accept_success_creates_skill_choice_pending(self):
        events = [
            *self._setup(),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='scholar_event_8_roll', skill='Deception', modified_roll=9),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'skill_choice' for p in projection.pending_inputs)

    def test_accept_failure_gains_enemy(self):
        events = [
            *self._setup(),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='scholar_event_8_roll', skill='Deception', modified_roll=5),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'enemy' for c in projection.summary.connections)

    def test_accept_failure_creates_advancement_pending(self):
        events = [
            *self._setup(),
            SkillChoiceEvent(id=7, fulfills='6.0', skill='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='scholar_event_8_roll', skill='Deception', modified_roll=5),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestScholarEvent11:
    """Event 11: brilliant mentor (Ally already handled). Space Science +1 OR DM+4 to advancement."""

    def _setup(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=11),
        ]

    def test_gains_ally_unconditionally(self):
        projection = replay(1, self._setup())

        assert any(c.kind == 'ally' for c in projection.summary.connections)

    def test_creates_scholar_event_11_pending(self):
        projection = replay(1, self._setup())

        pending = next((p for p in projection.pending_inputs if p.kind == 'scholar_event_11'), None)
        assert pending is not None
        assert set(pending.options) == {'Space Science', 'advancement_dm_4'}

    def test_choose_space_science_grants_space_science_1(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='Space Science')]
        projection = replay(1, events)

        assert projection.summary.skills.get('Space Science', -1) >= 1

    def test_choose_advancement_dm_adds_scheduled_effect(self):
        events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill='advancement_dm_4')]
        projection = replay(1, events)

        adv_dm = next((se for se in projection.scheduled_effects if se.trigger == 'advancement'), None)
        assert adv_dm is not None
        assert adv_dm.effect.get('amount') == 4

    def test_both_choices_create_advancement_pending(self):
        for choice in ['Space Science', 'advancement_dm_4']:
            events = [*self._setup(), SkillChoiceEvent(id=7, fulfills='6.0', skill=choice)]
            projection = replay(1, events)
            assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestSevereInjury:
    """Mishap 1 for Scout and Scholar: severely injured — reduce one physical characteristic by 2."""

    def _setup_through_failed_survive(
        self, career: str = 'Scout', assignment: str = 'Courier', qualification_roll: int = 7
    ) -> list:
        return [
            *_full_setup(),
            CareerEvent(
                id=4, fulfills='3.0', career=career, assignment=assignment, qualification_roll=qualification_roll
            ),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
        ]

    def test_scout_mishap_1_creates_characteristic_choice_for_physical_stats(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=1)]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if p.kind == 'characteristic_choice'), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}

    def test_scout_mishap_1_instruction_mentions_reduction_of_2(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills='5.0', roll=1)]
        projection = replay(1, events)

        choice = next(p for p in projection.pending_inputs if p.kind == 'characteristic_choice')
        assert '2' in choice.instruction

    def test_scout_mishap_1_choice_reduces_characteristic_by_2(self):
        events = [
            *self._setup_through_failed_survive(),
            MishapEvent(id=6, fulfills='5.0', roll=1),
            CharacteristicChoiceEvent(id=7, fulfills='6.0', characteristic='STR', amount=2),
        ]
        projection = replay(1, events)

        # STR was 7 from UCP '7869A5'
        assert projection.summary.characteristics['STR'] == 5

    def test_scholar_mishap_1_also_creates_characteristic_choice(self):
        events = [
            *self._setup_through_failed_survive('Scholar', 'Field Researcher', qualification_roll=5),
            MishapEvent(id=6, fulfills='5.0', roll=1),
        ]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if p.kind == 'characteristic_choice'), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}

    def test_normal_injury_still_reduces_by_1(self):
        # Scout mishap 6: normal injury should still only reduce by 1
        events = [
            *self._setup_through_failed_survive(),
            MishapEvent(id=6, fulfills='5.0', roll=6),
            CharacteristicChoiceEvent(id=7, fulfills='6.0', characteristic='STR'),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['STR'] == 6  # 7 - 1


class TestFromTableInjury:
    """Scholar mishap 2: injury roll on the Injury table (1D). All six outcomes."""

    def _setup_to_mishap_2(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail
            MishapEvent(id=6, fulfills='5.0', roll=2),  # Scholar mishap 2: from_table injury + rival
        ]

    def test_creates_injury_table_pending(self):
        projection = replay(1, self._setup_to_mishap_2())

        assert any(p.kind == 'injury_table' for p in projection.pending_inputs)

    def test_gains_rival_immediately(self):
        projection = replay(1, self._setup_to_mishap_2())

        assert any(c.kind == 'rival' for c in projection.summary.connections)

    def test_roll_6_lightly_injured_no_characteristic_change(self):
        events = [
            *self._setup_to_mishap_2(),
            InjuryTableEvent(id=7, fulfills='6.0', roll=6),
        ]
        projection = replay(1, events)

        # All characteristics unchanged from UCP '7869A5'
        assert projection.summary.characteristics['STR'] == 7
        assert projection.summary.characteristics['DEX'] == 8
        assert projection.summary.characteristics['END'] == 6
        assert not any(p.kind == 'characteristic_choice' for p in projection.pending_inputs)

    def test_roll_5_creates_characteristic_choice_reduce_by_1(self):
        events = [*self._setup_to_mishap_2(), InjuryTableEvent(id=7, fulfills='6.0', roll=5)]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if p.kind == 'characteristic_choice'), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}
        assert '1' in choice.instruction

    def test_roll_5_choice_reduces_by_1(self):
        events = [
            *self._setup_to_mishap_2(),
            InjuryTableEvent(id=7, fulfills='6.0', roll=5),
            CharacteristicChoiceEvent(id=8, fulfills='7.0', characteristic='END', amount=1),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['END'] == 5  # 6 - 1

    def test_roll_4_creates_characteristic_choice_reduce_by_2(self):
        events = [*self._setup_to_mishap_2(), InjuryTableEvent(id=7, fulfills='6.0', roll=4)]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if p.kind == 'characteristic_choice'), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}
        assert '2' in choice.instruction

    def test_roll_4_choice_reduces_by_2(self):
        events = [
            *self._setup_to_mishap_2(),
            InjuryTableEvent(id=7, fulfills='6.0', roll=4),
            CharacteristicChoiceEvent(id=8, fulfills='7.0', characteristic='STR', amount=2),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['STR'] == 5  # 7 - 2

    def test_roll_3_options_are_str_and_dex_only(self):
        events = [*self._setup_to_mishap_2(), InjuryTableEvent(id=7, fulfills='6.0', roll=3)]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if p.kind == 'characteristic_choice'), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX'}

    def test_roll_3_choice_reduces_by_2(self):
        events = [
            *self._setup_to_mishap_2(),
            InjuryTableEvent(id=7, fulfills='6.0', roll=3),
            CharacteristicChoiceEvent(id=8, fulfills='7.0', characteristic='DEX', amount=2),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['DEX'] == 6  # 8 - 2

    def test_roll_2_creates_characteristic_choice_for_1d_reduction(self):
        events = [*self._setup_to_mishap_2(), InjuryTableEvent(id=7, fulfills='6.0', roll=2)]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if p.kind == 'characteristic_choice'), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}

    def test_roll_2_choice_reduces_by_player_supplied_amount(self):
        # Player rolled 1D=4 for the reduction
        events = [
            *self._setup_to_mishap_2(),
            InjuryTableEvent(id=7, fulfills='6.0', roll=2),
            CharacteristicChoiceEvent(id=8, fulfills='7.0', characteristic='DEX', amount=4),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['DEX'] == 4  # 8 - 4
        # Other physical stats unchanged
        assert projection.summary.characteristics['STR'] == 7
        assert projection.summary.characteristics['END'] == 6

    def test_roll_1_creates_nearly_killed_pending(self):
        events = [*self._setup_to_mishap_2(), InjuryTableEvent(id=7, fulfills='6.0', roll=1)]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if p.kind == 'nearly_killed'), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}

    def test_roll_1_choice_reduces_chosen_by_player_amount_and_others_by_2(self):
        # Player rolled 1D=3 for the chosen stat (DEX); STR and END auto-reduced by 2
        events = [
            *self._setup_to_mishap_2(),
            InjuryTableEvent(id=7, fulfills='6.0', roll=1),
            CharacteristicChoiceEvent(id=8, fulfills='7.0', characteristic='DEX', amount=3),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['DEX'] == 5  # 8 - 3
        assert projection.summary.characteristics['STR'] == 5  # 7 - 2 (auto)
        assert projection.summary.characteristics['END'] == 4  # 6 - 2 (auto)


class TestLifeEvents:
    """Term event roll 7 triggers the Life Events table (2D roll, 11 outcomes)."""

    def _setup_to_life_event(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),
        ]

    def test_creates_life_event_pending(self):
        projection = replay(1, self._setup_to_life_event())

        assert any(p.kind == 'life_event' for p in projection.pending_inputs)

    def test_roll_7_new_contact_adds_contact(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=7)]
        projection = replay(1, events)

        assert any(c.kind == 'contact' for c in projection.summary.connections)

    def test_roll_7_creates_advancement_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=7)]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_roll_5_improved_relationship_adds_ally(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=5)]
        projection = replay(1, events)

        assert any(c.kind == 'ally' for c in projection.summary.connections)

    def test_roll_6_new_relationship_adds_ally(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=6)]
        projection = replay(1, events)

        assert any(c.kind == 'ally' for c in projection.summary.connections)

    def test_roll_3_birth_or_death_creates_advancement_no_mechanical_effect(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=3)]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)
        # no characteristic or connection changes
        assert not projection.summary.connections

    def test_roll_4_ending_relationship_creates_choice_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=4)]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if p.kind == 'life_event_4'), None)
        assert pending is not None
        assert set(pending.options) == {'rival', 'enemy'}

    def test_roll_4_choose_rival_adds_rival(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills='6.0', roll=4),
            SkillChoiceEvent(id=8, fulfills='7.0', skill='rival'),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'rival' for c in projection.summary.connections)

    def test_roll_4_choose_enemy_adds_enemy(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills='6.0', roll=4),
            SkillChoiceEvent(id=8, fulfills='7.0', skill='enemy'),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'enemy' for c in projection.summary.connections)

    def test_roll_4_choice_resolves_to_advancement(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills='6.0', roll=4),
            SkillChoiceEvent(id=8, fulfills='7.0', skill='rival'),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_roll_8_betrayal_creates_choice_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=8)]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if p.kind == 'life_event_8'), None)
        assert pending is not None
        assert 'rival' in pending.options and 'enemy' in pending.options

    def test_roll_8_choose_rival_adds_rival(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills='6.0', roll=8),
            SkillChoiceEvent(id=8, fulfills='7.0', skill='rival'),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'rival' for c in projection.summary.connections)

    def test_roll_9_travel_creates_qualification_dm_scheduled_effect(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=9)]
        projection = replay(1, events)

        qual_dm = next((se for se in projection.scheduled_effects if se.trigger == 'qualification'), None)
        assert qual_dm is not None
        assert qual_dm.effect.get('amount') == 2

    def test_roll_9_creates_advancement_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=9)]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_roll_10_good_fortune_creates_advancement_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=10)]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_roll_11_crime_creates_advancement_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=11)]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_roll_2_sickness_creates_injury_table_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=2)]
        projection = replay(1, events)

        assert any(p.kind == 'injury_table' for p in projection.pending_inputs)

    def test_roll_2_after_light_injury_advancement_pending_exists(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills='6.0', roll=2),
            InjuryTableEvent(id=8, fulfills='7.0', roll=6),  # lightly injured — no effect
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)

    def test_roll_12_unusual_creates_life_event_unusual_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills='6.0', roll=12)]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if p.kind == 'life_event_unusual'), None)
        assert pending is not None
        assert pending.options == ['1', '2', '3', '4', '5', '6']

    def test_roll_12_unusual_1_useful_ally_adds_ally(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills='6.0', roll=12),
            LifeEventUnusualEvent(id=8, fulfills='7.0', roll=1),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'ally' for c in projection.summary.connections)

    def test_roll_12_unusual_2_aliens_adds_contact_and_science_skill(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills='6.0', roll=12),
            LifeEventUnusualEvent(id=8, fulfills='7.0', roll=2),
        ]
        projection = replay(1, events)

        assert any(c.kind == 'contact' for c in projection.summary.connections)
        # Any science skill gained at level 1
        science_skills = {'Life Science', 'Physical Science', 'Robotic Science', 'Social Science', 'Space Science'}
        assert any(projection.summary.skills.get(s, -1) >= 1 for s in science_skills)

    def test_roll_12_unusual_3_to_6_no_connections_or_skills(self):
        for roll in [3, 4, 5, 6]:
            events = [
                *self._setup_to_life_event(),
                LifeEventEvent(id=7, fulfills='6.0', roll=12),
                LifeEventUnusualEvent(id=8, fulfills='7.0', roll=roll),
            ]
            projection = replay(1, events)
            assert not projection.summary.connections, f'roll={roll} should have no connections'

    def test_roll_12_unusual_creates_advancement_pending(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills='6.0', roll=12),
            LifeEventUnusualEvent(id=8, fulfills='7.0', roll=1),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


def _setup_through_3_terms_reenlist() -> list:
    """Complete setup and 3 Scout Courier terms. Age=30 after. Skill_table pending at '18.0'."""
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=['Admin', 'Athletics', 'Carouse', 'Drive']),
        # Term 1
        CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills='4.0', roll=7),
        TermEventEvent(id=6, fulfills='5.0', roll=5),
        AdvancementEvent(id=7, fulfills='6.0', roll=3),
        ReenlistEvent(id=8, fulfills='7.0', reenlist=True),  # age=22
        # Term 2
        SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
        SurviveEvent(id=10, fulfills='9.0', roll=7),
        TermEventEvent(id=11, fulfills='10.0', roll=5),
        AdvancementEvent(id=12, fulfills='11.0', roll=3),
        ReenlistEvent(id=13, fulfills='12.0', reenlist=True),  # age=26
        # Term 3
        SkillTableEvent(id=14, fulfills='13.0', table='service_skills', roll=1),
        SurviveEvent(id=15, fulfills='14.0', roll=7),
        TermEventEvent(id=16, fulfills='15.0', roll=5),
        AdvancementEvent(id=17, fulfills='16.0', roll=3),
        ReenlistEvent(id=18, fulfills='17.0', reenlist=True),  # age=30
    ]


def _setup_through_4_terms_advancement() -> list:
    """Complete setup through advancement of term 4. Age still 30.
    Next: ReenlistEvent(fulfills='22.0') triggers aging (age->34)."""
    return [
        *_setup_through_3_terms_reenlist(),
        # Term 4
        SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
        SurviveEvent(id=20, fulfills='19.0', roll=7),
        TermEventEvent(id=21, fulfills='20.0', roll=5),
        AdvancementEvent(id=22, fulfills='21.0', roll=3),
    ]


class TestAging:
    """Aging starts at 34 (end of 4th term). Roll 2D - term_count on aging table."""

    def test_no_aging_at_30(self):
        # After 3 complete terms, age=30 -> no aging_roll pending
        projection = replay(1, _setup_through_3_terms_reenlist())

        assert not any(p.kind == 'aging_roll' for p in projection.pending_inputs)
        assert any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_aging_roll_pending_after_4th_term_reenlist(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'aging_roll' for p in projection.pending_inputs)

    def test_no_skill_table_before_aging_resolves(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert not any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_age_is_34_after_4th_term_reenlist(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 34

    def test_no_effect_creates_skill_table(self):
        # 4 terms: DM=-4. roll=5 -> 5-4=1 -> no effect
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_no_effect_preserves_characteristics(self):
        # STR=7 DEX=8 END=6 -- unchanged
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['STR'] == 7
        assert projection.summary.characteristics['END'] == 6

    def test_effective_0_creates_one_aging_choice(self):
        # roll=4 -> 4-4=0 -> reduce 1 physical by 1
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
        ]
        projection = replay(1, events)

        aging_choices = [p for p in projection.pending_inputs if p.kind == 'aging_choice']
        assert len(aging_choices) == 1
        assert set(aging_choices[0].options) == {'STR', 'DEX', 'END'}

    def test_effective_0_choice_reduces_characteristic(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['STR'] == 6  # was 7

    def test_effective_0_after_choice_creates_skill_table(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_effective_minus1_creates_two_aging_choices(self):
        # roll=3 -> 3-4=-1 -> reduce 2 physicals by 1
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=3),
        ]
        projection = replay(1, events)

        aging_choices = [p for p in projection.pending_inputs if p.kind == 'aging_choice']
        assert len(aging_choices) == 2

    def test_effective_minus1_no_skill_table_until_both_resolved(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=3),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'aging_choice' for p in projection.pending_inputs)
        assert not any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_effective_minus1_skill_table_after_both_resolved(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=3),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
            CharacteristicChoiceEvent(id=26, fulfills='24.1', characteristic='DEX', amount=1),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_effective_minus2_auto_reduces_all_physicals(self):
        # roll=2 -> 2-4=-2 -> auto reduce all 3 physicals by 1, no choice pending
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=2),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['STR'] == 6  # was 7
        assert projection.summary.characteristics['DEX'] == 7  # was 8
        assert projection.summary.characteristics['END'] == 5  # was 6

    def test_effective_minus2_no_aging_choice_pending(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=2),
        ]
        projection = replay(1, events)

        assert not any(p.kind == 'aging_choice' for p in projection.pending_inputs)

    def test_effective_minus2_creates_skill_table(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=2),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_reenlist_false_aging_then_career_ends(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=False),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),  # no effect
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_reenlist_false_aging_no_skill_table(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=False),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),
        ]
        projection = replay(1, events)

        assert not any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_mishap_ejection_at_34_triggers_aging(self):
        # 3 terms (age=30), start 4th, fail survive -> mishap -> age=34 -> aging
        events = [
            *_setup_through_3_terms_reenlist(),
            SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
            SurviveEvent(id=20, fulfills='19.0', roll=3),
            MishapEvent(id=21, fulfills='20.0', roll=5),  # Scout mishap 5: no effects, ejected
        ]
        projection = replay(1, events)

        assert any(p.kind == 'aging_roll' for p in projection.pending_inputs)

    def test_mishap_ejection_aging_career_stays_ended(self):
        events = [
            *_setup_through_3_terms_reenlist(),
            SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
            SurviveEvent(id=20, fulfills='19.0', roll=3),
            MishapEvent(id=21, fulfills='20.0', roll=5),
            AgingRollEvent(id=22, fulfills='21.0', roll=5),  # no effect
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None


def _setup_through_reenlist_false() -> list:
    """1 Scout Courier term, reenlist=False. Age=22, career ended. Muster out pending at '7.0'."""
    # term_count=1, rank=0 → 1 muster out roll (1 term + 0 rank // 2)
    return [
        *_full_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills='4.0', roll=7),
        TermEventEvent(id=6, fulfills='5.0', roll=5),
        AdvancementEvent(id=7, fulfills='6.0', roll=3),  # fail advancement — rank stays 0
        ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
    ]


class TestMusterOut:
    """Muster out: benefit rolls when leaving a career."""

    def test_reenlist_false_creates_muster_out_pending(self):
        # 1 term, rank 0 → 1 roll (1 + 0//2 = 1)
        projection = replay(1, _setup_through_reenlist_false())

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 1

    def test_muster_out_pending_has_cash_and_benefits_options(self):
        projection = replay(1, _setup_through_reenlist_false())

        p = next(p for p in projection.pending_inputs if p.kind == 'muster_out')
        assert set(p.options) == {'cash', 'benefits'}

    def test_muster_out_career_set_while_pendings_remain(self):
        projection = replay(1, _setup_through_reenlist_false())

        assert projection.muster_out_career == 'Scout'

    def test_cash_roll_adds_to_summary_cash(self):
        # Scout roll 1 on cash table → Cr20000
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='cash', roll=1),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 20000

    def test_cash_roll_3_gives_cr30000(self):
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='cash', roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 30000

    def test_benefits_roll_weapon_adds_to_benefits(self):
        # Scout benefits roll 4 → Weapon
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=4),
        ]
        projection = replay(1, events)

        assert 'weapon' in projection.summary.benefits

    def test_benefits_roll_ship_share_adds_to_benefits(self):
        # Scout benefits roll 1 → ship_share
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=1),
        ]
        projection = replay(1, events)

        assert 'ship_share' in projection.summary.benefits

    def test_benefits_roll_int_plus_1_increases_int(self):
        # Scout benefits roll 2 → INT +1 (INT was 9)
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=2),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['INT'] == 10

    def test_benefits_roll_edu_plus_1_increases_edu(self):
        # Scout benefits roll 3 → EDU +1 (EDU was 10)
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['EDU'] == 11

    def test_benefits_roll_scout_ship_adds_to_benefits(self):
        # Scout benefits roll 6 → scout_ship
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=6),
        ]
        projection = replay(1, events)

        assert 'scout_ship' in projection.summary.benefits

    def test_muster_out_career_cleared_after_all_rolls(self):
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='cash', roll=1),
        ]
        projection = replay(1, events)

        assert projection.muster_out_career is None

    def test_roll_count_two_terms_rank_0(self):
        # 2 terms, rank 0 → 2 + 0//2 = 2 rolls
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),  # fail — rank=0
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),  # age=22
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),
            AdvancementEvent(id=12, fulfills='11.0', roll=3),  # fail — rank=0
            ReenlistEvent(id=13, fulfills='12.0', reenlist=False),  # age=26
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 2

    def test_roll_count_includes_rank_bonus(self):
        # 1 term, rank 1 → 1 + 1//2 = 1 + 0 = 1. rank 2 → 1 + 2//2 = 2 rolls
        # Use 2 terms + advance to rank 1 in first term → 2 + 0 = 2
        # Use 1 term with rank 2 → 1 + 1 = 2 rolls
        # Simplest: setup_through_3_terms_reenlist has rank 0 (advancement rolls 3 always fail)
        # Advance in term 1: Scout Courier EDU 9+, EDU=10 DM+1, roll=8 → 8+1=9 ≥ 9 ✓
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=8),  # 8+1=9>=9 → rank 1
            ReenlistEvent(id=8, fulfills='7.0', reenlist=False),  # 1 term, rank 1 → 1 + 1//2 = 1 + 0 = 1
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 1

    def test_roll_count_rank_2_gives_extra_roll(self):
        # rank 2 → rank//2 = 1 extra roll. With 1 term: 1+1=2 rolls
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=8),  # rank 1
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),
            AdvancementEvent(id=12, fulfills='11.0', roll=8),  # rank 2
            ReenlistEvent(id=13, fulfills='12.0', reenlist=False),  # 2 terms, rank 2 → 2+1=3 rolls
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 3

    def test_cash_max_3_times(self):
        # 3 terms, rank 0 → 3 rolls. Take cash 3 times: ok
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),
            AdvancementEvent(id=12, fulfills='11.0', roll=3),
            ReenlistEvent(id=13, fulfills='12.0', reenlist=True),
            SkillTableEvent(id=14, fulfills='13.0', table='service_skills', roll=1),
            SurviveEvent(id=15, fulfills='14.0', roll=7),
            TermEventEvent(id=16, fulfills='15.0', roll=5),
            AdvancementEvent(id=17, fulfills='16.0', roll=3),
            ReenlistEvent(id=18, fulfills='17.0', reenlist=False),  # 3 terms, rank 0 → 3 rolls
            MusterOutEvent(id=19, fulfills='18.0', table='cash', roll=1),
            MusterOutEvent(id=20, fulfills='18.1', table='cash', roll=1),
            MusterOutEvent(id=21, fulfills='18.2', table='cash', roll=1),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 60000
        assert projection.summary.muster_out_cash_count == 3

    def test_cash_4th_time_raises_error(self):
        # 3 terms, rank 2 → 3 + 1 = 4 rolls; cash max 3 → 4th raises error
        # Advance twice: Scout Courier EDU 9+, EDU=10 (DM+1), roll=8 → 8+1=9 ≥ 9 ✓
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=8),  # rank 1
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),  # age=22
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),
            AdvancementEvent(id=12, fulfills='11.0', roll=8),  # rank 2
            ReenlistEvent(id=13, fulfills='12.0', reenlist=True),  # age=26
            SkillTableEvent(id=14, fulfills='13.0', table='service_skills', roll=1),
            SurviveEvent(id=15, fulfills='14.0', roll=7),
            TermEventEvent(id=16, fulfills='15.0', roll=5),
            AdvancementEvent(id=17, fulfills='16.0', roll=3),  # fail
            ReenlistEvent(id=18, fulfills='17.0', reenlist=False),  # age=30, 3 terms rank 2 → 4 rolls
            MusterOutEvent(id=19, fulfills='18.0', table='cash', roll=1),
            MusterOutEvent(id=20, fulfills='18.1', table='cash', roll=1),
            MusterOutEvent(id=21, fulfills='18.2', table='cash', roll=1),
            MusterOutEvent(id=22, fulfills='18.3', table='cash', roll=1),  # 4th cash → error
        ]
        with pytest.raises(ReplayError, match='Cash'):
            replay(1, events)

    def test_mishap_ejection_loses_current_term_benefit(self):
        # 1 term enter → mishap → lose current term's roll → 0 muster out rolls
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail survive
            MishapEvent(id=6, fulfills='5.0', roll=5),  # Scout mishap 5: no effects, ejected
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 0

    def test_mishap_ejection_after_2_terms_gets_1_roll(self):
        # 2 terms: first completes normally (reenlist=True), second term mishap → lose current → 1 roll
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=3),  # fail survive
            MishapEvent(id=11, fulfills='10.0', roll=5),  # ejected, lose current term → 1 roll
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 1

    def test_benefit_dm_tracked_as_scheduled_effect(self):
        # Scout event 5 grants benefit_dm+1 — tracked as a muster_out ScheduledEffect.
        # The player includes the DM in their roll value (MusterOutEvent.roll already includes DMs).
        # Scholar cash row 1=Cr5000, row 2=Cr10000. Player rolls 1 and applies DM+1 → submits roll=2.
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # scholar event 5: benefit_dm +1
            AdvancementEvent(id=7, fulfills='6.0', roll=3),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
        ]
        projection = replay(1, events)

        # benefit_dm tracked as a scheduled effect
        muster_out_dms = [se for se in projection.scheduled_effects if se.trigger == 'muster_out']
        assert len(muster_out_dms) == 1
        assert muster_out_dms[0].effect.get('amount') == 1

    def test_scholar_soc_plus_1_benefit(self):
        # Scholar benefits roll 4 → SOC +1 (SOC was 5)
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=4),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['SOC'] == 6  # was 5

    def test_scholar_two_ship_shares_benefit(self):
        # Scholar benefits roll 3 → Two Ship Shares → 2 ship_share entries
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.benefits.count('ship_share') == 2

    def test_scholar_scientific_equipment_benefit(self):
        # Scholar benefits roll 5 → scientific_equipment
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=5),
        ]
        projection = replay(1, events)

        assert 'scientific_equipment' in projection.summary.benefits

    def test_aging_reenlist_false_gets_muster_out_after_aging(self):
        # 4 terms, reenlist=False, age=34 → aging required → muster out after aging resolves
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=False),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),  # no effect (5-4=1)
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) > 0

    def test_aging_reenlist_false_roll_count(self):
        # 4 terms, rank 0 → 4 muster out rolls
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=False),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),  # no effect
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 4

    def test_mishap_aging_muster_out_loses_current_term(self):
        # 4th term mishap ejection with aging → 3 rolls (4-1=3 terms, rank 0)
        events = [
            *_setup_through_3_terms_reenlist(),
            SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
            SurviveEvent(id=20, fulfills='19.0', roll=3),  # fail
            MishapEvent(id=21, fulfills='20.0', roll=5),  # ejected, age=34
            AgingRollEvent(id=22, fulfills='21.0', roll=5),  # no effect
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 3


# ── Life event roll=10 and roll=11 ─────────────────────────────────────────


class TestLifeEventGoodFortune:
    """Life event roll=10: Good Fortune — DM+2 to any one Benefit roll."""

    def _setup_through_life_event_10(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),  # life_event pending
            LifeEventEvent(id=7, fulfills='6.0', roll=10),  # Good Fortune
        ]

    def test_good_fortune_creates_muster_out_dm_scheduled_effect(self):
        projection = replay(1, self._setup_through_life_event_10())

        dm_effects = [se for se in projection.scheduled_effects if se.trigger == 'muster_out']
        assert len(dm_effects) == 1
        assert dm_effects[0].effect.get('amount') == 2

    def test_good_fortune_also_creates_advancement_pending(self):
        projection = replay(1, self._setup_through_life_event_10())

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


class TestLifeEventCrime:
    """Life event roll=11: Crime — lose one Benefit roll."""

    def _setup_through_life_event_11(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=7),  # life_event pending
            LifeEventEvent(id=7, fulfills='6.0', roll=11),  # Crime
        ]

    def test_crime_reduces_muster_out_roll_count_by_1(self):
        # 1 term, rank 0 → normally 1 roll; crime reduces by 1 → 0 rolls
        events = [
            *self._setup_through_life_event_11(),
            AdvancementEvent(id=8, fulfills='7.0', roll=3),
            ReenlistEvent(id=9, fulfills='8.0', reenlist=False),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 0

    def test_crime_roll_count_cannot_go_negative(self):
        # 1 term, rank 0, crime → would be -1 rolls → clamped to 0
        events = [
            *self._setup_through_life_event_11(),
            AdvancementEvent(id=8, fulfills='7.0', roll=3),
            ReenlistEvent(id=9, fulfills='8.0', reenlist=False),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 0

    def test_crime_with_2_terms_gives_1_roll(self):
        # 2 terms rank 0 → 2 - 1 = 1 roll
        events = [
            *self._setup_through_life_event_11(),
            AdvancementEvent(id=8, fulfills='7.0', roll=3),
            ReenlistEvent(id=9, fulfills='8.0', reenlist=True),
            SkillTableEvent(id=10, fulfills='9.0', table='service_skills', roll=1),
            SurviveEvent(id=11, fulfills='10.0', roll=7),
            TermEventEvent(id=12, fulfills='11.0', roll=5),
            AdvancementEvent(id=13, fulfills='12.0', roll=3),
            ReenlistEvent(id=14, fulfills='13.0', reenlist=False),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) == 1

    def test_crime_still_creates_advancement_pending(self):
        projection = replay(1, self._setup_through_life_event_11())

        assert any(p.kind == 'advancement' for p in projection.pending_inputs)


# ── Aging crisis ────────────────────────────────────────────────────────────


def _setup_low_str(character_id: int = 1) -> list:
    """Character with STR=1 for aging crisis tests. UCP '1869A5'."""
    # STR=1 DEX=8 END=6 INT=9 EDU=10 SOC=5 — 4 background skills
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='1869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=['Admin', 'Athletics', 'Carouse', 'Drive']),
    ]


def _setup_low_str_through_4_terms_advancement() -> list:
    """Low-STR character through 4 terms to advancement, ready for ReenlistEvent."""
    return [
        *_setup_low_str(),
        # Term 1
        CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills='4.0', roll=7),
        TermEventEvent(id=6, fulfills='5.0', roll=5),
        AdvancementEvent(id=7, fulfills='6.0', roll=3),
        ReenlistEvent(id=8, fulfills='7.0', reenlist=True),  # age=22
        # Term 2
        SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
        SurviveEvent(id=10, fulfills='9.0', roll=7),
        TermEventEvent(id=11, fulfills='10.0', roll=5),
        AdvancementEvent(id=12, fulfills='11.0', roll=3),
        ReenlistEvent(id=13, fulfills='12.0', reenlist=True),  # age=26
        # Term 3
        SkillTableEvent(id=14, fulfills='13.0', table='service_skills', roll=1),
        SurviveEvent(id=15, fulfills='14.0', roll=7),
        TermEventEvent(id=16, fulfills='15.0', roll=5),
        AdvancementEvent(id=17, fulfills='16.0', roll=3),
        ReenlistEvent(id=18, fulfills='17.0', reenlist=True),  # age=30
        # Term 4
        SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
        SurviveEvent(id=20, fulfills='19.0', roll=7),
        TermEventEvent(id=21, fulfills='20.0', roll=5),
        AdvancementEvent(id=22, fulfills='21.0', roll=3),
    ]


class TestAgingCrisis:
    """Aging crisis: any characteristic reduced to 0 triggers crisis pending."""

    def test_crisis_pending_when_str_reaches_0(self):
        # STR=1, aging effective=0 (1 physical -1) → choose STR → STR=0 → crisis
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),  # 4-4=0: one physical -1
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
        ]
        projection = replay(1, events)

        assert any(p.kind == 'aging_crisis' for p in projection.pending_inputs)

    def test_no_skill_table_before_crisis_resolved(self):
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
        ]
        projection = replay(1, events)

        assert not any(p.kind == 'skill_table' for p in projection.pending_inputs)

    def test_crisis_triggered_by_auto_reduction(self):
        # STR=1, aging effective=-2 (all 3 physicals -1, auto) → STR=0 → crisis
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=2),  # 2-4=-2: auto all physicals -1
        ]
        projection = replay(1, events)

        assert any(p.kind == 'aging_crisis' for p in projection.pending_inputs)

    def test_crisis_clears_remaining_aging_choices(self):
        # effective=-1: 2 aging_choices; choose STR first → STR=0 → crisis clears the other
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=3),  # 3-4=-1: 2 physicals -1
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
        ]
        projection = replay(1, events)

        aging_choices = [p for p in projection.pending_inputs if p.kind == 'aging_choice']
        assert len(aging_choices) == 0
        assert any(p.kind == 'aging_crisis' for p in projection.pending_inputs)

    def test_crisis_paid_restores_str_to_1(self):
        from ceres.character.events import AgingCrisisEvent

        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=True, medical_roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics['STR'] == 1

    def test_crisis_paid_ends_career(self):
        from ceres.character.events import AgingCrisisEvent

        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=True, medical_roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_crisis_paid_creates_muster_out_pendings(self):
        from ceres.character.events import AgingCrisisEvent

        # 4 terms reenlisting → crisis during term 5 aging (reenlist=True path)
        # term_count at crisis: 4 (from 4 reenlist=True increments in _complete_aging for terms 1-4)
        # Actually: in reenlist=True aging path, term_count is incremented in _complete_aging.
        # After 3 completed terms (3 reenlist=True non-aging), term_count=3 after 3rd reenlist.
        # Then term 4: reenlist=True with aging → pending_reenlist=True → crisis before _complete_aging
        # → term_count still=3 at crisis time, but _apply_aging_crisis adds 1 for completed term → 4 rolls
        # rank=0 → 4 + 0 = 4 muster out rolls
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),  # triggers aging
            AgingRollEvent(id=24, fulfills='23.0', roll=4),  # effective=0: one choice
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=True, medical_roll=3),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if p.kind == 'muster_out']
        assert len(muster_out_pendings) > 0

    def test_crisis_die_marks_character_dead(self):
        from ceres.character.events import AgingCrisisEvent

        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=False, medical_roll=0),
        ]
        projection = replay(1, events)

        assert projection.summary.dead is True

    def test_crisis_die_no_muster_out(self):
        from ceres.character.events import AgingCrisisEvent

        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic='STR', amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=False, medical_roll=0),
        ]
        projection = replay(1, events)

        assert not any(p.kind == 'muster_out' for p in projection.pending_inputs)
