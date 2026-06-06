"""Tests for career flow: complete Scout Courier term, scripted with deterministic rolls."""

import pytest

from ceres.character.characteristics import Chars, ConnectionKind
from ceres.character.events import (
    AdvancementEvent,
    AssignmentChangeChoiceEvent,
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    ConnectionKindChoiceEvent,
    InjuryTableEvent,
    LifeEventCrimeLoseBenefitRoll,
    LifeEventCrimeTakePrisoner,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
    PendingAdvancement,
    PendingAgingRoll,
    PendingAssignmentChangeChoice,
    PendingCareerChoice,
    PendingCharacteristicChoice,
    PendingChoices,
    PendingInjuryTable,
    PendingLifeEvent,
    PendingLifeEventChoice,
    PendingLifeEventUnusual,
    PendingMishap,
    PendingMusterOut,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingSkillChoice,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingSurvive,
    PendingTermEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import ReplayError, replay
from ceres.character.skills import (
    Admin,
    Astrogation,
    Athletics,
    Carouse,
    Diplomat,
    Drive,
    Electronics,
    Flyer,
    GunCombat,
    Investigate,
    Level,
    LifeScience,
    Mechanic,
    Medic,
    PhysicalScience,
    Pilot,
    RoboticScience,
    SocialScience,
    SpaceScience,
    Survival,
    VaccSuit,
)
from ceres.character.sophonts import VILANI
from ceres.character.state import (
    Ally,
    BenefitRollDm,
    Contact,
    Enemy,
    Rival,
)
from tests.character.helpers import MOCK_WORLD


class TestCoreCareerCoverage:
    def test_all_core_careers_are_loaded(self):
        from ceres.character.careers.loader import load_careers

        assert {
            'Agent',
            'Army',
            'Citizen',
            'Drifter',
            'Entertainer',
            'Marines',
            'Merchant',
            'Navy',
            'Noble',
            'Prisoner',
            'Rogue',
            'Scholar',
            'Scout',
        } <= set(load_careers())

    @pytest.mark.parametrize(
        ('career_name', 'assignments'),
        [
            ('Entertainer', {'Artist', 'Journalist', 'Performer'}),
            ('Noble', {'Administrator', 'Diplomat', 'Dilettante'}),
            ('Rogue', {'Thief', 'Enforcer', 'Pirate'}),
        ],
    )
    def test_remaining_core_careers_have_assignments(self, career_name, assignments):
        from ceres.character.careers.loader import load_careers

        career = load_careers()[career_name]

        assert {assignment.name for assignment in career.assignments} == assignments
        assert career.skill_table('personal_development') is not None
        assert career.skill_table('service_skills') is not None
        assert career.skill_table('advanced_education') is not None

    def test_entertainer_qualification_accepts_dex_or_int(self):
        events = [
            CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
            UcpEvent(id=2, fulfills=(1, 0), ucp='7833A5'),
            BackgroundSkillsEvent(id=3, fulfills=(2, 0), skills=[Admin(), Athletics(), Carouse(), Drive()]),
            CareerEvent(id=4, fulfills=(3, 0), career='Entertainer', assignment='Performer', qualification_roll=5),
        ]

        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Entertainer'


def _full_setup(character_id: int = 1) -> list:
    """Return events that get a character through setup: started → ucp → background skills."""
    # STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 → 4 background skills
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills=(1, 0), ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills=(2, 0), skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _scholar_setup(character_id: int = 1) -> list:
    """Like _full_setup() but with Medic instead of Drive.

    Scholar service_skills row 1 offers Drive/Flyer. Using Drive in background causes Flyer to be
    auto-granted (only 1 option left). This setup preserves both options so Scholar initial training
    creates two choice pendings: Drive/Flyer (id .0) and Science (id .1).
    """
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills=(1, 0), ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills=(2, 0), skills=[Admin(), Athletics(), Carouse(), Medic()]),
    ]


class TestQualification:
    """Qualification roll on career entry."""

    def test_success_starts_career(self):
        # Scout: INT 5+, character has INT=9 (DM+1), roll 5 → 5+1=6 >= 5
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)

    def test_failure_clears_career_and_creates_draft_pending(self):
        # Scout: INT 5+, INT=9 (DM+1), roll 3 → 3+1=4 < 5
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None
        from ceres.character.events import PendingDraftChoice

        pi = next(p for p in projection.pending_inputs if isinstance(p, PendingDraftChoice))
        assert 'draft' in pi.options
        assert 'drifter' in pi.options

    def test_failure_adds_problem_with_career_name(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=3),
        ]
        projection = replay(1, events)

        assert any('Scout' in p for p in projection.summary.problems)

    def test_scholar_failure(self):
        # Scholar: INT 6+, INT=9 (DM+1), roll 4 → 4+1=5 < 6
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Field Researcher', qualification_roll=4),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_scholar_success(self):
        # EDU=10 (DM+1), roll 5 → 5+1=6 >= 6
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Field Researcher', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scholar'

    def test_retry_after_failure_can_succeed(self):
        # Fail Scout, then succeed Scholar
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=3),
            CareerEvent(id=5, fulfills=(4, 0), career='Scholar', assignment='Field Researcher', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scholar'


class TestSubsequentBasicTraining:
    """Re-entering a career gets basic training (one service skill pick), not a skill roll."""

    def _setup_scout_then_agent_muster_out(self) -> list:
        """Scout term 1 → muster out → Agent/Intelligence term 1 → muster out.

        Uses Scout event roll=5 (BenefitDm, no pending) and Agent event roll=4 (BenefitDm, no pending).
        Agent qualification: INT 5+, INT=9 DM+1, roll=4 → 5 >= 5 → pass.
        Agent advancement: INT 5+, roll=3 → 4 < 5 → fail.
        """
        return [
            *_full_setup(),
            # Scout term 1
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),
            AdvancementEvent(id=7, fulfills=(6, 0), roll=3),
            ReenlistEvent(id=8, fulfills=(7, 0), reenlist=False),
            MusterOutEvent(id=9, fulfills=(8, 0), table='cash', roll=1),
            # Agent/Intelligence term 1 (2nd career → basic training: one service skill pick)
            CareerEvent(id=10, fulfills=(9, 0), career='Agent', assignment='Intelligence', qualification_roll=5),
            SkillChoiceEvent(id=11, fulfills=(10, 0), skill=Investigate()),
            SurviveEvent(id=12, fulfills=(11, 0), roll=9),
            TermEventEvent(id=13, fulfills=(12, 0), roll=4),
            AdvancementEvent(id=14, fulfills=(13, 0), roll=3),
            ReenlistEvent(id=15, fulfills=(14, 0), reenlist=False),
            MusterOutEvent(id=16, fulfills=(15, 0), table='cash', roll=1),
        ]

    def test_scout_reentry_creates_survive_not_skill_table(self):
        """Re-entering Scout (all service skills already known) gives survival pending, not skill roll."""
        events = [
            *self._setup_scout_then_agent_muster_out(),
            CareerEvent(id=17, fulfills=(16, 0), career='Scout', assignment='Courier', qualification_roll=7),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)
        assert not any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_scout_reentry_survival_id_from_career_event(self):
        """Survival pending ID is career_event.id.0 — no skill table interleaved."""
        events = [
            *self._setup_scout_then_agent_muster_out(),
            CareerEvent(id=17, fulfills=(16, 0), career='Scout', assignment='Courier', qualification_roll=7),
        ]
        projection = replay(1, events)

        survive_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSurvive))
        assert survive_pending.id == '17.0'


