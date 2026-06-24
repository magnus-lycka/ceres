"""Tests for the Core Psion career."""

from typing import Literal

import pytest

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.benefits import COMBAT_IMPLANT, CONTACT, GUN, SHIP_SHARE, TAS_MEMBERSHIP
from ceres.character.domain.career import ARMY, PSION
from ceres.character.domain.career.career_events import (
    CareerEntryHandler,
    PendingAdvancement,
    PendingCareerChoice,
    PendingChoices,
    PendingDraftChoice,
    PendingInitialTrainingChoice,
    PendingLifeEvent,
    PendingMishap,
    PendingRankBonusChoice,
    PendingSkillChoice,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingSurvive,
    PendingTermEvent,
    SkillChoiceHandler,
    SkillTableHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.loader import selectable_careers
from ceres.character.domain.career.psion import (
    PendingPsionConnectionConversion,
    PendingPsionMishap3Roll,
    PsionEvent5Accept,
    PsionEvent5Benefit,
    PsionEvent5Soc,
    PsionMishap4Accept,
    PsionMishap4Refuse,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.connection import Ally, Contact, Enemy
from ceres.character.domain.health.health_events import (
    PendingInjuryTable,
)
from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeOffered
from ceres.character.domain.psionics import (
    PendingPsionicInstituteTraining,
    Psi,
    Psionics,
    Telepathy,
    psionic_talent_instances,
)
from ceres.character.domain.skills import (
    Admin,
    Athletics,
    Carouse,
    CreativeArt,
    Drive,
    GunCombat,
    JackOfAllTrades,
    Level,
    PerformingArt,
    PresentationArt,
    Stealth,
    Survival,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import Select
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver


def _setup(homeworld: TravellerMapWorld = MOCK_WORLD, psi: int = 9) -> list[Event]:
    ev1 = Event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=homeworld, player='NPC', name='Psi'))
    ev2 = Event(fulfills=(ev1.id, 0), handler=UcpHandler(ucp='7869A5'))
    ev3 = Event(
        fulfills=(ev2.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    return [
        ev1,
        ev2,
        ev3,
        Event(fulfills=(ev3.id, 0), handler=_SetPsiForTest(psi=psi)),
    ]


class _SetPsiForTest(EventHandlerBase):
    kind: Literal['test_set_psi'] = 'test_set_psi'
    psi: int

    def apply(self, projection, event, fulfilled_pending=None) -> None:
        projection.summary.characteristics[Chars.PSI] = self.psi
        projection.summary.psionics = Psionics() if self.psi > 0 else None


class _SetTrainedPsiForTest(EventHandlerBase):
    kind: Literal['test_set_trained_psi'] = 'test_set_trained_psi'

    def apply(self, projection, event, fulfilled_pending=None) -> None:
        projection.summary.characteristics[Chars.PSI] = 9
        projection.summary.psionics = Psionics(
            psionic_talent_skills=psionic_talent_instances(),
            talent_acquisition_checks=5,
        )


class PsionDriver(CharacterDriver):
    def establish_trained_psi(self) -> PsionDriver:
        pending = self._find(PendingCareerChoice)
        self._add(Event(fulfills=pending.pending_id, handler=_SetTrainedPsiForTest()))
        return self

    def enter_psion(self, assignment: str = 'Wild Talent') -> PsionDriver:
        career = PSION
        assignment_data = career.assignment(assignment)
        assert assignment_data is not None
        self._add(Event(handler=CareerEntryHandler(career=career, assignment=assignment_data, qualification_roll=7)))
        while pending := self._find_opt(PendingInitialTrainingChoice):
            option = next((option for option in pending.options if not isinstance(option, Psi)), None)
            assert option is not None, (
                'Trained Psion should not be offered another psionic talent during basic training'
            )
            self._add(Event(fulfills=pending.pending_id, handler=SkillChoiceHandler(skill=option)))
        return self

    def psion_mishap_three_result(self, roll: int) -> PsionDriver:
        from ceres.character.domain.career.psion import PsionMishap3RollHandler

        pending = self._find(PendingPsionMishap3Roll)
        self._add(Event(fulfills=pending.pending_id, handler=PsionMishap3RollHandler(roll=roll)))
        return self


def _psion_driver(assignment: str = 'Wild Talent') -> PsionDriver:
    driver = PsionDriver()
    driver.start(VILANI, MOCK_WORLD).ucp('7869A5').background_skills([Admin(), Athletics(), Carouse(), Drive()])
    driver.establish_trained_psi().enter_psion(assignment)
    return driver


def _enter_psion(
    assignment: str = 'Wild Talent',
    qualification_roll: int = 7,
    homeworld: TravellerMapWorld = MOCK_WORLD,
    psi: int = 9,
) -> list[Event]:
    psion = PSION
    resolved_assignment = psion.assignment(assignment)
    assert resolved_assignment is not None
    return [
        *_setup(homeworld, psi),
        Event(
            handler=CareerEntryHandler(
                career=psion,
                assignment=resolved_assignment,
                qualification_roll=qualification_roll,
            ),
        ),
    ]


class TestPsionCareer:
    def test_registered_with_core_assignments(self):
        psion = PSION

        assert [assignment.name for assignment in psion.assignments] == ['Wild Talent', 'Adept', 'Psi-Warrior']
        assert psion.qualification.characteristic is Chars.PSI
        assert psion.qualification.target == 6
        assert psion.does_draft() is False

    def test_only_selectable_after_psi_test_of_nine_or_more(self):
        without_psi = replay(1, _setup(psi=0)[:-1])
        low_psi = replay(1, _setup(psi=8))
        eligible = replay(1, _setup(psi=9))

        assert PSION not in selectable_careers(without_psi)
        assert PSION not in selectable_careers(low_psi)
        assert PSION in selectable_careers(eligible)

    def test_failed_qualification_returns_to_career_choice_without_draft(self):
        projection = replay(1, _enter_psion(qualification_roll=2))

        assert any(isinstance(p, PendingCareerChoice) for p in projection.pending_inputs)
        assert not any(isinstance(p, PendingDraftChoice) for p in projection.pending_inputs)
        assert projection.summary.current_career is None

    def test_each_assignment_uses_its_specialist_table_for_basic_training(self):
        for assignment in ('Wild Talent', 'Adept', 'Psi-Warrior'):
            projection = replay(1, _enter_psion(assignment))

            talent_choices = [
                option
                for pending in projection.pending_inputs
                if isinstance(pending, PendingInitialTrainingChoice)
                for option in pending.options
                if isinstance(option, Psi)
            ]
            assert talent_choices == []

    def test_basic_training_does_not_improve_possessed_talents(self):
        driver = PsionDriver()
        driver.start(VILANI, MOCK_WORLD).ucp('7869A5').background_skills([Admin(), Athletics(), Carouse(), Drive()])
        driver.establish_trained_psi().enter_psion('Adept')

        assert driver.projection.summary.psionics is not None
        assert all(talent.level.value == 0 for talent in driver.projection.summary.psionics.psionic_talent_skills)

    def test_mishap_two_loses_one_psi(self):
        driver = _psion_driver()
        driver.survive(6).mishap(2)

        assert driver.projection.summary.characteristics[Chars.PSI] == 8
        assert driver.projection.summary.current_career is None
        assert driver._find(PendingCareerChoice)

    def test_event_eight_increases_psi(self):
        driver = _psion_driver()
        driver.survive(7).term_event(8)

        assert driver.projection.summary.characteristics[Chars.PSI] == 10
        assert driver._find(PendingAdvancement)

    def test_psi_warrior_rank_one_offers_gun_combat_specialisations_then_skill_table(self):
        driver = _psion_driver('Psi-Warrior')
        driver.survive(6).term_event(8).advancement(6)

        pending = driver._find(PendingRankBonusChoice)
        select = pending.input_specs(driver.projection)[0]
        assert isinstance(select, Select)
        assert {label for label, _ in select.options} == {
            'Gun Combat (Archaic)',
            'Gun Combat (Energy)',
            'Gun Combat (Slug)',
        }
        assert driver.projection.summary.skill_level(GunCombat, -1) == 0

        driver._add(
            Event(
                fulfills=pending.pending_id,
                handler=SkillChoiceHandler(skill=GunCombat(slug=Level(value=1))),
            )
        )

        gun_combat = next(skill for skill in driver.projection.summary.skills if isinstance(skill, GunCombat))
        assert gun_combat.slug.value == 1
        assert gun_combat.archaic.value == 0
        assert gun_combat.energy.value == 0
        assert driver.projection.summary.rank == 1
        assert driver._find(PendingSkillTable)

    def test_army_rank_zero_offers_one_gun_combat_specialisation(self):
        army = ARMY
        infantry = army.assignment('Infantry')
        assert infantry is not None
        events = [
            *_setup(),
            Event(handler=CareerEntryHandler(career=army, assignment=infantry, qualification_roll=7)),
        ]

        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingRankBonusChoice))
        select = pending.input_specs(projection)[0]
        assert isinstance(select, Select)
        assert len(select.options) == 3
        gun_combat = next(skill for skill in projection.summary.skills if isinstance(skill, GunCombat))
        assert [gun_combat.archaic.value, gun_combat.energy.value, gun_combat.slug.value] == [0, 0, 0]

    def test_mishap_four_asks_whether_to_accept_unethical_work(self):
        driver = _psion_driver()
        driver.survive(6).mishap(4)

        assert driver._find(PendingChoices)

    def test_event_five_asks_whether_to_use_powers_unethically(self):
        driver = _psion_driver()
        driver.survive(7).term_event(5)

        assert driver._find(PendingChoices)


class TestPsionHomeworldRule:
    def test_institute_training_precedes_relocation_and_basic_training(self):
        projection = replay(1, _enter_psion())

        assert isinstance(projection.pending_inputs[0], PendingPsionicInstituteTraining)

    def test_non_x_starport_offers_optional_relocation(self):
        projection = replay(1, _enter_psion())

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeOffered))
        assert pending.blocking is False
        assert pending.source_kind == 'career_entry'
        assert pending.source_career == 'Psion'
        assert pending.target_constraints is None

    def test_x_starport_does_not_offer_relocation(self):
        x_world = TravellerMapWorld.model_validate({**MOCK_WORLD.model_dump(), 'UWP': 'X78A577-D'})

        projection = replay(1, _enter_psion(homeworld=x_world))

        assert not any(isinstance(p, PendingHomeworldChangeOffered) for p in projection.pending_inputs)

    def test_every_new_term_on_starport_world_offers_relocation(self):
        psion = PSION
        assignment = psion.assignment('Wild Talent')
        assert assignment is not None
        projection = replay(1, _enter_psion())

        psion.start_new_term(projection, assignment, event_id=6, is_continuation=True)

        offers = [p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeOffered)]
        assert len(offers) == 2


