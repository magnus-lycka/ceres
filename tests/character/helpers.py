"""Shared test helpers for character tests."""

from typing import Any, Literal

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import AnySkill
from ceres.character.domain.sophont import Sophont
from ceres.character.events import (
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    AssignmentChangeChoiceEvent,
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    MishapEvent,
    MusterOutEvent,
    PendingAdvancement,
    PendingAgingChoice,
    PendingAgingCrisis,
    PendingAgingRoll,
    PendingAssignmentChangeChoice,
    PendingBackgroundSkills,
    PendingCareerChoice,
    PendingChoices,
    PendingMishap,
    PendingMusterOut,
    PendingReenlist,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingSurvive,
    PendingTermEvent,
    PendingUcp,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.mechanism.replay import replay
from ceres.character.state import CharacterProjection, ChoiceBase


class CharacterDriver:
    """High-level test driver for character creation.

    Finds the correct pending input by type and submits the matching event.
    Never hardcodes internal event IDs.
    """

    def __init__(self, character_id: int = 1) -> None:
        self._character_id = character_id
        self._events: list[Any] = []
        self._projection: CharacterProjection | None = None

    @property
    def projection(self) -> CharacterProjection:
        if self._projection is None:
            raise ValueError('No events — call start() first')
        return self._projection

    def _add(self, event: Any) -> CharacterDriver:
        event = event.model_copy(update={'id': len(self._events) + 1})
        self._events.append(event)
        self._projection = replay(self._character_id, self._events)
        return self

    def _find(self, pending_type: type) -> Any:
        found = next((p for p in self.projection.pending_inputs if isinstance(p, pending_type)), None)
        if found is None:
            present = [type(p).__name__ for p in self.projection.pending_inputs]
            raise ValueError(f'No {pending_type.__name__} in pending inputs: {present}')
        return found

    def _find_opt(self, pending_type: type) -> Any:
        return next((p for p in self.projection.pending_inputs if isinstance(p, pending_type)), None)

    def start(
        self,
        sophont: Sophont,
        homeworld: TravellerMapWorld,
        player: str = 'NPC',
        name: str = 'Test',
    ) -> CharacterDriver:
        return self._add(CharacterStartedEvent(sophont=sophont, homeworld=homeworld, player=player, name=name))

    def ucp(self, ucp_string: str) -> CharacterDriver:
        pending = self._find(PendingUcp)
        return self._add(UcpEvent(ucp=ucp_string, fulfills=pending.pending_id))

    def background_skills(self, skills: list[AnySkill]) -> CharacterDriver:
        pending = self._find(PendingBackgroundSkills)
        return self._add(BackgroundSkillsEvent(skills=skills, fulfills=pending.pending_id))

    def career(self, career_name: str, assignment: str, roll: int = 7) -> CharacterDriver:
        pending = self._find(PendingCareerChoice)
        return self._add(
            CareerEvent(career=career_name, assignment=assignment, qualification_roll=roll, fulfills=pending.pending_id)
        )

    def survive(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingSurvive)
        return self._add(SurviveEvent(roll=roll, fulfills=pending.pending_id))

    def mishap(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingMishap)
        return self._add(MishapEvent(roll=roll, fulfills=pending.pending_id))

    def term_event(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingTermEvent)
        return self._add(TermEventEvent(roll=roll, fulfills=pending.pending_id))

    def advancement(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingAdvancement)
        return self._add(AdvancementEvent(roll=roll, fulfills=pending.pending_id))

    def reenlist(self, reenlist: bool) -> CharacterDriver:
        assignment_pending = self._find_opt(PendingAssignmentChangeChoice)
        if assignment_pending is not None:
            choice = 'same' if reenlist else 'muster_out'
            return self._add(AssignmentChangeChoiceEvent(choice=choice, fulfills=assignment_pending.pending_id))
        reenlist_pending = self._find(PendingReenlist)
        return self._add(ReenlistEvent(reenlist=reenlist, fulfills=reenlist_pending.pending_id))

    def skill_table(self, table: str, roll: int) -> CharacterDriver:
        pending = self._find(PendingSkillTable)
        return self._add(SkillTableEvent(table=table, roll=roll, fulfills=pending.pending_id))

    def skill_table_choice(self, skill: AnySkill) -> CharacterDriver:
        pending = self._find(PendingSkillTableChoice)
        return self._add(SkillChoiceEvent(skill=skill, fulfills=pending.pending_id))

    def aging_roll(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingAgingRoll)
        return self._add(AgingRollEvent(roll=roll, fulfills=pending.pending_id))

    def aging_choice(self, characteristic: Chars, amount: int = 1) -> CharacterDriver:
        pending = self._find(PendingAgingChoice)
        return self._add(
            CharacteristicChoiceEvent(characteristic=characteristic, amount=amount, fulfills=pending.pending_id)
        )

    def aging_crisis(self, paid: bool, medical_roll: int) -> CharacterDriver:
        pending = self._find(PendingAgingCrisis)
        return self._add(AgingCrisisEvent(paid=paid, medical_roll=medical_roll, fulfills=pending.pending_id))

    def muster_out(self, table: Literal['cash', 'benefits'], roll: int) -> CharacterDriver:
        pending = self._find(PendingMusterOut)
        return self._add(MusterOutEvent(table=table, roll=roll, fulfills=pending.pending_id))

    def career_choice(self, choice_cls: type[ChoiceBase]) -> CharacterDriver:
        pending = self._find(PendingChoices)
        return self._add(CareerChoiceEvent.for_choice(choice_cls, fulfills=pending.pending_id))

    def skill_roll(self, skill: Any, modified_roll: int) -> CharacterDriver:
        pending = self._find(CareerSkillRollPendingBase)
        return self._add(SkillRollEvent(skill=skill, modified_roll=modified_roll, fulfills=pending.pending_id))


MOCK_WORLD_2 = TravellerMapWorld.model_validate(
    {
        'Name': 'Regina',
        'Hex': '1910',
        'UWP': 'A788899-C',
        'PBG': '703',
        'Zone': '',
        'Bases': 'NW',
        'Allegiance': 'ImDd',
        'Stellar': 'F7 V',
        'SS': 'A',
        'Ix': '{ 4 }',
        'Ex': '(D7E+5)',
        'Cx': '[AC9G]',
        'Nobility': 'BcCeDfFe',
        'Worlds': 8,
        'ResourceUnits': 1116,
        'Subsector': 1,
        'Quadrant': 1,
        'WorldX': -50,
        'WorldY': -10,
        'Remarks': 'Ri Pa Ph An Cp (Spinward Marches) Sa',
        'LegacyBaseCode': 'NW',
        'Sector': 'Spinward Marches',
        'SubsectorName': 'Regina',
        'SectorAbbreviation': 'Spin',
        'AllegianceName': 'Third Imperium, Domain of Deneb',
    }
)

MOCK_WORLD = TravellerMapWorld.model_validate(
    {
        'Name': 'Hexx',
        'Hex': '2715',
        'UWP': 'B78A577-D',
        'PBG': '314',
        'Zone': '',
        'Bases': 'N',
        'Allegiance': 'ImDd',
        'Stellar': 'F6 V',
        'SS': 'H',
        'Ix': '{ 1 }',
        'Ex': '(C45+1)',
        'Cx': '[565D]',
        'Nobility': 'Bc',
        'Worlds': 11,
        'ResourceUnits': 240,
        'Subsector': 7,
        'Quadrant': 1,
        'WorldX': -102,
        'WorldY': -25,
        'Remarks': 'Ni Wa Pr Ht',
        'LegacyBaseCode': 'N',
        'Sector': 'Trojan Reach',
        'SubsectorName': 'Tobia',
        'SectorAbbreviation': 'Troj',
        'AllegianceName': 'Third Imperium, Domain of Deneb',
    }
)