class TestCareerEntry:
    def test_career_event_creates_survive_pending(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)

    def test_career_event_sets_current_career_in_summary(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
        assert projection.summary.current_assignment == 'Courier'

    def test_career_event_grants_initial_training_service_skills(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        # First term: all service skills at level 0
        assert projection.summary.skill_level(Pilot) == 0
        assert projection.summary.skill_level(Survival) == 0
        assert projection.summary.skill_level(Mechanic) == 0
        assert projection.summary.skill_level(Astrogation) == 0
        assert projection.summary.skill_level(VaccSuit) == 0
        assert projection.summary.skill_level(GunCombat) == 0

    def test_career_event_rejects_unknown_career(self):
        with pytest.raises(ReplayError):
            replay(
                1,
                [
                    *_full_setup(),
                    CareerEvent(id=4, fulfills=(3, 0), career='Pirate', assignment='Freebooter', qualification_roll=7),
                ],
            )

    def test_career_event_rejects_unknown_assignment(self):
        with pytest.raises(ReplayError):
            replay(
                1,
                [
                    *_full_setup(),
                    CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Admiral', qualification_roll=7),
                ],
            )

    def test_career_pending_id_derived_from_background_skills_event_id(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        survive_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSurvive))
        # The survive pending is created by the career event (id=4), so it's 4.0
        assert survive_pending.id == '4.0'

    def test_survive_pending_instruction_mentions_target(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
        ]

        projection = replay(1, events)

        survive_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSurvive))
        # Courier survival: END 5+
        assert 'END' in survive_pending.instruction
        assert '5' in survive_pending.instruction

    def test_scholar_career_event_grants_non_choice_service_skills(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Field Researcher', qualification_roll=5),
        ]

        projection = replay(1, events)

        # Non-choice Scholar service skills are granted
        assert projection.summary.skill_level(Electronics) is not None
        assert projection.summary.skill_level(Diplomat) is not None
        assert projection.summary.skill_level(Medic) is not None
        assert projection.summary.skill_level(Investigate) is not None
        # Drive already known → Flyer is the only remaining option → auto-granted, no dialog
        assert projection.summary.skill_level(Flyer) is not None
        # Science still requires a choice (5 options)
        assert projection.summary.skill_level(LifeScience) is None


class TestSurvive:
    def _setup_with_career(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
        ]

    def test_survive_success_creates_term_event_pending(self):
        # END=6 (DM+0), need 5+, roll 7 → success
        events = [*self._setup_with_career(), SurviveEvent(id=5, fulfills=(4, 0), roll=7)]

        projection = replay(1, events)

        assert any(isinstance(p, PendingTermEvent) for p in projection.pending_inputs)

    def test_survive_failure_creates_mishap_pending(self):
        # END=6 (DM+0), need 5+, roll 3 → failure
        events = [*self._setup_with_career(), SurviveEvent(id=5, fulfills=(4, 0), roll=3)]

        projection = replay(1, events)

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_natural_2_always_fails(self):
        # Natural 2 always fails regardless of characteristic DMs
        events = [*self._setup_with_career(), SurviveEvent(id=5, fulfills=(4, 0), roll=2)]

        projection = replay(1, events)

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_survive_success_at_exact_target(self):
        # END=6 (DM+0), need 5+, roll 5 → success
        events = [*self._setup_with_career(), SurviveEvent(id=5, fulfills=(4, 0), roll=5)]

        projection = replay(1, events)

        assert any(isinstance(p, PendingTermEvent) for p in projection.pending_inputs)


class TestMishap:
    def _setup_through_failed_survive(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=3),  # fail
        ]

    def test_mishap_resolves_mishap_pending(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills=(5, 0), roll=5)]

        projection = replay(1, events)

        assert not any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_mishap_ends_career(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills=(5, 0), roll=5)]

        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_mishap_records_mishap_text_in_problems(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills=(5, 0), roll=5)]

        projection = replay(1, events)

        assert len(projection.summary.problems) > 0


class TestTermEvent:
    def _setup_through_survive(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),  # success
        ]

    def test_term_event_resolves_pending_creates_life_event_pending(self):
        events = [*self._setup_through_survive(), TermEventEvent(id=6, fulfills=(5, 0), roll=7)]

        projection = replay(1, events)

        assert not any(isinstance(p, PendingTermEvent) for p in projection.pending_inputs)
        assert any(isinstance(p, PendingLifeEvent) for p in projection.pending_inputs)

    def test_event_7_life_event_blocks_advancement_until_resolved(self):
        # Life event (7) creates life_event pending; advancement is not visible until life event resolves
        events = [*self._setup_through_survive(), TermEventEvent(id=6, fulfills=(5, 0), roll=7)]

        projection = replay(1, events)

        assert any(isinstance(p, PendingLifeEvent) for p in projection.pending_inputs)
        assert not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_event_4_skill_choice_creates_skill_choice_pending(self):
        # Event 4 for Scout: gain one of Animals, Survival, Recon, Science
        events = [*self._setup_through_survive(), TermEventEvent(id=6, fulfills=(5, 0), roll=4)]

        projection = replay(1, events)

        # Should have both a skill_choice pending and the advancement pending
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)


