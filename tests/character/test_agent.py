"""Tests for the Agent career — law enforcement, intelligence, and corporate assignments."""

import pytest

from ceres.character.characteristics import Chars
from ceres.character.events import (
    AdvancementEvent,
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    MusterOutEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.projection import (
    CharacterProjection,
    Enemy,
    PendingAdvancement,
    PendingBenefitChoice,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingDoubleInjuryRoll,
    PendingInjuryTable,
    PendingMishap,
    PendingMusterOut,
    PendingSkillChoice,
    PendingSurvive,
)
from ceres.character.replay import ReplayError, replay
from ceres.character.skills import (
    Admin,
    Athletics,
    Carouse,
    Deception,
    Drive,
    Investigate,
    Level,
    Medic,
)


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — INT DM+1, END DM+0."""
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Sven'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_agent(assignment: str = 'Law Enforcement', qual_roll: int = 5) -> list:
    """Events through qualification (qual_roll=5 → INT DM+1 → modified 6 ≥ 6, pass)."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Agent', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Law Enforcement', survive_roll: int = 6) -> list:
    """Through qualification and survival (survive_roll=6 → END 6+, pass)."""
    return [
        *_enter_agent(assignment),
        SurviveEvent(id=5, fulfills='4.0', roll=survive_roll),
    ]


def _through_term_event(assignment: str = 'Law Enforcement', event_roll: int = 5) -> list:
    """Through survive and term event (event_roll=5 → benefit_dm, simple effect, advances)."""
    return [
        *_through_survive(assignment),
        TermEventEvent(id=6, fulfills='5.0', roll=event_roll),
    ]


# ── qualification ─────────────────────────────────────────────────────────────


class TestAgentQualification:
    def test_success_enters_career(self):
        # INT 6+, INT=9 (DM+1), roll 5 → 6 ≥ 6
        projection = replay(1, _enter_agent())
        assert projection.summary.current_career == 'Agent'

    def test_failure_clears_career(self):
        # INT 6+, INT=9 (DM+1), roll 4 → 5 < 6
        projection = replay(1, _enter_agent(qual_roll=4))
        assert projection.summary.current_career is None

    def test_all_three_assignments_accepted(self):
        for assignment in ('Law Enforcement', 'Intelligence', 'Corporate'):
            projection = replay(1, _enter_agent(assignment=assignment))
            assert projection.summary.current_assignment == assignment

    def test_unknown_assignment_raises(self):
        with pytest.raises(ReplayError):
            replay(1, _enter_agent(assignment='Shadow Ops'))


# ── initial training (first term service skills) ──────────────────────────────


class TestAgentInitialTraining:
    def test_service_skills_granted_at_level_0(self):
        projection = replay(1, _enter_agent())
        for skill in ('Streetwise', 'Drive', 'Investigate', 'Flyer', 'Recon', 'Gun Combat'):
            assert projection.summary.skill_level(skill) is not None, f'{skill} not granted'

    def test_survive_pending_created(self):
        projection = replay(1, _enter_agent())
        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


# ── survival ──────────────────────────────────────────────────────────────────


class TestAgentSurvival:
    def test_law_enforcement_survival_end_6plus(self):
        # END=6 (DM+0), roll 6 → 6 ≥ 6, survive
        projection = replay(1, [*_enter_agent('Law Enforcement'), SurviveEvent(id=5, fulfills='4.0', roll=6)])
        assert any(p for p in projection.pending_inputs if not isinstance(p, PendingSurvive))

    def test_law_enforcement_survival_failure_creates_mishap_pending(self):
        # END=6 (DM+0), roll 5 → 5 < 6, mishap pending created
        projection = replay(1, [*_enter_agent('Law Enforcement'), SurviveEvent(id=5, fulfills='4.0', roll=5)])
        from ceres.character.projection import PendingMishap

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_law_enforcement_survival_failure_then_mishap_ejects(self):
        # After mishap 6 (injury), career ends
        projection = replay(
            1,
            [
                *_enter_agent('Law Enforcement'),
                SurviveEvent(id=5, fulfills='4.0', roll=5),
                MishapEvent(id=6, fulfills='5.0', roll=6),
            ],
        )
        assert projection.summary.current_career is None

    def test_intelligence_survival_int_7plus_pass(self):
        # INT=9 (DM+1), roll 6 → 7 ≥ 7, survive
        projection = replay(1, [*_enter_agent('Intelligence'), SurviveEvent(id=5, fulfills='4.0', roll=6)])
        assert projection.summary.current_career == 'Agent'

    def test_intelligence_survival_int_7plus_fail_creates_mishap_pending(self):
        # INT=9 (DM+1), roll 5 → 6 < 7, mishap pending
        projection = replay(1, [*_enter_agent('Intelligence'), SurviveEvent(id=5, fulfills='4.0', roll=5)])
        from ceres.character.projection import PendingMishap

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_corporate_survival_int_5plus_pass(self):
        # INT=9 (DM+1), roll 4 → 5 ≥ 5, survive
        projection = replay(1, [*_enter_agent('Corporate'), SurviveEvent(id=5, fulfills='4.0', roll=4)])
        assert projection.summary.current_career == 'Agent'


# ── rank tables ───────────────────────────────────────────────────────────────


class TestAgentRanks:
    def _advance_once(self, assignment: str, adv_roll: int = 7) -> CharacterProjection:
        events = [
            *_through_term_event(assignment),
            AdvancementEvent(id=7, fulfills='6.0', roll=adv_roll),
        ]
        return replay(1, events)

    def test_law_enforcement_rank1_grants_streetwise(self):
        # INT advancement for Law Enforcement = INT 6+; INT=9 (DM+1), roll 5 → 6 ≥ 6
        projection = self._advance_once('Law Enforcement', adv_roll=5)
        assert projection.summary.rank == 1
        assert (projection.summary.skill_level('Streetwise') or 0) >= 1

    def test_intelligence_rank1_grants_deception(self):
        # INT advancement for Intelligence = INT 5+; INT=9 (DM+1), roll 4 → 5 ≥ 5
        projection = self._advance_once('Intelligence', adv_roll=4)
        assert projection.summary.rank == 1
        assert (projection.summary.skill_level('Deception') or 0) >= 1

    def test_corporate_rank1_grants_deception(self):
        # INT advancement for Corporate = INT 7+; INT=9 (DM+1), roll 6 → 7 ≥ 7
        projection = self._advance_once('Corporate', adv_roll=6)
        assert projection.summary.rank == 1
        assert (projection.summary.skill_level('Deception') or 0) >= 1


# ── event 3: dangerous investigation ─────────────────────────────────────────


class TestAgentEvent3:
    def _setup_to_event(self) -> list:
        return [
            *_through_survive(),
            TermEventEvent(id=6, fulfills='5.0', roll=3),
        ]

    def test_creates_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 3),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'Investigate', 'Streetwise'}

    def test_success_creates_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_3', skill=Investigate(), modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert set(pending.options) == {'Deception', 'Jack-of-all-Trades', 'Persuade', 'Tactics'}

    def test_success_creates_advancement_pending_after_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_3', skill=Investigate(), modified_roll=9),
            SkillChoiceEvent(id=8, fulfills='7.0', skill=Deception()),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_failure_creates_mishap_pending(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_3', skill=Investigate(), modified_roll=6),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_failure_mishap_does_not_eject(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_3', skill=Investigate(), modified_roll=6),
            MishapEvent(id=8, fulfills='7.0', roll=6, stay_in_career=True),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career == 'Agent'


