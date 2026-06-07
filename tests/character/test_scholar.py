"""Tests for Scholar career events, mishaps, qualification, and rank bonuses."""

from ceres.character.domain.career import SCHOLAR, SCOUT
from ceres.character.domain.career.career_data import AdvancementDmOption
from ceres.character.domain.career.career_events import (
    AdvancementDmChoiceHandler,
    AdvancementHandler,
    CareerChoiceHandler,
    CareerEntryHandler,
    CharacteristicChoiceHandler,
    MishapHandler,
    MusterOutHandler,
    PendingAdvancement,
    PendingChoices,
    PendingConnectionsRoll,
    PendingInitialTrainingChoice,
    PendingRankBonusChoice,
    PendingSkillChoice,
    PendingSkillTableChoice,
    PendingSurvive,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillRollHandler,
    SkillTableHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.scholar import (
    PendingScholarEvent6SkillRoll,
    PendingScholarEvent11,
    PendingScholarScienceChoice,
    PendingScholarScienceChoicePreCreated,
    ScholarEvent3Accept,
    ScholarEvent3Decline,
    ScholarEvent8Accept,
    ScholarEvent8Refuse,
    ScholarEvent8SkillRoll,
    ScholarMishap3Openly,
    ScholarMishap3Secretly,
    ScholarMishap5GiveUp,
    ScholarMishap5StartAgain,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import (
    Ally,
    Enemy,
    Rival,
)
from ceres.character.domain.health.health_events import (
    InjuryTableHandler,
    PendingCharacteristicChoice,
    PendingInjuryTable,
    PendingNearlyKilled,
)
from ceres.character.domain.skills import (
    Admin,
    Advocate,
    Athletics,
    Carouse,
    CreativeArt,
    Deception,
    Diplomat,
    Drive,
    Electronics,
    Engineer,
    Flyer,
    Investigate,
    Level,
    LifeScience,
    Medic,
    Navigation,
    PerformingArt,
    Persuade,
    PhysicalScience,
    PresentationArt,
    RoboticScience,
    Sciences,
    SocialScience,
    SpaceScience,
    Survival,
    _skill_classes,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.pending_input import ChoiceBase
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD

_SCIENCES = sorted(['Life Science', 'Physical Science', 'Robotic Science', 'Social Science', 'Space Science'])
_SCIENCE_CLASSES = set(_skill_classes(Sciences))


def _scholar_setup(character_id: int = 1) -> list:
    """Like _full_setup() but with Medic instead of Drive.

    Scholar service_skills row 1 offers Drive/Flyer. Using Drive in background causes Flyer to be
    auto-granted (only 1 option left). This setup preserves both options so Scholar initial training
    creates two choice pendings: Drive/Flyer (id .0) and Science (id .1).
    """
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Medic()])
        ),
    ]


class TestScholarInitialTraining:
    """Scholar service_skills roll 1 (Drive/Flyer) and roll 6 (Science) require a player choice."""

    def _setup(self) -> list:
        return [
            Event(
                id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')
            ),
            Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
            # Background skills without Drive/Flyer/Science so choice tests are unambiguous
            Event(
                id=3,
                fulfills=(2, 0),
                handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Medic()]),
            ),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
        ]

    def test_two_initial_training_choice_pendings_created(self):
        projection = replay(1, self._setup())

        choice_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice)]
        assert len(choice_pendings) == 2

    def test_drive_flyer_choice_pending_has_correct_options(self):
        projection = replay(1, self._setup())

        pending = next(
            (
                p
                for p in projection.pending_inputs
                if isinstance(p, PendingInitialTrainingChoice) and Drive() in p.options
            ),
            None,
        )
        assert pending is not None
        assert {type(s) for s in pending.options} == {Drive, Flyer}

    def test_science_choice_pending_has_correct_options(self):
        projection = replay(1, self._setup())

        pending = next(
            (
                p
                for p in projection.pending_inputs
                if isinstance(p, PendingInitialTrainingChoice) and LifeScience() in p.options
            ),
            None,
        )
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES

    def test_drive_not_granted_before_choice(self):
        projection = replay(1, self._setup())
        assert projection.summary.skill_level(Drive) is None

    def test_science_not_granted_before_choice(self):
        projection = replay(1, self._setup())
        assert projection.summary.skill_level(LifeScience) is None

    def test_survive_not_pending_before_choices_resolved(self):
        projection = replay(1, self._setup())
        assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)

    def test_drive_choice_grants_drive_at_level_0(self):
        events = [*self._setup(), Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive()))]
        projection = replay(1, events)

        assert projection.summary.skill_level(Drive) == 0

    def test_survive_pending_appears_after_both_choices_resolved(self):
        events = [
            *self._setup(),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)

    def test_survive_pending_id_from_last_choice_event(self):
        events = [
            *self._setup(),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
        ]
        projection = replay(1, events)

        survive = next(p for p in projection.pending_inputs if isinstance(p, PendingSurvive))
        assert survive.id == '6.0'

    def test_no_initial_training_choice_for_scout(self):
        events = [
            Event(
                id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')
            ),
            Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
            Event(
                id=3,
                fulfills=(2, 0),
                handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Medic()]),
            ),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)

        assert not any(isinstance(p, PendingInitialTrainingChoice) for p in projection.pending_inputs)