class TestAdvancement:
    def _setup_through_term_event(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # benefit_dm → direct advancement
        ]

    def test_advancement_success_increases_rank(self):
        # EDU=10 (DM+1), need 9+, roll 9 → success (9+1=10 >= 9)
        events = [*self._setup_through_term_event(), AdvancementEvent(id=7, fulfills=(6, 0), roll=9)]

        projection = replay(1, events)

        assert projection.summary.rank == 1  # Scout rank 1

    def test_advancement_success_grants_rank_bonus_skill(self):
        # Rank 1 Scout gets Vacc Suit 1
        events = [*self._setup_through_term_event(), AdvancementEvent(id=7, fulfills=(6, 0), roll=9)]

        projection = replay(1, events)

        assert projection.summary.skill_level(VaccSuit) == 1

    def test_advancement_failure_keeps_rank(self):
        events = [*self._setup_through_term_event(), AdvancementEvent(id=7, fulfills=(6, 0), roll=5)]

        projection = replay(1, events)

        assert projection.summary.rank == 0

    def test_advancement_creates_assignment_change_pending(self):
        events = [*self._setup_through_term_event(), AdvancementEvent(id=7, fulfills=(6, 0), roll=9)]

        projection = replay(1, events)

        assert any(isinstance(p, PendingAssignmentChangeChoice) for p in projection.pending_inputs)

    def test_advancement_instruction_mentions_target(self):
        setup = self._setup_through_term_event()
        projection = replay(1, setup)

        adv_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingAdvancement))
        # Courier advancement: EDU 9+
        assert 'EDU' in adv_pending.instruction
        assert '9' in adv_pending.instruction


class TestAdvancementForcedLeave:
    """Advancement roll ≤ terms in career → character must leave (Core p.24)."""

    def _setup_scout_through_term_event(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # BenefitDm → PendingAdvancement
        ]

    def test_roll_1_in_term_1_removes_reenlist_choice(self):
        # roll=1 ≤ 1 term → forced leave; no reenlist or assignment-change choice
        events = [*self._setup_scout_through_term_event(), AdvancementEvent(id=7, fulfills=(6, 0), roll=1)]
        projection = replay(1, events)

        assert not any(
            isinstance(p, (PendingReenlist, PendingAssignmentChangeChoice)) for p in projection.pending_inputs
        )

    def test_roll_1_in_term_1_queues_muster_out(self):
        events = [*self._setup_scout_through_term_event(), AdvancementEvent(id=7, fulfills=(6, 0), roll=1)]
        projection = replay(1, events)

        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_roll_2_in_term_1_is_normal_path(self):
        # roll=2 > 1 term → normal assignment-change choice (Scout has allows_assignment_change)
        events = [*self._setup_scout_through_term_event(), AdvancementEvent(id=7, fulfills=(6, 0), roll=2)]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAssignmentChangeChoice) for p in projection.pending_inputs)


class TestAdvancementNatural12Stay:
    """Natural 12 on advancement dice forces the character to stay (Core p.24)."""

    def test_natural_12_scout_removes_muster_out_option(self):
        # Scout Courier advancement roll=12 → success + forced stay
        # Scout allows_assignment_change → PendingAssignmentChangeChoice without 'muster_out'
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),
            AdvancementEvent(id=7, fulfills=(6, 0), roll=12),
        ]
        projection = replay(1, events)

        asc = next((p for p in projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice)), None)
        assert asc is not None
        assert 'muster_out' not in asc.options

    def test_natural_12_merchant_forces_reenlist_true_only(self):
        # Merchant Marine advancement roll=12 → success + forced stay
        # Merchant has no allows_assignment_change → PendingReenlist with options=['true']
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Merchant', assignment='Merchant Marine', qualification_roll=3),
            SurviveEvent(id=5, fulfills=(4, 0), roll=4),
            TermEventEvent(id=6, fulfills=(5, 0), roll=10),  # BenefitDm → PendingAdvancement
            AdvancementEvent(id=7, fulfills=(6, 0), roll=12),
        ]
        projection = replay(1, events)

        reenlist = next((p for p in projection.pending_inputs if isinstance(p, PendingReenlist)), None)
        assert reenlist is not None
        assert reenlist.options == ['true']


class TestReenlist:
    def _setup_through_advancement(self, advancement_roll: int = 9) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills=(6, 0), roll=advancement_roll),
        ]

    def test_same_assignment_starts_another_term(self):
        events = [*self._setup_through_advancement(), AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='same')]

        projection = replay(1, events)

        assert projection.summary.terms_started_in_current_career == 2

    def test_same_assignment_creates_skill_table_pending(self):
        events = [*self._setup_through_advancement(), AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='same')]

        projection = replay(1, events)

        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_muster_out_ends_career(self):
        events = [
            *self._setup_through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='muster_out'),
        ]

        projection = replay(1, events)

        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_assignment_change_pending_options(self):
        """Scout shows same + two other assignments + muster_out."""
        setup = self._setup_through_advancement()
        projection = replay(1, setup)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice))
        assert 'same' in pending.options
        assert 'muster_out' in pending.options
        assert 'Surveyor' in pending.options
        assert 'Explorer' in pending.options