class TestPsionValidLifecycle:
    @pytest.mark.parametrize('assignment', ['Wild Talent', 'Adept', 'Psi-Warrior'])
    def test_entry_resolves_real_basic_training_before_survival(self, assignment: str):
        driver = _psion_driver(assignment)

        assert driver.projection.summary.current_assignment is not None
        assert driver.projection.summary.current_assignment.name == assignment
        assert not any(isinstance(p, PendingInitialTrainingChoice) for p in driver.projection.pending_inputs)
        assert driver._find(PendingSurvive)

    @pytest.mark.parametrize(
        ('assignment', 'pass_roll', 'fail_roll'),
        [
            ('Wild Talent', 7, 6),
            ('Adept', 3, 2),
            ('Psi-Warrior', 6, 5),
        ],
    )
    def test_assignment_survival_checks(self, assignment: str, pass_roll: int, fail_roll: int):
        passed = _psion_driver(assignment)
        passed.survive(pass_roll)
        assert passed._find(PendingTermEvent)

        failed = _psion_driver(assignment)
        failed.survive(fail_roll)
        assert failed._find(PendingMishap)


class TestPsionCoreTables:
    def test_service_skills_may_offer_acquisition_of_an_unpossessed_talent(self):
        driver = _psion_driver('Adept')
        assert driver.projection.summary.psionics is not None
        driver.projection.summary.psionics.psionic_talent_skills = [
            talent
            for talent in driver.projection.summary.psionics.psionic_talent_skills
            if not isinstance(talent, Telepathy)
        ]
        driver.projection.pending_inputs.clear()

        Event(handler=SkillTableHandler(table='service_skills', roll=1)).apply(driver.projection)

        pending = driver._find(PendingSkillTableChoice)
        assert len(pending.options) == 1
        assert isinstance(pending.options[0], Psi)
        assert isinstance(pending.options[0].talent, Telepathy)

    def test_assignment_table_cannot_offer_acquisition_of_an_unpossessed_talent(self):
        driver = _psion_driver('Adept')
        assert driver.projection.summary.psionics is not None
        driver.projection.summary.psionics.psionic_talent_skills = [
            talent
            for talent in driver.projection.summary.psionics.psionic_talent_skills
            if not isinstance(talent, Telepathy)
        ]
        driver.projection.pending_inputs.clear()

        Event(handler=SkillTableHandler(table='assignment2', roll=1)).apply(driver.projection)

        assert not any(isinstance(pending, PendingSkillTableChoice) for pending in driver.projection.pending_inputs)
        assert driver._find(PendingSurvive)

    def test_assignment_progress_checks_match_core(self):
        psion = PSION

        assert {
            assignment.name: (
                assignment.survival.characteristic,
                assignment.survival.target,
                assignment.advancement.characteristic,
                assignment.advancement.target,
            )
            for assignment in psion.assignments
        } == {
            'Wild Talent': (Chars.SOC, 6, Chars.INT, 8),
            'Adept': (Chars.EDU, 4, Chars.EDU, 8),
            'Psi-Warrior': (Chars.END, 6, Chars.END, 6),
        }

    def test_muster_out_table_matches_core(self):
        rows = PSION.muster_out.rows

        assert [(rows[roll].cash, rows[roll].benefit, rows[roll].count) for roll in range(1, 8)] == [
            (1000, GUN, 1),
            (2000, SHIP_SHARE, 2),
            (4000, CONTACT, 1),
            (4000, TAS_MEMBERSHIP, 1),
            (8000, CONTACT, 1),
            (8000, COMBAT_IMPLANT, 1),
            (16000, SHIP_SHARE, 10),
        ]

    def test_rank_titles_match_core(self):
        psion = PSION

        assert [psion.assignment_ranks(1)[rank].title or '' for rank in range(7)] == [
            '',
            'Survivor',
            '',
            'Witch',
            '',
            '',
            '',
        ]
        adept = psion.assignment('Adept')
        psi_warrior = psion.assignment('Psi-Warrior')
        assert adept is not None
        assert psi_warrior is not None
        assert [psion.assignment_ranks(psion.assignment_index(adept))[rank].title or '' for rank in range(7)] == [
            '',
            'Initiate',
            '',
            'Acolyte',
            '',
            '',
            'Master',
        ]
        assert [psion.assignment_ranks(psion.assignment_index(psi_warrior))[rank].title or '' for rank in range(7)] == [
            'Psi-Soldier',
            '',
            'Knight',
            '',
            '',
            'Master of Wills',
            '',
        ]


