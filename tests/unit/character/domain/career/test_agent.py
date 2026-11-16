"""Tests for the Agent career — law enforcement, intelligence, and corporate assignments."""

import pytest

from ceres.character.domain.career import AGENT, ROGUE
from ceres.character.domain.career.agent import (
    AgentMishap2Accept,
    AgentMishap2Refuse,
    AgentMishap5Ally,
    AgentMishap5Contact,
    AgentMishap5Family,
    PendingAgentEvent3SkillRoll,
    PendingAgentEvent11SkillChoice,
    PendingAgentMishap3SkillRoll,
)
from ceres.character.domain.career.career_data import AdvancementDmOption
from ceres.character.domain.career.career_events import (
    AdvancementDmChoiceHandler,
    AdvancementHandler,
    CareerChoiceHandler,
    CareerEntryHandler,
    MishapHandler,
    MusterOutHandler,
    PendingAdvancement,
    PendingBenefitChoice,
    PendingCareerChoice,
    PendingChoices,
    PendingMishap,
    PendingMusterOut,
    PendingSkillChoice,
    PendingSurvive,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.character_start import BackgroundSkillsHandler, UcpHandler
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import (
    Enemy,
)
from ceres.character.domain.health.health_events import (
    PendingDoubleInjuryRoll,
    PendingInjuryTable,
)
from ceres.character.domain.skills import (
    Admin,
    Advocate,
    Athletics,
    Carouse,
    Deception,
    Drive,
    Flyer,
    Gambler,
    GunCombat,
    Investigate,
    JackOfAllTrades,
    Level,
    Medic,
    Persuade,
    Recon,
    Stealth,
    Streetwise,
    Tactics,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver, _creation_events


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — INT DM+1, END DM+0."""
    c = _creation_events(VILANI, MOCK_WORLD, 'NPC', 'Sven')
    ucp = Event(fulfills=(c[-1].id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(
        fulfills=(ucp.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    return [*c, ucp, background]


def _enter_agent(assignment: str = 'Law Enforcement', qual_roll: int = 5) -> list:
    """Events through qualification (qual_roll=5 → INT DM+1 → modified 6 ≥ 6, pass)."""
    base = _setup()
    entry = Event(
        fulfills=(base[-1].id, 0),
        handler=CareerEntryHandler(career=AGENT, assignment=AGENT.assignment(assignment), qualification_roll=qual_roll),
    )
    return [
        *base,
        entry,
    ]


def _through_survive(assignment: str = 'Law Enforcement', survive_roll: int = 6) -> list:
    """Through qualification and survival (survive_roll=6 → END 6+, pass)."""
    base = _enter_agent(assignment)
    return [
        *base,
        Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=survive_roll)),
    ]


def _through_term_event(assignment: str = 'Law Enforcement', event_roll: int = 10) -> list:
    """Through survive and term event (event_roll=10 → DM+2 advancement, no blocking pendings)."""
    base = _through_survive(assignment)
    return [
        *base,
        Event(fulfills=(base[-1].id, 0), handler=TermEventHandler(roll=event_roll)),
    ]


# ── qualification ─────────────────────────────────────────────────────────────


class TestAgentQualification:
    def test_success_enters_career(self):
        # INT 6+, INT=9 (DM+1), roll 5 → 6 ≥ 6
        projection = replay(1, _enter_agent())
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Agent'

    def test_failure_clears_career(self):
        # INT 6+, INT=9 (DM+1), roll 4 → 5 < 6
        projection = replay(1, _enter_agent(qual_roll=4))
        assert projection.summary.current_career is None

    def test_all_three_assignments_accepted(self):
        for assignment in ('Law Enforcement', 'Intelligence', 'Corporate'):
            projection = replay(1, _enter_agent(assignment=assignment))
            assert projection.summary.current_assignment is not None
            assert projection.summary.current_assignment.name == assignment

    def test_unknown_assignment_raises(self):
        from pydantic import ValidationError

        with pytest.raises((ValidationError, Exception)):
            _enter_agent(assignment='Shadow Ops')


# ── initial training (first term service skills) ──────────────────────────────


class TestAgentInitialTraining:
    def test_service_skills_granted_at_level_0(self):
        projection = replay(1, _enter_agent())
        for cls in (Streetwise, Drive, Investigate, Flyer, Recon, GunCombat):
            assert projection.summary.skill_level(cls) is not None, f'{cls.name()} not granted'

    def test_survive_pending_created(self):
        projection = replay(1, _enter_agent())
        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


# ── survival ──────────────────────────────────────────────────────────────────


class TestAgentSurvival:
    def test_law_enforcement_survival_end_6plus(self):
        # END=6 (DM+0), roll 6 → 6 ≥ 6, survive
        base = _enter_agent('Law Enforcement')
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=6))])
        assert any(p for p in projection.pending_inputs if not isinstance(p, PendingSurvive))

    def test_law_enforcement_survival_failure_creates_mishap_pending(self):
        # END=6 (DM+0), roll 5 → 5 < 6, mishap pending created
        base = _enter_agent('Law Enforcement')
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=5))])
        from ceres.character.domain.career.career_events import PendingMishap

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_law_enforcement_survival_failure_then_mishap_ejects(self):
        # After mishap 6 (injury), career ends
        base = _enter_agent('Law Enforcement')
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=5))
        projection = replay(
            1,
            [
                *base,
                survive,
                Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=6)),
            ],
        )
        assert projection.summary.current_career is None

    def test_intelligence_survival_int_7plus_pass(self):
        # INT=9 (DM+1), roll 6 → 7 ≥ 7, survive
        base = _enter_agent('Intelligence')
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=6))])
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Agent'

    def test_intelligence_survival_int_7plus_fail_creates_mishap_pending(self):
        # INT=9 (DM+1), roll 5 → 6 < 7, mishap pending
        base = _enter_agent('Intelligence')
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=5))])
        from ceres.character.domain.career.career_events import PendingMishap

        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_corporate_survival_int_5plus_pass(self):
        # INT=9 (DM+1), roll 4 → 5 ≥ 5, survive
        base = _enter_agent('Corporate')
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=4))])
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Agent'


class TestAgentDirectOutcomeRows:
    def _driver(self) -> CharacterDriver:
        return (
            CharacterDriver()
            .start(VILANI, MOCK_WORLD, name='Sven')
            .ucp('7869A5')
            .background_skills([Admin(), Athletics(), Carouse(), Drive()])
            .career('Agent', 'Law Enforcement', roll=5)
        )

    def test_mishap_4_gains_enemy_and_deception_1(self):
        projection = self._driver().survive(5).mishap(4).projection

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)
        assert projection.summary.skill_level(Deception) == 1
        assert projection.summary.current_career is None

    def test_event_4_adds_benefit_dm(self):
        projection = self._driver().survive(6).term_event(4).projection

        dms = projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms
        assert len(dms) == 1
        assert dms[0].amount == 1

    def test_event_9_adds_advancement_dm(self):
        projection = self._driver().survive(6).term_event(9).projection

        assert projection.pending_advancement_dm == 2


# ── rank tables ───────────────────────────────────────────────────────────────


class TestAgentRanks:
    def _advance_once(self, assignment: str, adv_roll: int = 7) -> CharacterProjection:
        base = _through_term_event(assignment)
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=AdvancementHandler(roll=adv_roll)),
        ]
        return replay(1, events)

    def test_law_enforcement_rank1_grants_streetwise(self):
        # INT advancement for Law Enforcement = INT 6+; INT=9 (DM+1), roll 5 → 6 ≥ 6
        projection = self._advance_once('Law Enforcement', adv_roll=5)
        assert projection.summary.rank == 1
        assert (projection.summary.skill_level(Streetwise) or 0) >= 1

    def test_intelligence_rank1_grants_deception(self):
        # INT advancement for Intelligence = INT 5+; INT=9 (DM+1), roll 4 → 5 ≥ 5
        projection = self._advance_once('Intelligence', adv_roll=4)
        assert projection.summary.rank == 1
        assert (projection.summary.skill_level(Deception) or 0) >= 1

    def test_corporate_rank1_grants_deception(self):
        # INT advancement for Corporate = INT 7+; INT=9 (DM+1), roll 6 → 7 ≥ 7
        projection = self._advance_once('Corporate', adv_roll=6)
        assert projection.summary.rank == 1
        assert (projection.summary.skill_level(Deception) or 0) >= 1


# ── event 3: dangerous investigation ─────────────────────────────────────────


class TestAgentEvent3:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=3)

    def test_creates_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingAgentEvent3SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [Investigate(), Streetwise()]

    def test_success_creates_skill_choice(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Investigate(), modified_roll=9)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [Deception(), JackOfAllTrades(), Persuade(), Tactics()]

    def test_success_creates_advancement_pending_after_skill_choice(self):
        base = self._setup_to_event()
        roll = Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Investigate(), modified_roll=9))
        events = [
            *base,
            roll,
            Event(fulfills=(roll.id, 0), handler=SkillChoiceHandler(skill=Deception())),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_failure_creates_mishap_pending(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Investigate(), modified_roll=6)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMishap) for p in projection.pending_inputs)

    def test_failure_mishap_does_not_eject(self):
        base = self._setup_to_event()
        roll = Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Investigate(), modified_roll=6))
        events = [
            *base,
            roll,
            Event(fulfills=(roll.id, 0), handler=MishapHandler(roll=6, stay_in_career=True)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Agent'


# ── event 6: advanced training ────────────────────────────────────────────────


class TestAgentEvent6:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=6)

    def test_creates_edu_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingAdvancedTrainingSkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == ['EDU']

    def test_success_creates_skill_choice_pending(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Chars.EDU, modified_roll=9)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Chars.EDU, modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 8: undercover mission ───────────────────────────────────────────────


def _agent_after_event(event_roll: int) -> CharacterDriver:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5. Law Enforcement: survival END 6+, advancement INT 6+ (INT DM+1)."""
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('7869A5')
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    d.career('Agent', 'Law Enforcement', roll=12)
    d.survive(9)
    d.term_event(event_roll)
    return d


def _undercover(cover: str, deception_roll: int) -> CharacterDriver:
    d = _agent_after_event(8)
    d.go_undercover(cover, deception_roll)
    return d


def _in_agent(d: CharacterDriver) -> bool:
    career = d.projection.summary.current_career
    return career is not None and career.name == 'Agent'


class TestAgentEvent8Undercover:
    """You go undercover to investigate an enemy. Roll Deception 8+.

    "If you succeed, roll immediately on the Rogue or Citizen Events table and
    make one roll on any Specialist skill table for that career. If you fail,
    roll immediately on the Rogue or Citizen Mishap table." Read as RIC-030.
    """

    def test_is_never_left_as_a_manual_problem(self):
        assert _undercover('Rogue', 8).projection.summary.problems == []
        assert _undercover('Rogue', 7).projection.summary.problems == []

    # ── failure: a mishap from the cover career ends the Agent career ──────

    def test_failure_applies_the_rogue_mishap_rolled(self):
        d = _undercover('Rogue', 7)
        d.mishap(5)  # Rogue: a detective or rival criminal vows to hunt you down. Gain an Enemy.
        assert [type(c) for c in d.projection.summary.connections] == [Enemy]

    def test_failure_applies_the_citizen_mishap_rolled(self):
        d = _undercover('Citizen', 7)
        d.mishap(3)  # Citizen: hard times cost you your job. Lose one SOC.
        assert d.projection.summary.characteristics[Chars.SOC] == 4

    def test_failure_ends_the_agent_career(self):
        d = _undercover('Rogue', 7)
        d.mishap(5)
        assert d.projection.summary.current_career is None

    def test_failure_loses_the_benefit_roll_of_the_term(self):
        d = _undercover('Rogue', 7)
        d.mishap(5)
        assert not d.has_muster_out_roll()  # one term served, its only Benefit roll lost

    def test_failure_with_rogue_mishap_2_sends_the_agent_to_prison(self):
        d = _undercover('Rogue', 7)
        d.mishap(2)  # Arrested. You must take the Prisoner career in your next term.
        assert [career.name for career in d.career_choice_options()] == ['Prisoner']

    # ── success: an event and a specialist skill roll from the cover career ─

    def test_success_applies_the_rogue_event_rolled(self):
        d = _undercover('Rogue', 8)
        d.term_event(10)  # Rogue: you are involved in a gambling ring. Gain Gambler 1.
        assert d.projection.summary.skill_level(Gambler) == 1

    def test_success_keeps_the_agent_career(self):
        d = _undercover('Rogue', 8)
        d.term_event(10)
        assert _in_agent(d)

    def test_success_offers_the_specialist_tables_of_the_rogue_career(self):
        d = _undercover('Rogue', 8)
        assert d.skill_table_labels() == ['Thief', 'Enforcer', 'Pirate']

    def test_success_offers_the_specialist_tables_of_the_citizen_career(self):
        d = _undercover('Citizen', 8)
        assert d.skill_table_labels() == ['Corporate', 'Worker', 'Colonist']

    def test_success_grants_the_specialist_skill_rolled(self):
        d = _undercover('Rogue', 8)
        d.term_event(10)
        d.skill_table('Thief', 1)  # Thief 1: Stealth
        assert d.projection.summary.skill_level(Stealth) == 1

    def test_borrowed_promotion_is_a_promotion_in_the_agent_career(self):
        d = _undercover('Citizen', 8)
        d.term_event(12)  # Citizen: you rise to a position of power. You are automatically promoted.
        assert _in_agent(d)
        assert d.projection.summary.rank == 1

    def test_borrowed_advancement_dm_applies_to_the_agent_advancement_roll(self):
        d = _undercover('Citizen', 8)
        d.term_event(9)  # Citizen: DM+2 to your next advancement roll.
        d.skill_table('Corporate', 2)  # Corporate 2: Admin
        d.advancement(3)  # INT 6+: 3 + 1 + 2 = 6
        assert d.projection.summary.rank == 1

    def test_borrowed_disaster_rolls_the_cover_careers_mishap_without_ejection(self):
        d = _undercover('Rogue', 8)
        d.term_event(2)  # Disaster! Roll on the Mishap table but you are not ejected from this career.
        d.mishap(5)  # Rogue mishap 5: gain an Enemy
        assert [type(c) for c in d.projection.summary.connections] == [Enemy]
        assert _in_agent(d)

    def test_the_term_goes_on_to_advancement_after_both_rolls(self):
        d = _undercover('Rogue', 8)
        d.term_event(10)
        d.skill_table('Thief', 1)
        d.advancement(5)  # INT 6+: 5 + 1 = 6
        assert d.projection.summary.rank == 1

    # ── what the player is told matches what happens ────────────────────────

    def test_cover_career_and_deception_roll_are_entered_in_one_form(self):
        d = _agent_after_event(8)
        assert d.next_instruction() == 'Choose a cover career and roll Deception 8+.'
        cover, roll = d.projection.pending_inputs[0].input_specs(d.projection)
        assert isinstance(cover, Select)
        assert [label for label, _ in cover.options] == ['Rogue', 'Citizen']
        assert isinstance(roll, NumberEntry)
        assert roll.label == 'Modified roll (2D + Deception level + DMs)'

    def test_the_mishap_roll_says_it_ends_the_agent_career(self):
        d = _undercover('Rogue', 7)
        assert d.next_instruction() == (
            'Your cover is blown: roll 1D on the Rogue Mishap table. '
            "This ends your Agent career and loses this term's Benefit roll."
        )

    def test_the_event_and_skill_rolls_name_the_cover_career(self):
        d = _undercover('Rogue', 8)
        assert d.next_instruction() == 'Undercover: roll 2D on the Rogue Events table'
        d.term_event(10)
        assert d.next_instruction() == 'Undercover: choose a Rogue specialist skill table and roll 1D'

    def test_a_borrowed_disaster_names_the_cover_careers_mishap_table(self):
        d = _undercover('Rogue', 8)
        d.term_event(2)
        assert d.next_instruction() == 'Roll 1D on the Rogue Mishap table (you are not ejected from your career)'

    def test_a_stored_roll_still_knows_whose_table_it_was_rolled_on(self):
        d = _undercover('Rogue', 7)
        stored = d.projection.pending_inputs[0].event_from_form({'roll': '5'}).model_dump_json()
        reloaded = Event.model_validate_json(stored).handler
        assert isinstance(reloaded, MishapHandler)
        assert reloaded.table_career == ROGUE

    # ── creation history ────────────────────────────────────────────────────

    # Agent event 8 introduces the cover career's own text; that text is not rewritten for the Agent.
    _STORY = 'Term 1 event (Agent): To investigate an enemy, you go undercover'

    def test_history_before_the_choice_tells_only_the_story(self):
        d = _agent_after_event(8)
        assert d.projection.creation_history[-1].startswith(f'{self._STORY}. In progress: ')

    def test_history_of_a_blown_cover(self):
        d = _undercover('Rogue', 7)
        d.mishap(5)
        d.name_connection('Inspector Vance')
        assert d.projection.creation_history[-1] == (
            f'{self._STORY} as a rogue: '
            'A police detective or rival criminal forces you to flee and vows to hunt you down. Career ended. '
            'Enemy: Inspector Vance.'
        )

    def test_a_betrayal_ends_the_agent_career_not_a_rogue_career(self):
        d = _undercover('Rogue', 7)
        d.mishap(3)
        d.betrayal_mishap('enemy', 7, name='Dana Okoye')
        history = d.projection.creation_history[-1]
        assert history.startswith(f'{self._STORY} as a rogue: Betrayed by a friend.')
        assert history.endswith('Gained Enemy Dana Okoye. Prison roll 7: no forced prison career. Career ended.')

    def test_history_of_a_successful_mission(self):
        d = _undercover('Citizen', 8)
        d.term_event(9)
        d.skill_table('Corporate', 2)
        assert d.projection.creation_history[-1] == (
            f'{self._STORY} as a citizen: You are rewarded for your diligence or cunning. Admin increased from 0 to 1.'
        )

    def test_history_of_a_choice_made_in_a_borrowed_event(self):
        from ceres.character.domain.career.rogue import RogueEvent6Refuse

        d = _undercover('Rogue', 8)
        d.term_event(6)
        d.career_choice(RogueEvent6Refuse)
        d.name_connection('Mara Voss')
        assert d.projection.creation_history[-1].startswith(
            f'{self._STORY} as a rogue: You have the opportunity to backstab a fellow rogue for personal gain. '
            'You refuse. Contact: Mara Voss.'
        )


class TestAgentEvent3FailedInvestigation:
    """ "If you fail, roll on the Mishap table." The event does not say the Agent stays, so they do not (RIC-030)."""

    def test_the_mishap_ends_the_agent_career(self):
        d = _agent_after_event(3)
        d.skill_roll(Investigate(), 7)
        d.mishap(4)  # Agent mishap 4: gain an Enemy and Deception 1
        assert d.projection.summary.current_career is None

    def test_the_mishap_roll_says_it_ends_the_agent_career(self):
        d = _agent_after_event(3)
        d.skill_roll(Investigate(), 7)
        assert d.next_instruction() == (
            'The investigation goes wrong: roll 1D on the Mishap table. '
            "This ends your Agent career and loses this term's Benefit roll."
        )


# ── event 11: senior agent mentor ─────────────────────────────────────────────


class TestAgentEvent11:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=11)

    def test_creates_career_skill_choice_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingAgentEvent11SkillChoice)),
            None,
        )
        assert pending is not None
        assert pending.options == [Investigate(), AdvancementDmOption()]

    def test_choose_investigate_grants_investigate_level_1(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillChoiceHandler(skill=Investigate(level=Level(value=1)))),
        ]
        projection = replay(1, events)
        assert (projection.summary.skill_level(Investigate) or 0) >= 1

    def test_choose_advancement_dm_creates_advancement_pending(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=AdvancementDmChoiceHandler()),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── mishap 1: severe injury or double roll ────────────────────────────────────