class TestSkillTable:
    def _setup_in_term_2(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills=(6, 0), roll=9),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='same'),
        ]

    def test_skill_table_courier_roll_specialised_creates_choice_pending(self):
        # Courier table roll 1: Electronics (specialised) → PendingSkillTableChoice, not auto-granted
        events = [*self._setup_in_term_2(), SkillTableEvent(id=9, fulfills=(8, 0), table='courier', roll=1)]

        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert Electronics() in pending.options

    def test_skill_table_courier_roll_specialised_grants_after_choice(self):
        # Choose Electronics (Comms) → Electronics (Comms) 1 granted
        events = [
            *self._setup_in_term_2(),
            SkillTableEvent(id=9, fulfills=(8, 0), table='courier', roll=1),
            SkillChoiceEvent(id=10, fulfills=(9, 0), skill=Electronics(comms=Level(value=1))),
        ]

        projection = replay(1, events)

        assert projection.summary.skill_level(Electronics) == 1

    def test_skill_table_personal_development_characteristic_increase(self):
        # Personal development roll 1: STR +1 (STR was 7, should be 8)
        events = [
            *self._setup_in_term_2(),
            SkillTableEvent(id=9, fulfills=(8, 0), table='personal_development', roll=1),
        ]

        projection = replay(1, events)

        assert projection.summary.characteristics.get(Chars.STR) == 8

    def test_skill_table_creates_survive_pending_after_non_specialised_roll(self):
        # Personal development roll 1 (STR) — non-specialised → survive appears immediately
        events = [
            *self._setup_in_term_2(),
            SkillTableEvent(id=9, fulfills=(8, 0), table='personal_development', roll=1),
        ]

        projection = replay(1, events)

        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)

    def test_skill_table_specialised_survive_pending_after_choice(self):
        # Electronics (specialised) → survive only appears after the specialisation choice
        events = [
            *self._setup_in_term_2(),
            SkillTableEvent(id=9, fulfills=(8, 0), table='courier', roll=1),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)

        events.append(SkillChoiceEvent(id=10, fulfills=(9, 0), skill=Electronics(comms=Level(value=1))))
        projection = replay(1, events)
        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)

    def test_skill_table_rejects_advanced_education_when_edu_too_low(self):
        # EDU=10 meets Scout advanced education min EDU 8
        # Make a character with EDU=6 to fail the advanced education requirement
        low_edu_events = [
            CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
            UcpEvent(id=2, fulfills=(1, 0), ucp='786600'),  # EDU=6
            BackgroundSkillsEvent(id=3, fulfills=(2, 0), skills=[Admin(), Athletics(), Drive()]),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills=(6, 0), roll=9),
            ReenlistEvent(id=8, fulfills=(7, 0), reenlist=True),
        ]
        with pytest.raises(ReplayError):
            replay(
                1,
                [*low_edu_events, SkillTableEvent(id=9, fulfills=(8, 0), table='advanced_education', roll=1)],
            )


class TestTermEventRollMishap:
    """Event 2 Disaster! — creates mishap pending; character stays in career."""

    def _setup_to_disaster(
        self, career: str = 'Scout', assignment: str = 'Courier', qualification_roll: int = 7
    ) -> list:
        return [
            *_full_setup(),
            CareerEvent(
                id=4, fulfills=(3, 0), career=career, assignment=assignment, qualification_roll=qualification_roll
            ),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=2),
        ]

    def test_creates_mishap_pending(self):
        projection = replay(1, self._setup_to_disaster())

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_mishap_stay_keeps_career(self):
        events = [
            *self._setup_to_disaster(),
            MishapEvent(id=7, fulfills=(6, 0), roll=5, stay_in_career=True),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'

    def test_mishap_stay_creates_advancement_pending(self):
        events = [
            *self._setup_to_disaster(),
            MishapEvent(id=7, fulfills=(6, 0), roll=5, stay_in_career=True),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_works_for_scholar_too(self):
        # _full_setup includes Drive, so Drive/Flyer row auto-grants Flyer; only Science needs a choice.
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=SpaceScience()),
            SurviveEvent(id=6, fulfills=(5, 0), roll=7),
            TermEventEvent(id=7, fulfills=(6, 0), roll=2),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)


class TestTermEventAutoAdvance:
    """Event 12 — automatic promotion, no advancement roll needed."""

    def test_scout_event_12_promotes_rank(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=12),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 1

    def test_scout_event_12_applies_rank_1_vacc_suit_bonus(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=12),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(VaccSuit) == 1

    def test_creates_assignment_change_pending_not_advancement(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=12),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAssignmentChangeChoice) for p in projection.pending_inputs)
        assert not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_scholar_event_12_promotes_and_creates_science_choice_pending(self):
        # Rank 1 bonus is Science 1 (player chooses which broad science) — Core p.43
        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=Drive()),
            SkillChoiceEvent(id=6, fulfills=(4, 1), skill=SpaceScience()),
            SurviveEvent(id=7, fulfills=(6, 0), roll=7),
            TermEventEvent(id=8, fulfills=(7, 0), roll=12),
        ]
        projection = replay(1, events)

        from ceres.character.skills import Sciences, _skill_classes

        assert projection.summary.rank == 1
        science_classes = set(_skill_classes(Sciences))
        pending = next(
            (
                p
                for p in projection.pending_inputs
                if isinstance(p, PendingRankBonusChoice) and {type(s) for s in p.options} == science_classes
            ),
            None,
        )
        assert pending is not None


class TestSkillTableIncrement:
    """Skill table rolls increment: gain at 0 if new, +1 if already possessed."""

    def _setup_in_term_2(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills=(6, 0), roll=9),
            ReenlistEvent(id=8, fulfills=(7, 0), reenlist=True),
        ]

    def test_new_skill_gains_level_1(self):
        # Courier table roll 2: Flyer (specialised) → choice pending, then Flyer 1 after picking spec
        events = [
            *self._setup_in_term_2(),
            SkillTableEvent(id=9, fulfills=(8, 0), table='courier', roll=2),
            SkillChoiceEvent(id=10, fulfills=(9, 0), skill=Flyer(grav=Level(value=1))),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Flyer) == 1

    def test_existing_skill_at_0_increments_to_1(self):
        # Courier table roll 3: Pilot (specialised, existing at 0) → choice pending, then Pilot 1
        events = [
            *self._setup_in_term_2(),
            SkillTableEvent(id=9, fulfills=(8, 0), table='courier', roll=3),
            SkillChoiceEvent(id=10, fulfills=(9, 0), skill=Pilot(spacecraft=Level(value=1))),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Pilot) == 1

    def test_existing_skill_at_1_increments_to_2(self):
        # Scout rank 1 bonus: Vacc Suit 1. Roll service_skills 5 (Vacc Suit) in term 2 → 2
        events = [*self._setup_in_term_2(), SkillTableEvent(id=9, fulfills=(8, 0), table='service_skills', roll=5)]
        projection = replay(1, events)

        assert projection.summary.skill_level(VaccSuit) == 2