# ── event 6: advanced training ────────────────────────────────────────────────


class TestAgentEvent6:
    def _setup_to_event(self) -> list:
        return [
            *_through_survive(),
            TermEventEvent(id=6, fulfills='5.0', roll=6),
        ]

    def test_creates_edu_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 6),
            None,
        )
        assert pending is not None
        assert pending.options == ['EDU']

    def test_success_creates_skill_choice_pending(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_6', skill=Chars.EDU, modified_roll=9),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_6', skill=Chars.EDU, modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 8: undercover mission ───────────────────────────────────────────────


class TestAgentEvent8:
    def _setup_to_event(self) -> list:
        return [
            *_through_survive(),
            TermEventEvent(id=6, fulfills='5.0', roll=8),
        ]

    def test_creates_deception_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 8),
            None,
        )
        assert pending is not None
        assert pending.options == ['Deception']

    def test_success_adds_problem_about_cross_career_tables(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_8', skill=Deception(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert any('Rogue or Citizen' in p for p in projection.summary.problems)

    def test_failure_adds_problem_about_cross_career_mishap(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_8', skill=Deception(), modified_roll=6),
        ]
        projection = replay(1, events)
        assert any('Rogue or Citizen' in p for p in projection.summary.problems)

    def test_creates_advancement_pending_after_roll(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_event_8', skill=Deception(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 11: senior agent mentor ─────────────────────────────────────────────


class TestAgentEvent11:
    def _setup_to_event(self) -> list:
        return [
            *_through_survive(),
            TermEventEvent(id=6, fulfills='5.0', roll=11),
        ]

    def test_creates_career_skill_choice_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillChoice) and p.roll == 11),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'Investigate', 'advancement_dm_4'}

    def test_choose_investigate_grants_investigate_level_1(self):
        events = [
            *self._setup_to_event(),
            SkillChoiceEvent(id=7, fulfills='6.0', skill=Investigate(level=Level(value=1))),
        ]
        projection = replay(1, events)
        assert (projection.summary.skill_level('Investigate') or 0) >= 1

    def test_choose_advancement_dm_creates_advancement_pending(self):
        from ceres.character.events import AdvancementDmChoiceEvent

        events = [
            *self._setup_to_event(),
            AdvancementDmChoiceEvent(id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── mishap 2: criminal deal ───────────────────────────────────────────────────


class TestAgentMishap2:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_agent(),
            SurviveEvent(id=5, fulfills='4.0', roll=5),  # fail END 6+
            MishapEvent(id=6, fulfills='5.0', roll=2),
        ]

    def test_creates_accept_refuse_pending(self):
        projection = replay(1, self._setup_to_mishap())
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerMishap)), None)
        assert pending is not None
        assert set(pending.options) == {'accept', 'refuse'}

    def test_accept_leaves_career_without_injury(self):
        events = [
            *self._setup_to_mishap(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='agent_mishap_2', choice='accept'),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_refuse_adds_enemy(self):
        events = [
            *self._setup_to_mishap(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='agent_mishap_2', choice='refuse'),
        ]
        projection = replay(1, events)
        assert any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_refuse_creates_double_injury_roll_pending(self):
        events = [
            *self._setup_to_mishap(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='agent_mishap_2', choice='refuse'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingDoubleInjuryRoll) for p in projection.pending_inputs)

    def test_refuse_creates_skill_choice_pending(self):
        events = [
            *self._setup_to_mishap(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='agent_mishap_2', choice='refuse'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)


# ── mishap 3: investigation gone wrong ────────────────────────────────────────


class TestAgentMishap3:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_agent(),
            SurviveEvent(id=5, fulfills='4.0', roll=5),  # fail END 6+
            MishapEvent(id=6, fulfills='5.0', roll=3),
        ]

    def test_creates_advocate_skill_roll_pending(self):
        projection = replay(1, self._setup_to_mishap())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 3),
            None,
        )
        assert pending is not None
        assert 'Advocate' in pending.options

    def test_success_keeps_benefit_roll(self):
        # term_count=1, rank=0 → roll_count=1; success → lose_current_term=False → 1 muster-out pending
        events = [
            *self._setup_to_mishap(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_mishap_3', skill=Medic(), modified_roll=8),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_failure_loses_benefit_roll(self):
        # term_count=1, rank=0 → roll_count=1; failure → lose_current_term=True → 0 muster-out pending
        events = [
            *self._setup_to_mishap(),
            SkillRollEvent(id=7, fulfills='6.0', context='agent_mishap_3', skill=Medic(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_both_outcomes_end_career(self):
        for roll in (8, 7):
            events = [
                *self._setup_to_mishap(),
                SkillRollEvent(id=7, fulfills='6.0', context='agent_mishap_3', skill=Medic(), modified_roll=roll),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None


# ── mishap 5: someone gets hurt ───────────────────────────────────────────────


class TestAgentMishap5:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_agent(),
            SurviveEvent(id=5, fulfills='4.0', roll=5),
            MishapEvent(id=6, fulfills='5.0', roll=5),
        ]

    def test_creates_choice_pending_with_three_options(self):
        projection = replay(1, self._setup_to_mishap())
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerMishap)), None)
        assert pending is not None
        assert set(pending.options) == {'contact', 'ally', 'family'}

    @pytest.mark.parametrize('choice', ['contact', 'ally', 'family'])
    def test_choice_adds_problem_note(self, choice):
        events = [
            *self._setup_to_mishap(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='agent_mishap_5', choice=choice),
        ]
        projection = replay(1, events)
        assert any(choice in p.lower() for p in projection.summary.problems)


# ── muster-out: choice benefit ────────────────────────────────────────────────


class TestAgentMusterOut:
    def _muster_out_setup(self) -> list:
        """Character through one term, then reenlist=False to trigger muster-out."""
        from ceres.character.events import ReenlistEvent

        return [
            *_through_term_event(),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),  # fail INT 6+; just get skill table
            SkillTableEvent(id=8, fulfills='7.0', table='service_skills', roll=3),  # Investigate
            ReenlistEvent(id=9, fulfills='8.0', reenlist=False),
        ]

    def test_muster_out_row6_choice_benefit_creates_pending(self):
        events = [
            *self._muster_out_setup(),
            MusterOutEvent(id=10, fulfills='9.0', table='benefits', roll=6),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingBenefitChoice)), None)
        assert pending is not None
        labels = pending.options
        assert any('SOC' in lbl for lbl in labels)
        assert any('Cybernetic' in lbl for lbl in labels)