class TestPsionMishaps:
    def _failed_survival(self) -> PsionDriver:
        driver = _psion_driver()
        driver.survive(6)
        return driver

    def test_mishap_one_uses_common_handler(self):
        driver = self._failed_survival()
        driver.mishap(1)

        pending = driver._find(PendingChoices)
        assert {type(choice) for choice in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}

    @pytest.mark.parametrize(
        ('result', 'injured', 'soc_loss'),
        [(1, True, 0), (2, True, 0), (3, False, 1), (4, False, 1), (5, False, 0), (6, False, 0)],
    )
    def test_mishap_three_resolves_anti_psi_attack(self, result: int, injured: bool, soc_loss: int):
        driver = self._failed_survival()
        starting_soc = driver.projection.summary.characteristics[Chars.SOC]
        driver.mishap(3)
        driver.psion_mishap_three_result(result)

        assert driver.projection.summary.current_career is None
        assert any(isinstance(p, PendingInjuryTable) for p in driver.projection.pending_inputs) is injured
        assert driver.projection.summary.characteristics[Chars.SOC] == starting_soc - soc_loss

    def test_mishap_four_accepts_unethical_work_and_continues(self):
        driver = self._failed_survival()
        driver.mishap(4).career_choice(PsionMishap4Accept)

        assert driver.projection.summary.current_career is not None
        assert any(isinstance(connection, Enemy) for connection in driver.projection.summary.connections)
        assert driver._find(PendingAdvancement)

    def test_mishap_four_refusal_ejects(self):
        driver = self._failed_survival()
        driver.mishap(4).career_choice(PsionMishap4Refuse)

        assert driver.projection.summary.current_career is None

    @pytest.mark.parametrize('roll', [2, 5])
    def test_mishaps_with_no_deferred_choice_eject(self, roll: int):
        driver = self._failed_survival()
        driver.mishap(roll)

        assert driver.projection.summary.current_career is None

    def test_mishap_six_converts_a_connection_to_enemy(self):
        driver = self._failed_survival()
        driver.mishap(6)

        pending = driver._find(PendingPsionConnectionConversion)
        assert pending.new_kind is ConnectionKind.ENEMY