class TestSkillTableChoice:
    """Skill table entries with multiple options create a pending choice."""

    def _setup_scholar_term_2(self) -> list:
        return [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Scientist', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=Drive()),
            SkillChoiceEvent(id=6, fulfills=(4, 1), skill=SpaceScience()),
            SurviveEvent(id=7, fulfills=(6, 0), roll=7),
            TermEventEvent(id=8, fulfills=(7, 0), roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=9, fulfills=(8, 0), roll=7),
            ReenlistEvent(id=10, fulfills=(9, 0), reenlist=True),
        ]

    def test_choice_entry_creates_skill_table_choice_pending(self):
        # Scholar service_skills roll 1: Drive/Flyer choice
        events = [
            *self._setup_scholar_term_2(),
            SkillTableEvent(id=11, fulfills=(10, 0), table='service_skills', roll=1),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == {Drive, Flyer}

    def test_choice_increments_chosen_skill(self):
        # Scholar has Drive 0 from initial training → choose Drive → Drive 1
        events = [
            *self._setup_scholar_term_2(),
            SkillTableEvent(id=11, fulfills=(10, 0), table='service_skills', roll=1),
            SkillChoiceEvent(id=12, fulfills=(11, 0), skill=Drive(wheel=Level(value=1))),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Drive) == 1

    def test_language_entry_creates_skill_table_choice_with_all_languages(self):
        # Scholar personal_development roll 6: Language → choice from all Language skills in skills.py
        from ceres.character.skills import Languages, _skill_classes

        events = [
            *self._setup_scholar_term_2(),
            SkillTableEvent(id=11, fulfills=(10, 0), table='personal_development', roll=6),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == set(_skill_classes(Languages))

    def test_science_entry_creates_skill_table_choice_with_all_sciences(self):
        # Scholar service_skills roll 6: Science → choice from all Science skills in skills.py
        from ceres.character.skills import Sciences, _skill_classes

        events = [
            *self._setup_scholar_term_2(),
            SkillTableEvent(id=11, fulfills=(10, 0), table='service_skills', roll=6),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == set(_skill_classes(Sciences))

    def test_art_entry_creates_skill_table_choice_with_all_arts(self):
        # Scholar advanced_education roll 1: Art → choice from all Art skills in skills.py
        from ceres.character.skills import Arts, _skill_classes

        events = [
            *self._setup_scholar_term_2(),
            SkillTableEvent(id=11, fulfills=(10, 0), table='advanced_education', roll=1),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == set(_skill_classes(Arts))

    def test_rank_bonus_science_creates_rank_bonus_choice_with_all_sciences(self):
        # Scholar/Scientist advances to rank 1 → rank bonus = Science choice from skills.py
        from ceres.character.skills import Sciences, _skill_classes

        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Scientist', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=Drive()),
            SkillChoiceEvent(id=6, fulfills=(4, 1), skill=SpaceScience()),
            SurviveEvent(id=7, fulfills=(6, 0), roll=7),
            TermEventEvent(id=8, fulfills=(7, 0), roll=5),
            AdvancementEvent(id=9, fulfills=(8, 0), roll=7),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingRankBonusChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == set(_skill_classes(Sciences))

    def test_choice_creates_survive_pending_not_advancement(self):
        events = [
            *self._setup_scholar_term_2(),
            SkillTableEvent(id=11, fulfills=(10, 0), table='service_skills', roll=1),
            SkillChoiceEvent(id=12, fulfills=(11, 0), skill=Flyer(grav=Level(value=1))),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)
        assert not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestAdvancementDmFromScheduledEffects:
    """Pending advancement DMs are consumed and applied during the advancement check."""

    def test_breakthrough_dm_helps_marginal_roll_succeed(self):
        # Scholar Scientist: INT 9 (DM+1) needs INT 8+
        # Without event DM: roll 6 + DM+1 = 7 < 8 → fail
        # With Scholar event 9 DM+2: roll 6 + DM+1 + DM+2 = 9 >= 8 → success
        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Scientist', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=Drive()),
            SkillChoiceEvent(id=6, fulfills=(4, 1), skill=SpaceScience()),
            SurviveEvent(id=7, fulfills=(6, 0), roll=7),
            TermEventEvent(id=8, fulfills=(7, 0), roll=9),  # breakthrough → DM+2
            AdvancementEvent(id=9, fulfills=(8, 0), roll=6),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 1

    def test_without_dm_same_roll_fails(self):
        # Same roll (6) without the breakthrough DM → 7 < 8 → fail
        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Scientist', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=Drive()),
            SkillChoiceEvent(id=6, fulfills=(4, 1), skill=SpaceScience()),
            SurviveEvent(id=7, fulfills=(6, 0), roll=7),
            TermEventEvent(id=8, fulfills=(7, 0), roll=5),  # benefit_dm (no advancement DM)
            AdvancementEvent(id=9, fulfills=(8, 0), roll=6),
        ]
        projection = replay(1, events)

        assert projection.summary.rank == 0

    def test_breakthrough_dm_is_consumed_after_advancement(self):
        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Scientist', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=Drive()),
            SkillChoiceEvent(id=6, fulfills=(4, 1), skill=SpaceScience()),
            SurviveEvent(id=7, fulfills=(6, 0), roll=7),
            TermEventEvent(id=8, fulfills=(7, 0), roll=9),
            AdvancementEvent(id=9, fulfills=(8, 0), roll=6),
        ]
        projection = replay(1, events)

        assert projection.pending_advancement_dm == 0


class TestSevereInjury:
    """Mishap 1 for Scout and Scholar: severely injured — reduce one physical characteristic by 2."""

    def _setup_through_failed_survive(
        self, career: str = 'Scout', assignment: str = 'Courier', qualification_roll: int = 7
    ) -> list:
        return [
            *_full_setup(),
            CareerEvent(
                id=4, fulfills=(3, 0), career=career, assignment=assignment, qualification_roll=qualification_roll
            ),
            SurviveEvent(id=5, fulfills=(4, 0), roll=3),  # fail
        ]

    def test_scout_mishap_1_creates_characteristic_choice_for_physical_stats(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills=(5, 0), roll=1)]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice)), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}

    def test_scout_mishap_1_instruction_mentions_reduction_of_2(self):
        events = [*self._setup_through_failed_survive(), MishapEvent(id=6, fulfills=(5, 0), roll=1)]
        projection = replay(1, events)

        choice = next(p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice))
        assert '2' in choice.instruction

    def test_scout_mishap_1_choice_reduces_characteristic_by_2(self):
        events = [
            *self._setup_through_failed_survive(),
            MishapEvent(id=6, fulfills=(5, 0), roll=1),
            CharacteristicChoiceEvent(id=7, fulfills=(6, 0), characteristic=Chars.STR, amount=2),
        ]
        projection = replay(1, events)

        # STR was 7 from UCP '7869A5'
        assert projection.summary.characteristics[Chars.STR] == 5

    def test_scholar_mishap_1_also_creates_characteristic_choice(self):
        # Scholar Field Researcher (with Drive in background) has one initial training choice before survive.
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=LifeScience()),
            SurviveEvent(id=6, fulfills=(5, 0), roll=3),  # fail
            MishapEvent(id=7, fulfills=(6, 0), roll=1),
        ]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice)), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}

    def test_normal_injury_still_reduces_by_1(self):
        # Scout mishap 6: normal injury should still only reduce by 1
        events = [
            *self._setup_through_failed_survive(),
            MishapEvent(id=6, fulfills=(5, 0), roll=6),
            CharacteristicChoiceEvent(id=7, fulfills=(6, 0), characteristic=Chars.STR),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.STR] == 6  # 7 - 1