class TestScholarTerm:
    """Basic Scholar Field Researcher term: survival, events, advancement, reenlist."""

    def _setup_with_scholar(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
        ]

    def test_survive_pending_is_end_6(self):
        projection = replay(1, self._setup_with_scholar())

        survive_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSurvive))
        assert 'END' in survive_pending.instruction and '6' in survive_pending.instruction

    def test_advancement_pending_is_int_6(self):
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),  # benefit_dm → direct advancement
        ]
        projection = replay(1, events)

        adv_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingAdvancement))
        assert 'INT' in adv_pending.instruction and '6' in adv_pending.instruction

    def test_rank_1_bonus_creates_science_choice_pending(self):
        # Rank 1 bonus is Science 1 (player chooses which broad science) — Core p.43
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),  # benefit_dm → direct advancement
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=7)),  # INT=9 DM+1 → 8 >= 6
        ]
        projection = replay(1, events)

        pending = next(
            (
                p
                for p in projection.pending_inputs
                if isinstance(p, PendingRankBonusChoice) and {type(s) for s in p.options} == _SCIENCE_CLASSES
            ),
            None,
        )
        assert pending is not None

    def test_event_4_skill_choice_options(self):
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=4)),
        ]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice))
        # Core event 4: one of Medic, Science, Engineer, Electronics, Investigate — Science = any broad science
        assert pending.options == [
            Medic(),
            LifeScience(),
            PhysicalScience(),
            RoboticScience(),
            SocialScience(),
            SpaceScience(),
            Engineer(),
            Electronics(),
            Investigate(),
        ]

    def test_event_9_stores_advancement_dm(self):
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=9)),
        ]
        projection = replay(1, events)

        assert projection.pending_advancement_dm == 2

    def test_event_9_still_creates_advancement_pending(self):
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=9)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_event_10_skill_choice_options(self):
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=10)),
        ]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice))
        assert pending.options == [Admin(), Advocate(), Persuade(), Diplomat()]

    def test_event_11_gains_ally_and_creates_scholar_event_11_pending(self):
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=11)),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Ally) for c in projection.summary.connections)
        assert any(isinstance(p, PendingScholarEvent11) for p in projection.pending_inputs)

    def test_mishap_4_grants_skill_choice_before_ejection(self):
        # Scholar mishap 4: skill_choice [Survival, Athletics], character still leaves career
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=3)),  # fail
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=4)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [Survival(), Athletics()]

    def test_mishap_4_skill_choice_grants_skill_and_no_advancement_pending(self):
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=3)),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=4)),
            Event(id=9, fulfills=(8, 0), handler=SkillChoiceHandler(skill=Survival(level=Level(value=1)))),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Survival, -1) >= 1
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_scholar_mishap_6_stays_in_career_and_gains_rival(self):
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=3)),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=6)),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scholar'
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        assert any(isinstance(c, Rival) for c in projection.summary.connections)

    def test_scholar_mishap_6_stays_even_without_explicit_flag(self):
        # MishapEntry.stay_in_career overrides player's default stay_in_career=False
        events = [
            *self._setup_with_scholar(),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=3)),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=6, stay_in_career=False)),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scholar'