class TestAgentMishap1:
    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Agent', 'Law Enforcement', roll=5)
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}


# ── mishap 2: criminal deal ───────────────────────────────────────────────────


class TestAgentMishap2:
    def _setup_to_mishap(self) -> list:
        base = _enter_agent()
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=5))
        mishap = Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=2))
        return [
            *base,
            survive,
            mishap,
        ]

    def test_creates_accept_refuse_pending(self):
        projection = replay(1, self._setup_to_mishap())
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {AgentMishap2Accept, AgentMishap2Refuse}

    def test_accept_leaves_career_without_injury(self):
        base = self._setup_to_mishap()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=AgentMishap2Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_refuse_adds_enemy(self):
        base = self._setup_to_mishap()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=AgentMishap2Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_refuse_creates_double_injury_roll_pending(self):
        base = self._setup_to_mishap()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=AgentMishap2Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingDoubleInjuryRoll) for p in projection.pending_inputs)

    def test_refuse_creates_skill_choice_pending(self):
        base = self._setup_to_mishap()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=AgentMishap2Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)


# ── mishap 3: investigation gone wrong ────────────────────────────────────────


class TestAgentMishap3:
    def _setup_to_mishap(self) -> list:
        base = _enter_agent()
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=5))
        mishap = Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=3))
        return [
            *base,
            survive,
            mishap,
        ]

    def test_creates_advocate_skill_roll_pending(self):
        projection = replay(1, self._setup_to_mishap())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingAgentMishap3SkillRoll)),
            None,
        )
        assert pending is not None
        assert Advocate() in pending.options

    def test_success_keeps_benefit_roll(self):
        # term_count=1, rank=0 → roll_count=1; success → lose_current_term=False → 1 muster-out pending
        base = self._setup_to_mishap()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Medic(), modified_roll=8)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_failure_loses_benefit_roll(self):
        # term_count=1, rank=0 → roll_count=1; failure → lose_current_term=True → 0 muster-out pending
        base = self._setup_to_mishap()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Medic(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_both_outcomes_end_career(self):
        for roll in (8, 7):
            base = self._setup_to_mishap()
            events = [
                *base,
                Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Medic(), modified_roll=roll)),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None

    def test_roll_2_forces_prisoner_next(self):
        base = self._setup_to_mishap()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Medic(), modified_roll=2)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert [c.name for c in pending.options] == ['Prisoner']