class TestLifeEvents:
    """Term event roll 7 triggers the Life Events table (2D roll, 11 outcomes)."""

    def _setup_to_life_event(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=7),
        ]

    def test_creates_life_event_pending(self):
        projection = replay(1, self._setup_to_life_event())

        assert any(isinstance(p, PendingLifeEvent) for p in projection.pending_inputs)

    def test_roll_7_new_contact_adds_contact(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=7)]
        projection = replay(1, events)

        assert any(isinstance(c, Contact) for c in projection.summary.connections)

    def test_roll_7_creates_advancement_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=7)]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_roll_5_improved_relationship_adds_ally(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=5)]
        projection = replay(1, events)

        assert any(isinstance(c, Ally) for c in projection.summary.connections)

    def test_roll_6_new_relationship_adds_ally(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=6)]
        projection = replay(1, events)

        assert any(isinstance(c, Ally) for c in projection.summary.connections)

    def test_roll_3_birth_or_death_creates_advancement_no_mechanical_effect(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=3)]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        # no characteristic or connection changes
        assert not projection.summary.connections

    def test_roll_4_ending_relationship_creates_choice_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=4)]
        projection = replay(1, events)

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingLifeEventChoice) and p.roll == 4), None
        )
        assert pending is not None
        assert set(pending.options) == {'connection_rival', 'connection_enemy'}

    def test_roll_4_choose_rival_adds_rival(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills=(6, 0), roll=4),
            ConnectionKindChoiceEvent(id=8, fulfills=(7, 0), connection_kind=ConnectionKind.RIVAL),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Rival) for c in projection.summary.connections)

    def test_roll_4_choose_enemy_adds_enemy(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills=(6, 0), roll=4),
            ConnectionKindChoiceEvent(id=8, fulfills=(7, 0), connection_kind=ConnectionKind.ENEMY),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_roll_4_choice_resolves_to_advancement(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills=(6, 0), roll=4),
            ConnectionKindChoiceEvent(id=8, fulfills=(7, 0), connection_kind=ConnectionKind.RIVAL),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_roll_8_betrayal_creates_choice_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=8)]
        projection = replay(1, events)

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingLifeEventChoice) and p.roll == 8), None
        )
        assert pending is not None
        assert ConnectionKind.RIVAL in pending.options and ConnectionKind.ENEMY in pending.options

    def test_roll_8_choose_rival_adds_rival(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills=(6, 0), roll=8),
            ConnectionKindChoiceEvent(id=8, fulfills=(7, 0), connection_kind=ConnectionKind.RIVAL),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Rival) for c in projection.summary.connections)

    def test_roll_9_travel_creates_qualification_dm_scheduled_effect(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=9)]
        projection = replay(1, events)

        assert projection.pending_qualification_dm == 2

    def test_roll_9_creates_advancement_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=9)]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_roll_10_good_fortune_creates_advancement_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=10)]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_roll_11_crime_creates_advancement_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=11)]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_roll_2_sickness_creates_injury_table_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=2)]
        projection = replay(1, events)

        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_roll_2_after_light_injury_advancement_pending_exists(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills=(6, 0), roll=2),
            InjuryTableEvent(id=8, fulfills=(7, 0), roll=6),  # lightly injured — no effect
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_roll_12_unusual_creates_life_event_unusual_pending(self):
        events = [*self._setup_to_life_event(), LifeEventEvent(id=7, fulfills=(6, 0), roll=12)]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingLifeEventUnusual)), None)
        assert pending is not None
        assert pending.options == ['1', '2', '3', '4', '5', '6']

    def test_roll_12_unusual_1_useful_ally_adds_ally(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills=(6, 0), roll=12),
            LifeEventUnusualEvent(id=8, fulfills=(7, 0), roll=1),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Ally) for c in projection.summary.connections)

    def test_roll_12_unusual_2_aliens_adds_contact_and_science_skill(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills=(6, 0), roll=12),
            LifeEventUnusualEvent(id=8, fulfills=(7, 0), roll=2),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Contact) for c in projection.summary.connections)
        # Any science skill gained at level 1
        science_skills = (LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience)
        assert any(projection.summary.skill_level(cls, -1) >= 1 for cls in science_skills)

    def test_roll_12_unusual_3_to_6_no_connections_or_skills(self):
        for roll in [3, 4, 5, 6]:
            events = [
                *self._setup_to_life_event(),
                LifeEventEvent(id=7, fulfills=(6, 0), roll=12),
                LifeEventUnusualEvent(id=8, fulfills=(7, 0), roll=roll),
            ]
            projection = replay(1, events)
            assert not projection.summary.connections, f'roll={roll} should have no connections'

    def test_roll_12_unusual_creates_advancement_pending(self):
        events = [
            *self._setup_to_life_event(),
            LifeEventEvent(id=7, fulfills=(6, 0), roll=12),
            LifeEventUnusualEvent(id=8, fulfills=(7, 0), roll=1),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── Life event roll=10 and roll=11 ─────────────────────────────────────────


class TestLifeEventGoodFortune:
    """Life event roll=10: Good Fortune — DM+2 to any one Benefit roll."""

    def _setup_through_life_event_10(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=7),  # life_event pending
            LifeEventEvent(id=7, fulfills=(6, 0), roll=10),  # Good Fortune
        ]

    def test_good_fortune_stores_benefit_dm_on_muster_out(self):
        projection = replay(1, self._setup_through_life_event_10())

        assert projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms == [BenefitRollDm(amount=2)]

    def test_good_fortune_also_creates_advancement_pending(self):
        projection = replay(1, self._setup_through_life_event_10())

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestLifeEventCrime:
    """Life event roll=11: Crime — choose between losing a Benefit roll or taking Prisoner next term."""

    def _setup_through_life_event_11(self) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=7),  # life_event pending
            LifeEventEvent(id=7, fulfills=(6, 0), roll=11),  # Crime
        ]

    def test_crime_creates_pending_choices_with_two_options(self):
        projection = replay(1, self._setup_through_life_event_11())

        choices_pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert choices_pending is not None
        assert len(choices_pending.choices) == 2
        kinds = {c.kind for c in choices_pending.choices}
        assert kinds == {
            LifeEventCrimeLoseBenefitRoll.model_fields['kind'].default,
            LifeEventCrimeTakePrisoner.model_fields['kind'].default,
        }

    def test_crime_reduces_muster_out_roll_count_by_1(self):
        # 1 term, rank 0 → normally 1 roll; lose-benefit-roll choice reduces by 1 → 0 rolls
        events = [
            *self._setup_through_life_event_11(),
            CareerChoiceEvent.for_choice(LifeEventCrimeLoseBenefitRoll, id=8, fulfills=(7, 0)),
            AdvancementEvent(id=9, fulfills=(7, 1), roll=3),
            ReenlistEvent(id=10, fulfills=(9, 0), reenlist=False),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 0

    def test_crime_roll_count_cannot_go_negative(self):
        # 1 term, rank 0, lose-benefit-roll → would be -1 rolls → clamped to 0
        events = [
            *self._setup_through_life_event_11(),
            CareerChoiceEvent.for_choice(LifeEventCrimeLoseBenefitRoll, id=8, fulfills=(7, 0)),
            AdvancementEvent(id=9, fulfills=(7, 1), roll=3),
            ReenlistEvent(id=10, fulfills=(9, 0), reenlist=False),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 0

    def test_crime_with_2_terms_gives_1_roll(self):
        # 2 terms rank 0 → lose-benefit-roll reduces 2 → 1 roll
        events = [
            *self._setup_through_life_event_11(),
            CareerChoiceEvent.for_choice(LifeEventCrimeLoseBenefitRoll, id=8, fulfills=(7, 0)),
            AdvancementEvent(id=9, fulfills=(7, 1), roll=3),
            ReenlistEvent(id=10, fulfills=(9, 0), reenlist=True),
            SkillTableEvent(id=11, fulfills=(10, 0), table='service_skills', roll=5),
            SurviveEvent(id=12, fulfills=(11, 0), roll=7),
            TermEventEvent(id=13, fulfills=(12, 0), roll=5),
            AdvancementEvent(id=14, fulfills=(13, 0), roll=3),
            ReenlistEvent(id=15, fulfills=(14, 0), reenlist=False),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1

    def test_crime_still_creates_advancement_pending(self):
        projection = replay(1, self._setup_through_life_event_11())

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_crime_take_prisoner_forces_prisoner_career_choice(self):
        # choosing take-prisoner sets forced_next_career; after muster-out, only Prisoner is offered
        events = [
            *self._setup_through_life_event_11(),
            CareerChoiceEvent.for_choice(LifeEventCrimeTakePrisoner, id=8, fulfills=(7, 0)),
            AdvancementEvent(id=9, fulfills=(7, 1), roll=3),
            ReenlistEvent(id=10, fulfills=(9, 0), reenlist=False),
            MusterOutEvent(id=11, fulfills=(10, 0), table='benefits', roll=3),
        ]
        projection = replay(1, events)

        career_choice = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert career_choice is not None
        assert career_choice.options == ['Prisoner']


class TestAgentAssignmentTableFiltering:
    """Agent skill table options are filtered to the character's assignment (Core p.28)."""

    def _setup_in_term_2(self, assignment: str) -> list:
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Agent', assignment=assignment, qualification_roll=8),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),
            AdvancementEvent(id=7, fulfills=(6, 0), roll=9),
            ReenlistEvent(id=8, fulfills=(7, 0), reenlist=True),
        ]

    def test_intelligence_assignment_excludes_corporate_and_law_enforcement_tables(self):
        events = self._setup_in_term_2('Intelligence')
        projection = replay(1, events)

        skill_table_pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTable)), None)
        assert skill_table_pending is not None
        options = set(skill_table_pending.options)
        assert 'intelligence' in options
        assert 'corporate' not in options
        assert 'law enforcement' not in options

    def test_corporate_assignment_excludes_intelligence_and_law_enforcement_tables(self):
        events = self._setup_in_term_2('Corporate')
        projection = replay(1, events)

        skill_table_pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTable)), None)
        assert skill_table_pending is not None
        options = set(skill_table_pending.options)
        assert 'corporate' in options
        assert 'intelligence' not in options
        assert 'law enforcement' not in options

    def test_law_enforcement_assignment_excludes_intelligence_and_corporate_tables(self):
        events = self._setup_in_term_2('Law Enforcement')
        projection = replay(1, events)

        skill_table_pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTable)), None)
        assert skill_table_pending is not None
        options = set(skill_table_pending.options)
        assert 'law enforcement' in options
        assert 'intelligence' not in options
        assert 'corporate' not in options


