"""Shared test helpers for character tests."""

import copy
from pathlib import Path
from typing import Any, Literal

from deepdiff import DeepDiff

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.career.career_events import (
    AdvancementDmChoiceHandler,
    AdvancementHandler,
    AssignmentChangeChoiceHandler,
    BenefitChoiceHandler,
    CareerChoiceHandler,
    CareerEntryHandler,
    CharacteristicChoiceHandler,
    CommissionHandler,
    MishapHandler,
    MusterOutHandler,
    PendingAdvancement,
    PendingAssignmentChangeChoice,
    PendingBenefitChoice,
    PendingCareerChoice,
    PendingChoices,
    PendingCommissionChoice,
    PendingInitialTrainingChoice,
    PendingMishap,
    PendingMusterOut,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingSkillChoice,
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
from ceres.character.domain.career.common_pending import (
    CareerSkillChoicePendingBase,
    CareerSkillRollPendingBase,
    PendingAdvancedTrainingSkillRoll,
    PendingAnySkillAtLevelOnSuccessRoll,
)
from ceres.character.domain.character_start import (
    BackgroundSkillsHandler,
    CharacterCreatedHandler,
    HomeworldSelectedHandler,
    PendingBackgroundSkills,
    PendingUcp,
    SophontSelectedHandler,
    UcpHandler,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.connection_events import (
    ConnectionNameHandler,
    ConnectionsRollHandler,
    PendingConnectionName,
    PendingConnectionsRoll,
)
from ceres.character.domain.event_handlers import register_event_handlers
from ceres.character.domain.health.health_events import (
    AgingCrisisHandler,
    AgingRollHandler,
    DoubleInjuryTableHandler,
    PendingAgingChoice,
    PendingAgingCrisis,
    PendingAgingRoll,
    PendingCharacteristicChoice,
    PendingDoubleInjuryRoll,
)
from ceres.character.domain.skills import Admin, AnySkill, Athletics, Carouse, Medic
from ceres.character.domain.sophont import VILANI, Sophont
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import ChoiceBase
from ceres.character.mechanism.replay import replay
from ceres.character.mechanism.store import SqliteCharacterBackend


def create_backend(database: str | Path | None = None) -> SqliteCharacterBackend:
    return SqliteCharacterBackend(
        database=database,
        ensure_handlers_registered=register_event_handlers,
        summary_from_json=CharacterSummary.model_validate_json,
    )


def scripted_event(
    *,
    handler: EventHandlerBase,
    id_: int | None = None,
    fulfills: tuple[int, int] | str | None = None,
) -> Event:
    """Build replay-script events while keeping explicit ids out of test bodies."""
    if id_ is None:
        return Event(handler=handler, fulfills=fulfills)
    return Event.model_validate({'id': id_, 'fulfills': fulfills, 'handler': handler})


def pending_id(source: Event | int, pending_index: int) -> tuple[int, int]:
    event_id = source.id if isinstance(source, Event) else source
    return (event_id, pending_index)


class AdvancedTrainingTestMixin:
    """Shared tests for career advanced training events (EDU skill roll → existing skill choice).

    Subclasses must provide _setup_to_event() returning 6 events ending at the term event.
    Override _existing_service_skill_type() and _failure_queues_commission() as needed.
    """

    def _setup_to_event(self) -> list:
        raise NotImplementedError

    def _existing_service_skill_type(self) -> type:
        """A skill type guaranteed to appear in the success skill-choice options."""
        raise NotImplementedError

    def _failure_queues_commission(self) -> bool:
        return False

    def test_creates_edu_skill_roll_pending(self) -> None:
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingAdvancedTrainingSkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == ['EDU']

    def test_success_creates_skill_choice_with_existing_skills(self) -> None:
        setup = self._setup_to_event()
        events = [*setup, Event(fulfills=(setup[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert any(isinstance(o, self._existing_service_skill_type()) for o in pending.options)

    def test_failure_no_skill_choice(self) -> None:
        setup = self._setup_to_event()
        events = [*setup, Event(fulfills=(setup[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7))]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_queues_advancement(self) -> None:
        setup = self._setup_to_event()
        events = [*setup, Event(fulfills=(setup[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7))]
        projection = replay(1, events)
        if self._failure_queues_commission():
            assert any(isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs)
        else:
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


class AnySkillAtLevelTestMixin:
    """Shared tests for 'roll EDU N+ to gain any one skill at level 1' events.

    Subclasses must provide _setup_to_event(), _absent_skill_type() (a skill the
    character definitely does not have at the time of the event), and
    _absent_skill_instance() (a level-1 instance of that skill).
    Override _threshold() and _failure_queues_commission() as needed.
    """

    def _setup_to_event(self) -> list:
        raise NotImplementedError

    def _absent_skill_type(self) -> type:
        """A skill type guaranteed to be absent from the character's skills at event time."""
        raise NotImplementedError

    def _absent_skill_instance(self) -> Any:
        """A level-1 instance of the absent skill, for the fulfillment test."""
        raise NotImplementedError

    def _threshold(self) -> int:
        return 8

    def _failure_queues_commission(self) -> bool:
        return False

    def test_creates_edu_skill_roll_pending(self) -> None:
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingAnySkillAtLevelOnSuccessRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == ['EDU']
        assert pending.threshold == self._threshold()

    def test_success_offers_any_skill_including_absent_ones(self) -> None:
        passing_roll = self._threshold() + 1
        setup = self._setup_to_event()
        events = [
            *setup,
            Event(fulfills=(setup[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=passing_roll)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert any(isinstance(o, self._absent_skill_type()) for o in pending.options)

    def test_success_chosen_skill_granted_at_level_1(self) -> None:
        passing_roll = self._threshold() + 1
        skill = self._absent_skill_instance()
        setup = self._setup_to_event()
        ev7 = Event(fulfills=(setup[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=passing_roll))
        ev8 = Event(fulfills=(ev7.id, 0), handler=SkillChoiceHandler(skill=skill))
        events = [*setup, ev7, ev8]
        projection = replay(1, events)
        assert projection.summary.skill_level(type(skill)) == 1

    def test_failure_no_skill_choice(self) -> None:
        setup = self._setup_to_event()
        events = [*setup, Event(fulfills=(setup[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7))]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_queues_advancement(self) -> None:
        setup = self._setup_to_event()
        events = [*setup, Event(fulfills=(setup[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7))]
        projection = replay(1, events)
        if self._failure_queues_commission():
            assert any(isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs)
        else:
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


def _creation_events(
    sophont: Sophont,
    homeworld: TravellerMapWorld,
    player: str = 'NPC',
    name: str = 'Test',
) -> list[Event]:
    """Return the three creation events: CharacterCreated → HomeworldSelected → SophontSelected."""
    ev1 = Event(handler=CharacterCreatedHandler(name=name, player=player))
    ev2 = Event(fulfills=(ev1.id, 0), handler=HomeworldSelectedHandler(homeworld=homeworld))
    ev3 = Event(fulfills=(ev2.id, 0), handler=SophontSelectedHandler(sophont=sophont))
    return [ev1, ev2, ev3]


def _scholar_setup() -> list:
    """Return start→ucp→background events suited for Scholar tests.

    Uses Medic instead of Drive so Scholar service_skills row 1 (Drive/Flyer) keeps both options
    open, producing two initial-training choice pendings: Drive/Flyer (.0) and Science (.1).
    """
    creation = _creation_events(VILANI, MOCK_WORLD, 'NPC', 'Boss')
    ev_ucp = Event(fulfills=(creation[-1].id, 0), handler=UcpHandler(ucp='7869A5'))
    ev_bg = Event(
        fulfills=(ev_ucp.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Medic()]),
    )
    return [*creation, ev_ucp, ev_bg]


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
        ev1, ev2, ev3 = _creation_events(sophont, homeworld, player, name)
        self._events.extend([ev1, ev2, ev3])
        self._projection = replay(self._character_id, self._events)
        return self

    def ucp(self, ucp_string: str) -> CharacterDriver:
        pending = self._find(PendingUcp)
        return self._add(Event(fulfills=pending.pending_id, handler=UcpHandler(ucp=ucp_string)))

    def background_skills(self, skills: list[AnySkill]) -> CharacterDriver:
        pending = self._find(PendingBackgroundSkills)
        return self._add(Event(fulfills=pending.pending_id, handler=BackgroundSkillsHandler(skills=skills)))

    def career(self, career_name: str, assignment: str, roll: int = 7) -> CharacterDriver:
        pending = self._find(PendingCareerChoice)
        career_obj = next((c for c in pending.options if c.name == career_name), None)
        if career_obj is None:
            raise ValueError(f'Career {career_name!r} is not available in the current pending choice')
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

    def mishap(self, roll: int, stay_in_career: bool = False) -> CharacterDriver:
        pending = self._find(PendingMishap)
        return self._add(
            Event(fulfills=pending.pending_id, handler=MishapHandler(roll=roll, stay_in_career=stay_in_career))
        )

    def term_event(self, roll: int) -> CharacterDriver:
        pending = self._find(PendingTermEvent)
        return self._add(Event(fulfills=pending.pending_id, handler=TermEventHandler(roll=roll)))

    def commission(self, attempt: bool, roll: int = 0) -> CharacterDriver:
        pending = self._find(PendingCommissionChoice)
        return self._add(Event(fulfills=pending.pending_id, handler=CommissionHandler(attempt=attempt, roll=roll)))

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

    def double_injury_roll(self, roll1: int, roll2: int) -> CharacterDriver:
        pending = self._find(PendingDoubleInjuryRoll)
        return self._add(Event(fulfills=pending.pending_id, handler=DoubleInjuryTableHandler(roll1=roll1, roll2=roll2)))

    def muster_out(self, table: Literal['cash', 'benefits'], roll: int) -> CharacterDriver:
        pending = self._find(PendingMusterOut)
        return self._add(Event(fulfills=pending.pending_id, handler=MusterOutHandler(table=table, roll=roll)))

    def benefit_choice(self, choice_index: int) -> CharacterDriver:
        pending = self._find(PendingBenefitChoice)
        return self._add(Event(fulfills=pending.pending_id, handler=BenefitChoiceHandler(choice_index=choice_index)))

    def name_connection(self, name: str = '', note: str = '') -> CharacterDriver:
        pending = self._find(PendingConnectionName)
        return self._add(
            Event(
                fulfills=pending.pending_id,
                handler=ConnectionNameHandler(
                    connection_index=pending.connection_index,
                    name=name,
                    note=note,
                ),
            )
        )

    def connections_roll(self, count: int) -> CharacterDriver:
        pending = self._find(PendingConnectionsRoll)
        return self._add(
            Event(
                fulfills=pending.pending_id,
                handler=ConnectionsRollHandler(
                    connection_type=pending.connection_type,
                    count=count,
                    origin=pending.origin,
                ),
            )
        )

    def career_choice(self, choice_cls: type[ChoiceBase]) -> CharacterDriver:
        pending = self._find(PendingChoices)
        choice_kind = choice_cls.model_fields['kind'].default
        return self._add(Event(fulfills=pending.pending_id, handler=CareerChoiceHandler(choice=choice_kind)))

    def choose_career_skill(self, skill: AnySkill) -> CharacterDriver:
        pending = self._find(CareerSkillChoicePendingBase)
        return self._add(Event(fulfills=pending.pending_id, handler=SkillChoiceHandler(skill=skill)))

    def choose_advancement_dm(self) -> CharacterDriver:
        pending = self._find(CareerSkillChoicePendingBase)
        return self._add(Event(fulfills=pending.pending_id, handler=AdvancementDmChoiceHandler()))

    def available_career_skill_options(self) -> list[Any]:
        pending = self._find(CareerSkillChoicePendingBase)
        return list(pending.options)

    def choose_skill(self, skill: AnySkill) -> CharacterDriver:
        """Resolve a PendingSkillChoice (e.g. from a mishap or life event)."""
        pending = self._find(PendingSkillChoice)
        return self._add(Event(fulfills=pending.pending_id, handler=SkillChoiceHandler(skill=skill)))

    def choose_characteristic(self, characteristic: Chars, amount: int = 1) -> CharacterDriver:
        """Resolve a PendingCharacteristicChoice (e.g. from a mishap or injury)."""
        pending = self._find(PendingCharacteristicChoice)
        return self._add(
            Event(
                fulfills=pending.pending_id,
                handler=CharacteristicChoiceHandler(characteristic=characteristic, amount=amount),
            )
        )

    def characteristic_choice_options(self) -> list[Chars]:
        """Return the characteristic options from the current PendingCharacteristicChoice."""
        pending = self._find(PendingCharacteristicChoice)
        return list(pending.options)

    def pending_connections_roll_count(self) -> int:
        """Return how many PendingConnectionsRoll items are in the pending queue."""
        return sum(isinstance(p, PendingConnectionsRoll) for p in self.projection.pending_inputs)

    def connections_roll_options(self, kind: ConnectionKind) -> list[int]:
        """Return the dice options of the PendingConnectionsRoll for the given connection kind."""
        pending = next(
            (
                p
                for p in self.projection.pending_inputs
                if isinstance(p, PendingConnectionsRoll) and p.connection_type == kind
            ),
            None,
        )
        if pending is None:
            present = [type(p).__name__ for p in self.projection.pending_inputs]
            raise ValueError(f'No PendingConnectionsRoll for {kind} in pending inputs: {present}')
        return list(pending.options)

    def snapshot(self) -> CharacterProjection:
        """Deep copy the current projection for before/after comparison."""
        return copy.deepcopy(self.projection)

    def skill_roll(self, skill: Any, modified_roll: int) -> CharacterDriver:
        pending = self._find(CareerSkillRollPendingBase)
        return self._add(
            Event(fulfills=pending.pending_id, handler=SkillRollHandler(skill=skill, modified_roll=modified_roll))
        )

    def available_skill_roll_options(self) -> list[Any]:
        pending = self._find(CareerSkillRollPendingBase)
        return pending.options


def projection_diff(before: CharacterProjection, after: CharacterProjection) -> DeepDiff:
    """Compare two projection states using DeepDiff on their JSON representations.

    Use to verify both that expected changes occurred and that nothing unexpected changed.
    All paths in the diff contain the changed key names, so you can check for unexpected
    changes with: ``{p for cat in diff.values() for p in cat} - expected_path_tokens``.
    """
    return DeepDiff(
        before.model_dump(mode='json'),
        after.model_dump(mode='json'),
        ignore_order=True,
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