# ── mishap 5: someone gets hurt ───────────────────────────────────────────────


class TestAgentMishap5:
    def _setup_to_mishap(self) -> list:
        base = _enter_agent()
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=5))
        mishap = Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=5))
        return [
            *base,
            survive,
            mishap,
        ]

    def test_creates_choice_pending_with_three_options(self):
        projection = replay(1, self._setup_to_mishap())
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {AgentMishap5Contact, AgentMishap5Ally, AgentMishap5Family}

    @pytest.mark.parametrize(
        ('choice_cls', 'keyword'),
        [
            (AgentMishap5Contact, 'contact'),
            (AgentMishap5Ally, 'ally'),
            (AgentMishap5Family, 'family'),
        ],
    )
    def test_choice_adds_problem_note(self, choice_cls, keyword):
        base = self._setup_to_mishap()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(keyword in p.lower() for p in projection.summary.problems)


# ── muster-out: choice benefit ────────────────────────────────────────────────


class TestAgentMusterOut:
    def _muster_out_setup(self) -> list:
        """Character through one term, then reenlist=False to trigger muster-out."""
        base = _through_term_event()
        advancement = Event(fulfills=(base[-1].id, 0), handler=AdvancementHandler(roll=3))
        leave = Event(fulfills=(advancement.id, 0), handler=ReenlistHandler(reenlist=False))
        return [*base, advancement, leave]

    def test_muster_out_row6_choice_benefit_creates_pending(self):
        base = self._muster_out_setup()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=MusterOutHandler(table='benefits', roll=6)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingBenefitChoice)), None)
        assert pending is not None
        labels = [b.display_label for b in pending.benefit_options]
        assert any('SOC' in lbl for lbl in labels)
        assert any('Cybernetic' in lbl for lbl in labels)