# ── regression: no spurious survive after end-of-term skill-table choice ─────


class TestNoSpuriousSurviveAfterEndOfTermSkillTableChoice:
    """After advancement, skill table + reenlist/aging are queued together.
    If the skill table roll requires a sub-choice (Language, Science, etc.),
    fulfilling that choice must NOT add another PendingSurvive before the
    already-queued PendingReenlist/PendingAgingRoll."""

    def _through_advancement(self) -> list:
        # Scout/Courier: survive END 5+, advancement EDU 9+ (EDU=10, DM+1, roll 8 → 9 ≥ 9)
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # simple event, no extra effects
            AdvancementEvent(id=7, fulfills=(6, 0), roll=8),  # EDU 9+; EDU=10, DM+1 → 9 ≥ 9
        ]

    def test_no_survive_after_choice_path_advanced_edu_language(self):
        """Choosing Language from advanced_education must not produce a spurious survive."""
        events = [
            *self._through_advancement(),
            SkillTableEvent(id=8, fulfills=(7, 0), table='advanced_education', roll=2),  # Language → choice
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillTableChoice) for p in projection.pending_inputs)
        assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)

        # Fulfill the choice — still no spurious survive
        from ceres.character.skills import LanguageGalanglic

        events2 = [*events, SkillChoiceEvent(id=9, fulfills=(8, 0), skill=LanguageGalanglic())]
        projection2 = replay(1, events2)
        assert not any(isinstance(p, PendingSurvive) for p in projection2.pending_inputs)
        assert any(
            isinstance(p, (PendingAssignmentChangeChoice, PendingReenlist, PendingAgingRoll))
            for p in projection2.pending_inputs
        )

    def test_no_survive_after_no_choice_path_service_skills(self):
        """A non-choice skill table roll at end-of-term must also not add survive."""
        events = [
            *self._through_advancement(),
            SkillTableEvent(id=8, fulfills=(7, 0), table='service_skills', roll=1),  # Pilot — no choice
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)
        assert any(
            isinstance(p, (PendingAssignmentChangeChoice, PendingReenlist, PendingAgingRoll))
            for p in projection.pending_inputs
        )