class TestScholarEvent6:
    """Scholar event 6: roll EDU 8+ to gain any one skill at level 1."""

    def _setup_to_event_6(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=6)),
        ]

    def test_creates_scholar_event_6_pending(self):
        projection = replay(1, self._setup_to_event_6())

        assert any(isinstance(p, PendingScholarEvent6SkillRoll) for p in projection.pending_inputs)

    def test_success_creates_skill_choice_pending(self):
        # EDU=10 (DM+1), need 8+, modified_roll=8 → success
        events = [
            *self._setup_to_event_6(),
            Event(id=9, fulfills=(8, 0), handler=SkillRollHandler(skill=Chars.EDU, modified_roll=8)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_creates_advancement_pending_not_skill_choice(self):
        # modified_roll=5 < 8 → failure
        events = [
            *self._setup_to_event_6(),
            Event(id=9, fulfills=(8, 0), handler=SkillRollHandler(skill=Chars.EDU, modified_roll=5)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_success_skill_choice_grants_skill_at_level_1(self):
        events = [
            *self._setup_to_event_6(),
            Event(id=9, fulfills=(8, 0), handler=SkillRollHandler(skill=Chars.EDU, modified_roll=8)),
            Event(id=10, fulfills=(9, 0), handler=SkillChoiceHandler(skill=Navigation(level=Level(value=1)))),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(Navigation, -1) >= 1

    def test_success_skill_choice_creates_advancement_pending(self):
        events = [
            *self._setup_to_event_6(),
            Event(id=9, fulfills=(8, 0), handler=SkillRollHandler(skill=Chars.EDU, modified_roll=8)),
            Event(id=10, fulfills=(9, 0), handler=SkillChoiceHandler(skill=Navigation(level=Level(value=1)))),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestScholarMishap3:
    """Mishap 3: planetary government interference. Player chooses openly or secretly. Career continues."""

    def _setup(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=3)),  # fail
        ]

    def test_creates_choice_pending_openly_or_secretly(self):
        events = [*self._setup(), Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=3))]
        projection = replay(1, events)

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {ScholarMishap3Openly, ScholarMishap3Secretly}

    def test_stays_in_career_before_choice(self):
        events = [*self._setup(), Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=3))]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scholar'

    def test_openly_adds_enemy_and_creates_science_pending(self):
        events = [
            *self._setup(),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=3)),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarMishap3Openly.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        # Core mishap 3: increase Science — any broad science — so a science choice pending is required
        assert any(isinstance(c, Enemy) for c in projection.summary.connections)
        science_pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingScholarScienceChoice)),
            None,
        )
        assert science_pending is not None
        assert science_pending.options == [
            LifeScience(),
            PhysicalScience(),
            RoboticScience(),
            SocialScience(),
            SpaceScience(),
        ]

    def test_secretly_creates_science_pending_and_decreases_soc(self):
        events = [
            *self._setup(),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=3)),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarMishap3Secretly.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        # Core mishap 3 secretly: Science +1 (any), SOC -2, no enemy
        assert any(isinstance(p, PendingScholarScienceChoice) for p in projection.pending_inputs)
        # SOC was 5 from UCP '7869A5'
        assert projection.summary.characteristics[Chars.SOC] == 3
        assert not any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_choice_creates_advancement_pending(self):
        events = [
            *self._setup(),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=3)),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarMishap3Openly.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestScholarMishap5:
    """Mishap 5: work sabotaged. Give up (leave) or start again (stay, lose benefit rolls)."""

    def _setup(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=3)),  # fail
        ]

    def test_creates_give_up_or_start_again_pending(self):
        events = [*self._setup(), Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=5))]
        projection = replay(1, events)

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {ScholarMishap5GiveUp, ScholarMishap5StartAgain}

    def test_give_up_ends_career(self):
        events = [
            *self._setup(),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=5)),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarMishap5GiveUp.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_give_up_increments_age_by_4(self):
        events = [
            *self._setup(),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=5)),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarMishap5GiveUp.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 22

    def test_start_again_stays_in_career(self):
        events = [
            *self._setup(),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=5)),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarMishap5StartAgain.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scholar'

    def test_start_again_creates_advancement_pending(self):
        events = [
            *self._setup(),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=5)),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarMishap5StartAgain.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_give_up_at_age_30_creates_aging_roll(self):
        from types import SimpleNamespace

        from ceres.character.domain.career.loader import load_careers
        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
        from ceres.character.domain.health.health_events import PendingAgingRoll

        scholar = load_careers()['Scholar']
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(
                name='Test',
                sophont=VILANI,
                homeworld=MOCK_WORLD,
                age=30,
                current_career=scholar,
                rank=1,
            ),
        )
        proj.pending_inputs.append(PendingAdvancement(pending_id=(99, 0), instruction='Advance'))

        ScholarMishap5GiveUp().handle(proj, SimpleNamespace(id=9))

        assert proj.summary.age == 34
        assert proj.summary.current_career is None
        assert not any(isinstance(p, PendingAdvancement) for p in proj.pending_inputs)
        assert any(isinstance(p, PendingAgingRoll) for p in proj.pending_inputs)


