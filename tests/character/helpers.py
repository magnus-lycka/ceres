"""Shared test helpers for character tests."""

from typing import Any, Literal

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.career.career_events import (
    AdvancementHandler,
    AssignmentChangeChoiceHandler,
    CareerChoiceHandler,
    CareerEntryHandler,
    CharacteristicChoiceHandler,
    MishapHandler,
    MusterOutHandler,
    PendingAdvancement,
    PendingAssignmentChangeChoice,
    PendingCareerChoice,
    PendingChoices,
    PendingInitialTrainingChoice,
    PendingMishap,
    PendingMusterOut,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingSurvive,
    PendingSwitchAssignment,
    PendingTermEvent,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillRollHandler,
    SkillTableHandler,
    SurviveHandler,
    SwitchAssignmentHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common_pending import CareerSkillChoicePendingBase, CareerSkillRollPendingBase
from ceres.character.domain.character_start import (
    BackgroundSkillsHandler,
    CharacterStartedHandler,
    PendingBackgroundSkills,
    PendingUcp,
    UcpHandler,
)
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.health.health_events import (
    AgingCrisisHandler,
    AgingRollHandler,
    PendingAgingChoice,
    PendingAgingCrisis,
    PendingAgingRoll,
)
from ceres.character.domain.skills import AnySkill
from ceres.character.domain.sophont import Sophont
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.pending_input import ChoiceBase
from ceres.character.mechanism.replay import replay


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
        return self._add(
            Event(handler=CharacterStartedHandler(sophont=sophont, homeworld=homeworld, player=player, name=name))
        )

    def ucp(self, ucp_string: str) -> CharacterDriver:
        pending = self._find(PendingUcp)
        return self._add(Event(fulfills=pending.pending_id, handler=UcpHandler(ucp=ucp_string)))

    def background_skills(self, skills: list[AnySkill]) -> CharacterDriver:
        pending = self._find(PendingBackgroundSkills)
        return self._add(Event(fulfills=pending.pending_id, handler=BackgroundSkillsHandler(skills=skills)))

    def career(self, career_name: str, assignment: str, roll: int = 7) -> CharacterDriver:
        from ceres.character.domain.career.loader import load_careers

        pending = self._find(PendingCareerChoice)
        career_obj = next((c for c in pending.options if c.name == career_name), None) or load_careers()[career_name]
        assignment_obj = career_obj.assignment(assignment)
        if assignment_obj is None:
            raise ValueError(f'Unknown assignment {assignment!r} for career {career_name!r}')
        return self._add(
            Event(
                fulfills=pending.pending_id,
                handler=CareerEntryHandler(career=career_obj, assignment=assignment_obj, qualification_roll=roll),
            )
        )

    def survive(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingSurvive)
        return self._add(Event(fulfills=pending.pending_id, handler=SurviveHandler(roll=roll)))

    def mishap(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingMishap)
        return self._add(Event(fulfills=pending.pending_id, handler=MishapHandler(roll=roll)))

    def term_event(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingTermEvent)
        return self._add(Event(fulfills=pending.pending_id, handler=TermEventHandler(roll=roll)))

    def advancement(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingAdvancement)
        return self._add(Event(fulfills=pending.pending_id, handler=AdvancementHandler(roll=roll)))

    def reenlist(self, reenlist: bool) -> CharacterDriver:
        assignment_pending = self._find_opt(PendingAssignmentChangeChoice)
        if assignment_pending is not None:
            choice = 'same' if reenlist else 'muster_out'
            return self._add(
                Event(fulfills=assignment_pending.pending_id, handler=AssignmentChangeChoiceHandler(choice=choice))
            )
        reenlist_pending = self._find(PendingReenlist)
        return self._add(Event(fulfills=reenlist_pending.pending_id, handler=ReenlistHandler(reenlist=reenlist)))

    def initial_training(self, skill: AnySkill) -> CharacterDriver:
        pending = self._find(PendingInitialTrainingChoice)
        return self._add(Event(fulfills=pending.pending_id, handler=SkillChoiceHandler(skill=skill)))

    def rank_bonus_choice(self, skill: AnySkill) -> CharacterDriver:
        pending = self._find(PendingRankBonusChoice)
        return self._add(Event(fulfills=pending.pending_id, handler=SkillChoiceHandler(skill=skill)))

    def choose_switch(self) -> CharacterDriver:
        """Resolve the assignment-change step 1 with 'switch', leaving step 2 pending."""
        pending = self._find(PendingAssignmentChangeChoice)
        return self._add(Event(fulfills=pending.pending_id, handler=AssignmentChangeChoiceHandler(choice='switch')))

    def available_switch_assignments(self) -> list[str]:
        """Return the assignment names offered in the current PendingSwitchAssignment."""
        pending = self._find(PendingSwitchAssignment)
        return [a.name for a in pending.options]

    def switch_assignment(self, assignment: str, roll: int) -> CharacterDriver:
        self.choose_switch()
        switch_pending = self._find(PendingSwitchAssignment)
        assignment_obj = next((a for a in switch_pending.options if a.name == assignment), None)
        if assignment_obj is None:
            raise ReplayError(
                f'Unknown assignment {assignment!r} in switch options: {[a.name for a in switch_pending.options]}'
            )
        return self._add(
            Event(
                fulfills=switch_pending.pending_id,
                handler=SwitchAssignmentHandler(assignment=assignment_obj, qualification_roll=roll),
            )
        )

    def skill_table(self, table: str, roll: int) -> CharacterDriver:
        pending = self._find(PendingSkillTable)
        option = next((o for o in pending.options if o.key == table or o.label.lower() == table.lower()), None)
        key = option.key if option else table
        return self._add(Event(fulfills=pending.pending_id, handler=SkillTableHandler(table=key, roll=roll)))

    def skill_table_choice(self, skill: AnySkill) -> CharacterDriver:
        pending = self._find(PendingSkillTableChoice)
        return self._add(Event(fulfills=pending.pending_id, handler=SkillChoiceHandler(skill=skill)))

    def aging_roll(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingAgingRoll)
        return self._add(Event(fulfills=pending.pending_id, handler=AgingRollHandler(roll=roll)))

    def aging_choice(self, characteristic: Chars, amount: int = 1) -> CharacterDriver:
        pending = self._find(PendingAgingChoice)
        return self._add(
            Event(
                fulfills=pending.pending_id,
                handler=CharacteristicChoiceHandler(characteristic=characteristic, amount=amount),
            )
        )

    def aging_crisis(self, paid: bool, medical_roll: int) -> CharacterDriver:
        pending = self._find(PendingAgingCrisis)
        return self._add(
            Event(fulfills=pending.pending_id, handler=AgingCrisisHandler(paid=paid, medical_roll=medical_roll))
        )

    def muster_out(self, table: Literal['cash', 'benefits'], roll: int) -> CharacterDriver:
        pending = self._find(PendingMusterOut)
        return self._add(Event(fulfills=pending.pending_id, handler=MusterOutHandler(table=table, roll=roll)))

    def career_choice(self, choice_cls: type[ChoiceBase]) -> CharacterDriver:
        pending = self._find(PendingChoices)
        choice_kind = choice_cls.model_fields['kind'].default
        return self._add(Event(fulfills=pending.pending_id, handler=CareerChoiceHandler(choice=choice_kind)))

    def choose_career_skill(self, skill: AnySkill) -> CharacterDriver:
        pending = self._find(CareerSkillChoicePendingBase)
        return self._add(Event(fulfills=pending.pending_id, handler=SkillChoiceHandler(skill=skill)))

    def skill_roll(self, skill: Any, modified_roll: int) -> CharacterDriver:
        pending = self._find(CareerSkillRollPendingBase)
        return self._add(
            Event(fulfills=pending.pending_id, handler=SkillRollHandler(skill=skill, modified_roll=modified_roll))
        )


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
        'Bases': 'NS',
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
        'LegacyBaseCode': 'NS',
        'Sector': 'Trojan Reach',
        'SubsectorName': 'Tobia',
        'SectorAbbreviation': 'Troj',
        'AllegianceName': 'Third Imperium, Domain of Deneb',
    }
)