class TestAssignmentChange:
    """Tests for the Changing Assignments rule: careers that allow intra-career assignment changes."""

    def _through_advancement(self, assignment: str = 'Courier') -> list:
        """Events through advancement for Scout (which allows assignment changes)."""
        return [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scout', assignment=assignment, qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills=(6, 0), roll=9),
        ]

    def _through_advancement_scholar(self, assignment: str = 'Field Researcher') -> list:
        """Events through advancement for Scholar (also allows assignment changes).

        Scholar rank 1 grants a Science skill choice (PendingRankBonusChoice), which must be
        resolved before the assignment-change pending is created.
        """
        return [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Scholar', assignment=assignment, qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills=(4, 0), skill=Drive()),
            SkillChoiceEvent(id=6, fulfills=(4, 1), skill=SpaceScience()),
            SurviveEvent(id=7, fulfills=(6, 0), roll=7),
            TermEventEvent(id=8, fulfills=(7, 0), roll=5),
            # INT 6+, INT=9 (DM+1), roll 6 → 6+1=7 >= 6 → success → rank 1 bonus
            AdvancementEvent(id=9, fulfills=(8, 0), roll=6),
            # Scholar rank 1 bonus: Science 1 (specialised) → PendingRankBonusChoice first
            SkillChoiceEvent(id=10, fulfills=(9, 0), skill=SpaceScience(astronomy=Level(value=1))),
        ]

    # ── pending options ────────────────────────────────────────────────────────

    def test_scout_courier_pending_options_include_all_assignments(self):
        """Scout Courier gets same + Surveyor + Explorer + muster_out."""
        projection = replay(1, self._through_advancement())

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice))
        assert set(pending.options) == {'same', 'Surveyor', 'Explorer', 'muster_out'}

    def test_scout_surveyor_pending_excludes_current_assignment(self):
        """Scout Surveyor gets same + Courier + Explorer + muster_out (not Surveyor in others)."""
        projection = replay(1, self._through_advancement(assignment='Surveyor'))

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice))
        assert 'Surveyor' not in pending.options
        assert 'Courier' in pending.options
        assert 'Explorer' in pending.options
        assert 'same' in pending.options
        assert 'muster_out' in pending.options

    def test_scholar_also_gets_assignment_change_pending(self):
        """Scholar also allows assignment changes."""
        projection = replay(1, self._through_advancement_scholar())

        assert any(isinstance(p, PendingAssignmentChangeChoice) for p in projection.pending_inputs)

    def test_agent_does_not_get_assignment_change_pending(self):
        """Agent (allows_assignment_change=false) creates PendingReenlist, not PendingAssignmentChangeChoice."""
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills=(3, 0), career='Agent', assignment='Intelligence', qualification_roll=7),
            SurviveEvent(id=5, fulfills=(4, 0), roll=7),
            TermEventEvent(id=6, fulfills=(5, 0), roll=3),  # generic event, no special effect
            AdvancementEvent(id=7, fulfills=(6, 0), roll=9),
        ]
        projection = replay(1, events)

        assert not any(isinstance(p, PendingAssignmentChangeChoice) for p in projection.pending_inputs)
        assert any(isinstance(p, PendingReenlist) for p in projection.pending_inputs)

    # ── successful assignment change ───────────────────────────────────────────

    def test_successful_change_updates_current_assignment(self):
        """A passing qualification roll changes current_assignment."""
        # Scout: INT 5+, INT=9 (DM+1), roll 5 → 5+1=6 >= 5 (success)
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.current_assignment == 'Surveyor'

    def test_successful_change_keeps_career(self):
        """Successful assignment change keeps character in the same career."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'

    def test_successful_change_starts_another_term(self):
        """Successful assignment change starts a new term."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.terms_started_in_current_career == 2

    def test_successful_change_creates_skill_table_pending(self):
        """After successful assignment change, a skill table choice is presented."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=5),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_successful_change_new_skill_table_options_include_new_assignment(self):
        """After changing to Surveyor, the skill table options include the surveyor table."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=5),
        ]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSkillTable))
        assert 'surveyor' in pending.options

    # ── failed assignment change ───────────────────────────────────────────────

    def test_failed_change_keeps_original_assignment(self):
        """A failing qualification roll leaves assignment unchanged."""
        # Scout: INT 5+, INT=9 (DM+1), roll 3 → 3+1=4 < 5 (fail)
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.current_assignment == 'Courier'

    def test_failed_change_creates_reenlist_pending(self):
        """Failed qualification for assignment change creates PendingReenlist (same or muster out)."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=3),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingReenlist) for p in projection.pending_inputs)

    def test_failed_change_reenlist_true_continues_same_assignment(self):
        """After failed change, choosing reenlist=True continues with original assignment."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=3),
            ReenlistEvent(id=9, fulfills=(8, 0), reenlist=True),
        ]
        projection = replay(1, events)

        assert projection.summary.current_assignment == 'Courier'
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_failed_change_reenlist_false_ends_career(self):
        """After failed change, choosing reenlist=False musters out."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor', qualification_roll=3),
            ReenlistEvent(id=9, fulfills=(8, 0), reenlist=False),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    # ── validation ─────────────────────────────────────────────────────────────

    def test_assignment_change_to_unknown_assignment_raises(self):
        """Attempting to change to a non-existent assignment raises ReplayError."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Admiral', qualification_roll=5),
        ]
        with pytest.raises(ReplayError):
            replay(1, events)

    def test_assignment_change_without_qual_roll_raises(self):
        """Providing an assignment name without a qualification_roll raises ReplayError."""
        events = [
            *self._through_advancement(),
            AssignmentChangeChoiceEvent(id=8, fulfills=(7, 0), choice='Surveyor'),
        ]
        with pytest.raises(ReplayError):
            replay(1, events)