class TestScholarEvent3:
    """Event 3: research against conscience. Accept (2 Sciences, D3 Enemies) or Decline (nothing)."""

    def _setup(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=3)),
        ]

    def test_creates_accept_decline_pending(self):
        projection = replay(1, self._setup())

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {ScholarEvent3Accept, ScholarEvent3Decline}

    def test_decline_creates_advancement_pending(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent3Decline.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_connections_roll_pending_for_d3_enemies(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent3Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        conn = next((p for p in projection.pending_inputs if isinstance(p, PendingConnectionsRoll)), None)
        assert conn is not None
        assert conn.options == [1, 2, 3]

    def test_accept_creates_two_science_choice_pendings(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent3Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        sciences = [p for p in projection.pending_inputs if isinstance(p, PendingScholarScienceChoicePreCreated)]
        assert len(sciences) == 2

    def test_accept_science_choice_options_contain_sciences(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent3Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingScholarScienceChoicePreCreated))
        assert SpaceScience() in pending.options
        assert LifeScience() in pending.options

    def test_accept_resolving_science_choices_grants_skills(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent3Accept.model_fields['kind'].default),
            ),
            Event(id=10, fulfills=(9, 1), handler=SkillChoiceHandler(skill=SpaceScience(planetology=Level(value=1)))),
            Event(id=11, fulfills=(9, 2), handler=SkillChoiceHandler(skill=LifeScience(biology=Level(value=1)))),
        ]
        projection = replay(1, events)

        assert projection.summary.skill_level(SpaceScience, -1) >= 1
        assert projection.summary.skill_level(LifeScience, -1) >= 1

    def test_accept_creates_advancement_pending(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent3Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestScholarEvent8:
    """Event 8: opportunity to cheat. Refuse (nothing) or Accept (Deception/Admin 8+)."""

    def _setup(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=8)),
        ]

    def test_creates_accept_refuse_pending(self):
        projection = replay(1, self._setup())

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {ScholarEvent8Accept, ScholarEvent8Refuse}

    def test_refuse_creates_advancement_pending(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent8Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_skill_roll_pending_with_deception_admin(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent8Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, ScholarEvent8SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [Deception(), Admin()]

    def test_accept_success_gains_enemy(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent8Accept.model_fields['kind'].default),
            ),
            Event(id=10, fulfills=(9, 0), handler=SkillRollHandler(skill=Deception(), modified_roll=9)),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_accept_success_creates_skill_choice_pending(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent8Accept.model_fields['kind'].default),
            ),
            Event(id=10, fulfills=(9, 0), handler=SkillRollHandler(skill=Deception(), modified_roll=9)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_accept_failure_gains_enemy(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent8Accept.model_fields['kind'].default),
            ),
            Event(id=10, fulfills=(9, 0), handler=SkillRollHandler(skill=Deception(), modified_roll=5)),
        ]
        projection = replay(1, events)

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)

    def test_accept_failure_creates_advancement_pending(self):
        events = [
            *self._setup(),
            Event(
                id=9,
                fulfills=(8, 0),
                handler=CareerChoiceHandler(choice=ScholarEvent8Accept.model_fields['kind'].default),
            ),
            Event(id=10, fulfills=(9, 0), handler=SkillRollHandler(skill=Deception(), modified_roll=5)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestScholarEvent11:
    """Event 11: brilliant mentor (Ally already handled). Space Science +1 OR DM+4 to advancement."""

    def _setup(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=11)),
        ]

    def test_gains_ally_unconditionally(self):
        projection = replay(1, self._setup())

        assert any(isinstance(c, Ally) for c in projection.summary.connections)

    def test_creates_scholar_event_11_pending(self):
        projection = replay(1, self._setup())

        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingScholarEvent11)),
            None,
        )
        assert pending is not None
        # Core event 11: increase Science by one level — any broad science — or DM+4 advancement
        assert pending.options == [
            LifeScience(),
            PhysicalScience(),
            RoboticScience(),
            SocialScience(),
            SpaceScience(),
            AdvancementDmOption(),
        ]

    def test_choose_space_science_grants_space_science_1(self):
        sci_choice = Event(
            id=9, fulfills=(8, 0), handler=SkillChoiceHandler(skill=SpaceScience(planetology=Level(value=1)))
        )
        events = [*self._setup(), sci_choice]
        projection = replay(1, events)

        assert projection.summary.skill_level(SpaceScience, -1) >= 1

    def test_choose_advancement_dm_adds_pending_advancement_dm(self):
        events = [*self._setup(), Event(id=9, fulfills=(8, 0), handler=AdvancementDmChoiceHandler())]
        projection = replay(1, events)

        assert projection.pending_advancement_dm == 4

    def test_skill_choice_creates_advancement_pending(self):
        events = [
            *self._setup(),
            Event(id=9, fulfills=(8, 0), handler=SkillChoiceHandler(skill=LifeScience(biology=Level(value=1)))),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_advancement_dm_choice_creates_advancement_pending(self):
        events = [*self._setup(), Event(id=9, fulfills=(8, 0), handler=AdvancementDmChoiceHandler())]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class TestFromTableInjury:
    """Scholar mishap 2: injury roll on the Injury table (1D). All six outcomes."""

    def _setup_to_mishap_2(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=3)),  # fail
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=2)),  # Scholar mishap 2: from_table injury + rival
        ]

    def test_creates_injury_table_pending(self):
        projection = replay(1, self._setup_to_mishap_2())

        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_gains_rival_immediately(self):
        projection = replay(1, self._setup_to_mishap_2())

        assert any(isinstance(c, Rival) for c in projection.summary.connections)

    def test_roll_6_lightly_injured_no_characteristic_change(self):
        events = [
            *self._setup_to_mishap_2(),
            Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=6)),
        ]
        projection = replay(1, events)

        # All characteristics unchanged from UCP '7869A5'
        assert projection.summary.characteristics[Chars.STR] == 7
        assert projection.summary.characteristics[Chars.DEX] == 8
        assert projection.summary.characteristics[Chars.END] == 6
        assert not any(isinstance(p, PendingCharacteristicChoice) for p in projection.pending_inputs)

    def test_roll_5_creates_characteristic_choice_reduce_by_1(self):
        events = [*self._setup_to_mishap_2(), Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=5))]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice)), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}
        assert '1' in choice.instruction

    def test_roll_5_choice_reduces_by_1(self):
        events = [
            *self._setup_to_mishap_2(),
            Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=5)),
            Event(id=10, fulfills=(9, 0), handler=CharacteristicChoiceHandler(characteristic=Chars.END, amount=1)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.END] == 5  # 6 - 1

    def test_roll_4_creates_characteristic_choice_reduce_by_2(self):
        events = [*self._setup_to_mishap_2(), Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=4))]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice)), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}
        assert '2' in choice.instruction

    def test_roll_4_choice_reduces_by_2(self):
        events = [
            *self._setup_to_mishap_2(),
            Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=4)),
            Event(id=10, fulfills=(9, 0), handler=CharacteristicChoiceHandler(characteristic=Chars.STR, amount=2)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.STR] == 5  # 7 - 2

    def test_roll_3_options_are_str_and_dex_only(self):
        events = [*self._setup_to_mishap_2(), Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=3))]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice)), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX'}

    def test_roll_3_choice_reduces_by_2(self):
        events = [
            *self._setup_to_mishap_2(),
            Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=3)),
            Event(id=10, fulfills=(9, 0), handler=CharacteristicChoiceHandler(characteristic=Chars.DEX, amount=2)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.DEX] == 6  # 8 - 2

    def test_roll_2_creates_characteristic_choice_for_1d_reduction(self):
        events = [*self._setup_to_mishap_2(), Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=2))]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice)), None)
        assert choice is not None
        assert set(choice.options) == {'STR', 'DEX', 'END'}

    def test_roll_2_choice_reduces_by_player_supplied_amount(self):
        # Player rolled 1D=4 for the reduction
        events = [
            *self._setup_to_mishap_2(),
            Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=2)),
            Event(id=10, fulfills=(9, 0), handler=CharacteristicChoiceHandler(characteristic=Chars.DEX, amount=4)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.DEX] == 4  # 8 - 4
        # Other physical stats unchanged
        assert projection.summary.characteristics[Chars.STR] == 7
        assert projection.summary.characteristics[Chars.END] == 6

    def test_roll_1_creates_nearly_killed_pending(self):
        events = [*self._setup_to_mishap_2(), Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=1))]
        projection = replay(1, events)

        choice = next((p for p in projection.pending_inputs if isinstance(p, PendingNearlyKilled)), None)
        assert choice is not None

    def test_roll_1_choice_reduces_chosen_by_player_amount_and_others_by_2(self):
        # Player rolled 1D=3 for the chosen stat (DEX); STR and END auto-reduced by 2
        events = [
            *self._setup_to_mishap_2(),
            Event(id=9, fulfills=(8, 0), handler=InjuryTableHandler(roll=1)),
            Event(id=10, fulfills=(9, 0), handler=CharacteristicChoiceHandler(characteristic=Chars.DEX, amount=3)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.DEX] == 5  # 8 - 3
        assert projection.summary.characteristics[Chars.STR] == 5  # 7 - 2 (auto)
        assert projection.summary.characteristics[Chars.END] == 4  # 6 - 2 (auto)


class TestScholarQualificationInt:
    """Scholar uses INT 6+ for qualification, not EDU (Core p.42)."""

    def test_qualifies_using_int_dm(self):
        # UCP '786965': STR=7 DEX=8 END=6 INT=9 EDU=6 SOC=5
        # INT=9 → DM+1; EDU=6 → DM+0; target 6; roll 5 → 5+1=6 ≥ 6 with INT, 5+0=5 < 6 with EDU
        events = [
            Event(
                id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')
            ),
            Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='786965')),
            Event(id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse()])),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scholar'

    def test_fails_when_int_is_low(self):
        # UCP '786695': STR=7 DEX=8 END=6 INT=6 EDU=9 SOC=5
        # INT=6 → DM+0; EDU=9 → DM+1; target 6; roll 5 → 5+0=5 < 6 → fails
        events = [
            Event(
                id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')
            ),
            Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='786695')),
            Event(
                id=3,
                fulfills=(2, 0),
                handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
            ),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None