class TestPsionEvents:
    def _event(self, roll: int) -> PsionDriver:
        driver = _psion_driver()
        driver.survive(7).term_event(roll)
        return driver

    def test_event_two_rolls_mishap_without_ejection(self):
        driver = self._event(2)

        pending = driver._find(PendingMishap)
        assert pending.stay_in_career is True

    def test_event_three_converts_connection_to_rival_then_advances(self):
        driver = self._event(3)
        pending = driver._find(PendingPsionConnectionConversion)

        assert pending.new_kind is ConnectionKind.RIVAL
        assert pending.continue_term is True

    def test_event_four_offers_only_the_core_skill_families_at_level_one(self):
        driver = self._event(4)
        pending = driver._find(PendingSkillChoice)

        assert {type(option) for option in pending.options} == {
            Athletics,
            Stealth,
            Survival,
            PerformingArt,
            CreativeArt,
            PresentationArt,
        }

    def test_event_five_refusal_continues_to_advancement(self):
        driver = self._event(5)
        from ceres.character.domain.career.psion import PsionEvent5Refuse

        driver.career_choice(PsionEvent5Refuse)
        assert driver._find(PendingAdvancement)

    def test_event_five_failed_psi_roll_loses_soc_and_advances(self):
        driver = self._event(5)
        starting_soc = driver.projection.summary.characteristics[Chars.SOC]
        driver.career_choice(PsionEvent5Accept).skill_roll(Chars.PSI, modified_roll=7)

        assert driver.projection.summary.characteristics[Chars.SOC] == starting_soc - 1
        assert driver._find(PendingAdvancement)

    def test_event_five_success_offers_benefit_roll_or_soc(self):
        driver = self._event(5)
        driver.career_choice(PsionEvent5Accept).skill_roll(Chars.PSI, modified_roll=8)

        pending = driver._find(PendingChoices)
        assert {type(choice) for choice in pending.choices} == {PsionEvent5Benefit, PsionEvent5Soc}

    def test_event_five_benefit_choice_adds_extra_muster_roll(self):
        driver = self._event(5)
        driver.career_choice(PsionEvent5Accept).skill_roll(Chars.PSI, modified_roll=8)
        driver.career_choice(PsionEvent5Benefit)

        assert driver.projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1
        assert driver._find(PendingAdvancement)

    def test_event_five_soc_choice_increases_soc(self):
        driver = self._event(5)
        starting_soc = driver.projection.summary.characteristics[Chars.SOC]
        driver.career_choice(PsionEvent5Accept).skill_roll(Chars.PSI, modified_roll=8)
        driver.career_choice(PsionEvent5Soc)

        assert driver.projection.summary.characteristics[Chars.SOC] == starting_soc + 1
        assert driver._find(PendingAdvancement)

    def test_event_six_adds_contact(self):
        driver = self._event(6)

        assert any(isinstance(connection, Contact) for connection in driver.projection.summary.connections)
        assert driver._find(PendingAdvancement)

    def test_event_seven_queues_life_event(self):
        driver = self._event(7)

        assert driver._find(PendingLifeEvent)

    def test_event_eight_increases_psi_and_advances(self):
        driver = self._event(8)

        assert driver.projection.summary.characteristics[Chars.PSI] == 10
        assert driver._find(PendingAdvancement)

    def test_event_nine_advanced_training_excludes_jack_of_all_trades(self):
        driver = self._event(9)
        driver.skill_roll(Chars.EDU, modified_roll=8)

        pending = driver._find(PendingSkillChoice)
        assert not any(isinstance(skill, JackOfAllTrades) for skill in pending.options)

    def test_event_nine_failed_training_advances_without_skill_choice(self):
        driver = self._event(9)
        driver.skill_roll(Chars.EDU, modified_roll=7)

        assert not any(isinstance(p, PendingSkillChoice) for p in driver.projection.pending_inputs)
        assert driver._find(PendingAdvancement)

    def test_event_ten_adds_one_benefit_roll_dm(self):
        driver = self._event(10)

        muster_out = driver.projection.summary.career_terms[-1].require_muster_out()
        assert [dm.amount for dm in muster_out.benefit_roll_dms] == [1]
        assert driver._find(PendingAdvancement)

    def test_event_eleven_adds_ally_and_next_advancement_dm(self):
        driver = self._event(11)

        assert any(isinstance(connection, Ally) for connection in driver.projection.summary.connections)
        assert driver.projection.pending_advancement_dm == 4
        assert driver._find(PendingAdvancement)

    def test_event_twelve_automatically_promotes(self):
        driver = self._event(12)

        assert driver.projection.summary.rank == 1
        assert driver._find(PendingRankBonusChoice)