class TestScholarLabShip:
    """Scholar muster out rows 6-7 give lab_ship (Core p.42), not scout_ship."""

    def _setup_through_reenlist_false_scholar(self) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=3)),
            Event(id=10, fulfills=(9, 0), handler=ReenlistHandler(reenlist=False)),
        ]

    def test_benefits_roll_6_gives_lab_ship(self):
        events = [
            *self._setup_through_reenlist_false_scholar(),
            Event(id=11, fulfills=(10, 0), handler=MusterOutHandler(table='benefits', roll=6)),
        ]
        projection = replay(1, events)

        assert any(b.key == 'lab_ship' for b in projection.summary.benefits)

    def test_benefits_roll_7_gives_lab_ship(self):
        # Row 7 (capped at 7 in table) also gives lab_ship
        events = [
            *self._setup_through_reenlist_false_scholar(),
            Event(id=11, fulfills=(10, 0), handler=MusterOutHandler(table='benefits', roll=6)),
        ]
        projection = replay(1, events)

        assert any(b.key == 'lab_ship' for b in projection.summary.benefits)
        assert not any(b.key == 'scout_ship' for b in projection.summary.benefits)


class TestScholarScienceChoicesInTables:
    """Scholar skill table entries that are 'Science' offer all broad sciences (Core p.43)."""

    def _setup_in_term_2(self, assignment: str = 'Field Researcher') -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment(assignment), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=3)),
            Event(id=10, fulfills=(9, 0), handler=ReenlistHandler(reenlist=True)),
        ]

    def test_service_skills_roll_6_creates_science_choice(self):
        events = [
            *self._setup_in_term_2(),
            Event(id=11, fulfills=(10, 0), handler=SkillTableHandler(table='service_skills', roll=6)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES

    def test_advanced_education_roll_6_creates_science_choice(self):
        # EDU=10 ≥ 10 → can access Scholar advanced_education table
        events = [
            *self._setup_in_term_2(),
            Event(id=11, fulfills=(10, 0), handler=SkillTableHandler(table='advanced_education', roll=6)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES

    def test_advanced_education_roll_1_creates_art_choice(self):
        # Core advanced_education row 1: Art (any broad art type)
        events = [
            *self._setup_in_term_2(),
            Event(id=11, fulfills=(10, 0), handler=SkillTableHandler(table='advanced_education', roll=1)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == {PerformingArt, CreativeArt, PresentationArt}

    def test_field_researcher_roll_6_creates_science_choice(self):
        events = [
            *self._setup_in_term_2('Field Researcher'),
            Event(id=11, fulfills=(10, 0), handler=SkillTableHandler(table='assignment1', roll=6)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES

    def test_scientist_roll_3_creates_science_choice(self):
        events = [
            *self._setup_in_term_2('Scientist'),
            Event(id=11, fulfills=(10, 0), handler=SkillTableHandler(table='assignment2', roll=3)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES

    def test_physician_roll_6_creates_science_choice(self):
        events = [
            *self._setup_in_term_2('Physician'),
            Event(id=11, fulfills=(10, 0), handler=SkillTableHandler(table='assignment3', roll=6)),
        ]
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillTableChoice)), None)
        assert pending is not None
        assert {type(s) for s in pending.options} == _SCIENCE_CLASSES


class TestScholarMishap3ScienceChoice:
    """Mishap 3 Science +1 is deferred until player chooses which broad science (Core p.44)."""

    def _setup_to_choice(self, choice_cls: type[ChoiceBase]) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=3)),
            Event(id=8, fulfills=(7, 0), handler=MishapHandler(roll=3)),
            Event(id=9, fulfills=(8, 0), handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default)),
        ]

    def test_openly_choice_grants_chosen_science(self):
        sci_choice = Event(
            id=10, fulfills=(9, 0), handler=SkillChoiceHandler(skill=LifeScience(biology=Level(value=1)))
        )
        events = [*self._setup_to_choice(ScholarMishap3Openly), sci_choice]
        projection = replay(1, events)

        assert projection.summary.skill_level(LifeScience, -1) >= 1

    def test_secretly_choice_grants_chosen_science(self):
        sci_choice = Event(
            id=10, fulfills=(9, 0), handler=SkillChoiceHandler(skill=PhysicalScience(chemistry=Level(value=1)))
        )
        events = [*self._setup_to_choice(ScholarMishap3Secretly), sci_choice]
        projection = replay(1, events)

        assert projection.summary.skill_level(PhysicalScience, -1) >= 1

    def test_openly_chosen_science_not_fixed_to_space_science(self):
        # Verify a non-space science can be chosen (science choice is free)
        sci_choice = Event(
            id=10, fulfills=(9, 0), handler=SkillChoiceHandler(skill=SocialScience(economics=Level(value=1)))
        )
        events = [*self._setup_to_choice(ScholarMishap3Openly), sci_choice]
        projection = replay(1, events)

        assert projection.summary.skill_level(SocialScience, -1) >= 1
        # Space Science starts at 0 from initial training, but is NOT raised to 1 by the mishap choice
        assert projection.summary.skill_level(SpaceScience, -1) == 0


class TestPhysicianRankBonuses:
    """Physician rank 1 grants Medic 1 (not Science); Field Researcher rank 1 grants Science (choice)."""

    def _setup_to_advancement(self, assignment: str) -> list:
        return [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment(assignment), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),
        ]

    def test_physician_rank_1_grants_medic_not_science_choice(self):
        events = [
            *self._setup_to_advancement('Physician'),
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=9)),  # INT=9 DM+1 → 10 ≥ 8 → advance to rank 1
        ]
        projection = replay(1, events)

        # Physician rank 1 = Medic 1; no science choice pending should be created
        assert projection.summary.skill_level(Medic, -1) >= 1
        science_pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert science_pending is None or {type(s) for s in science_pending.options} != _SCIENCE_CLASSES

    def test_field_researcher_rank_1_creates_science_choice_pending(self):
        events = [
            *self._setup_to_advancement('Field Researcher'),
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=5)),  # INT=9 DM+1 → 6 ≥ 6 → advance to rank 1
        ]
        projection = replay(1, events)

        # Field Researcher rank 1 = Science 1 — player chooses which science
        # Pending kind is rank_bonus_choice_{level} to distinguish from event skill choices
        science_pending = next(
            (
                p
                for p in projection.pending_inputs
                if isinstance(p, PendingRankBonusChoice) and {type(s) for s in p.options} == _SCIENCE_CLASSES
            ),
            None,
        )
        assert science_pending is not None
