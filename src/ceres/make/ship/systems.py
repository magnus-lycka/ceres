from math import ceil
from typing import Annotated, ClassVar, Literal, TypeVar

from pydantic import ConfigDict, Field

from ceres.shared import CeresModel, NoteList, _Note

from .base import ShipBase
from .parts import ShipPart
from .spec import ShipSpec, SpecSection
from .text import optional_count

_T = TypeVar('_T', bound=ShipPart)


class _ZeroPowerSystemPart(ShipPart):
    power: ClassVar[float]

    @property
    def power(self) -> float:
        return 0.0


class _ExplicitTonsSystemPart(ShipPart):
    tons: ClassVar[float]
    base_tons: float = Field(0.0, alias='tons')
    model_config = ConfigDict(frozen=True, populate_by_name=True, serialize_by_alias=True)

    @property
    def tons(self) -> float:
        return self.base_tons


class Workshop(_ZeroPowerSystemPart):
    system_type: Literal['WORKSHOP'] = 'WORKSHOP'
    description: Literal['Workshop'] = 'Workshop'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 6.0

    @property
    def cost(self) -> float:
        return 900_000.0


class Laboratory(_ZeroPowerSystemPart):
    system_type: Literal['LABORATORY'] = 'LABORATORY'
    description: Literal['Laboratory'] = 'Laboratory'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        return 1_000_000.0


class LibraryFacility(_ZeroPowerSystemPart):
    system_type: Literal['LIBRARY'] = 'LIBRARY'
    description: Literal['Library'] = 'Library'
    tl: int = 8
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        return 4_000_000.0


class BriefingRoom(_ZeroPowerSystemPart):
    system_type: Literal['BRIEFING_ROOM'] = 'BRIEFING_ROOM'
    description: Literal['Briefing Room'] = 'Briefing Room'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        return 500_000.0


class CommandBridge(_ZeroPowerSystemPart):
    system_type: Literal['COMMAND_BRIDGE'] = 'COMMAND_BRIDGE'
    description: Literal['Command Bridge'] = 'Command Bridge'
    tons: ClassVar[float]
    cost: ClassVar[float]

    def bind(self, assembly: ShipBase) -> None:
        super().bind(assembly)
        if self.assembly.displacement <= 5_000:
            self.error('Command bridge requires displacement greater than 5000 tons')

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +1 to Tactics (naval) checks made within the command bridge')
        return notes

    @property
    def tons(self) -> float:
        return 40.0

    @property
    def cost(self) -> float:
        return 30_000_000.0

    @property
    def tactics_naval_dm(self) -> int:
        return 1


class Armoury(_ZeroPowerSystemPart):
    system_type: Literal['ARMOURY'] = 'ARMOURY'
    description: Literal['Armoury'] = 'Armoury'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 250_000.0


class GravScreen(ShipPart):
    system_type: Literal['GRAV_SCREEN'] = 'GRAV_SCREEN'
    description: Literal['Grav Screen'] = 'Grav Screen'
    tl: int = 12
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Blocks densitometers; the presence of a grav screen is obvious to sensor operators')
        return notes

    @property
    def tons(self) -> float:
        return float(ceil(self.assembly.displacement / 200))

    @property
    def cost(self) -> float:
        return self.tons * 1_000_000.0

    @property
    def power(self) -> float:
        return self.tons * 2.0


class CommonArea(_ExplicitTonsSystemPart):
    description: Literal['Common Area'] = 'Common Area'
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 100_000.0

    @property
    def power(self) -> float:
        return 0.0


class CommercialZone(_ExplicitTonsSystemPart):
    system_type: Literal['COMMERCIAL_ZONE'] = 'COMMERCIAL_ZONE'
    description: Literal['Commercial Zone'] = 'Commercial Zone'
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0

    @property
    def power(self) -> float:
        return float(max(1, int(self.tons // 200)))


class SwimmingPool(CommonArea):
    description: Literal['Swimming Pool'] = 'Swimming Pool'

    @property
    def cost(self) -> float:
        return self.tons * 20_000.0


class Theatre(CommonArea):
    description: Literal['Theatre'] = 'Theatre'
    advanced: bool = False

    @property
    def cost(self) -> float:
        if self.advanced:
            return self.tons * 200_000.0
        return self.tons * 100_000.0


class WetBar(_ZeroPowerSystemPart):
    description: Literal['Wet Bar'] = 'Wet Bar'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return 2_000.0


class HotTub(CommonArea):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    base_tons: float = Field(0.0, alias='tons', exclude=True)
    users: int = 1

    def item_description(self) -> str:
        label = 'User' if self.users == 1 else 'Users'
        return f'Hot Tub ({self.users} {label})'

    @property
    def tons(self) -> float:
        return self.users * 0.25

    @property
    def cost(self) -> float:
        return self.tons * 12_000.0

    @property
    def power(self) -> float:
        return 0.0


class BasicAutodoc(CeresModel):
    description: Literal['Basic Autodoc'] = 'Basic Autodoc'

    @property
    def cost(self) -> float:
        return 100_000.0


class MedicalBay(ShipPart):
    system_type: Literal['MEDICAL_BAY'] = 'MEDICAL_BAY'
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    autodoc: BasicAutodoc | None = None

    def item_description(self) -> str:
        if self.autodoc is not None:
            return 'Medical Bay, Basic Autodoc'
        return 'Medical Bay'

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        cost = 2_000_000.0
        if self.autodoc is not None:
            cost += self.autodoc.cost
        return cost

    @property
    def power(self) -> float:
        return 1.0


class Biosphere(_ExplicitTonsSystemPart):
    system_type: Literal['BIOSPHERE'] = 'BIOSPHERE'
    description: Literal['Biosphere'] = 'Biosphere'
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0

    @property
    def power(self) -> float:
        return self.tons


class Airlock(_ZeroPowerSystemPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    size: float = 2.0

    def item_description(self) -> str:
        return f'Airlock ({self.size:g} tons)'

    def am_i_for_free(self) -> bool:
        if self.assembly.displacement < 100:
            return False
        free_airlocks = self.assembly.displacement // 100
        hull = self.assembly.hull
        if hull is None:
            return False
        siblings = hull.airlocks
        index = next((i for i, sibling in enumerate(siblings) if sibling is self), -1)
        if index < 0:
            return False
        return index < free_airlocks

    @property
    def tons(self) -> float:
        if self.am_i_for_free():
            return 0.0
        return max(self.size, 2.0)

    @property
    def cost(self) -> float:
        if self.am_i_for_free():
            return 0.0
        return self.tons * 100_000.0


class Aerofins(_ZeroPowerSystemPart):
    description: Literal['Aerofins'] = 'Aerofins'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def atmospheric_pilot_dm(self) -> int:
        return 2

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +2 to Pilot checks in atmosphere')
        return notes

    @property
    def tons(self) -> float:
        return self.assembly.displacement * 0.05

    @property
    def cost(self) -> float:
        return self.tons * 100_000.0


class ProbeDrones(_ZeroPowerSystemPart):
    drone_type: Literal['PROBE_DRONES'] = 'PROBE_DRONES'
    tl: int = 9
    tons: ClassVar[float]
    cost: ClassVar[float]
    drones_per_ton: ClassVar[int] = 5
    cost_per_ton: ClassVar[float] = 500_000.0
    count: int

    def item_description(self) -> str:
        if self.count == 1:
            return 'Probe Drone'
        return 'Probe Drones'

    @property
    def tons(self) -> float:
        return self.count / self.drones_per_ton

    @property
    def cost(self) -> float:
        return (self.count / self.drones_per_ton) * self.cost_per_ton


class AdvancedProbeDrones(ProbeDrones):
    drone_type: Literal['ADVANCED_PROBE_DRONES'] = 'ADVANCED_PROBE_DRONES'
    tl: int = 12
    cost_per_ton: ClassVar[float] = 800_000.0

    def item_description(self) -> str:
        if self.count == 1:
            return 'Advanced Probe Drone'
        return 'Advanced Probe Drones'


class RepairDrones(_ZeroPowerSystemPart):
    """Repair drones: 1 ton per 100 tons of displacement, Cr200,000 per ton."""

    drone_type: Literal['REPAIR_DRONES'] = 'REPAIR_DRONES'
    description: Literal['Repair Drones'] = 'Repair Drones'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return self.assembly.displacement / 100

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0


class MiningDrones(_ZeroPowerSystemPart):
    drone_type: Literal['MINING_DRONES'] = 'MINING_DRONES'
    tons: ClassVar[float]
    cost: ClassVar[float]
    count: int

    def item_description(self) -> str:
        if self.count == 1:
            return 'Mining Drone'
        return 'Mining Drones'

    @property
    def tons(self) -> float:
        return self.count * 2.0

    @property
    def cost(self) -> float:
        return self.count * 200_000.0


class TrainingFacility(_ZeroPowerSystemPart):
    system_type: Literal['TRAINING_FACILITY'] = 'TRAINING_FACILITY'
    tons: ClassVar[float]
    cost: ClassVar[float]
    trainees: int

    def item_description(self) -> str:
        return f'Training Facility: {self.trainees}-person capacity'

    @property
    def tons(self) -> float:
        return self.trainees * 2.0

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0


class UNREPSystem(_ExplicitTonsSystemPart):
    system_type: Literal['UNREP_SYSTEM'] = 'UNREP_SYSTEM'
    cost: ClassVar[float]
    power: ClassVar[float]

    def item_description(self) -> str:
        return f'UNREP System ({self.transfer_rate:g} tons/hour)'

    @property
    def transfer_rate(self) -> float:
        return self.tons * 20

    @property
    def cost(self) -> float:
        return self.tons * 500_000.0

    @property
    def power(self) -> float:
        return self.tons


class TowCable(_ZeroPowerSystemPart):
    system_type: Literal['TOW_CABLE'] = 'TOW_CABLE'
    tl: int = 7
    description: Literal['Tow Cable'] = 'Tow Cable'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return self.assembly.displacement * 0.01

    @property
    def cost(self) -> float:
        return self.assembly.displacement * 0.01 * 5_000


class GrapplingArm(_ZeroPowerSystemPart):
    system_type: Literal['GRAPPLING_ARM'] = 'GRAPPLING_ARM'
    tl: int = 9
    description: Literal['Grappling Arm'] = 'Grappling Arm'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 2.0

    @property
    def cost(self) -> float:
        return 1_000_000.0


class AccelerationSeat(_ZeroPowerSystemPart):
    system_type: Literal['ACCELERATION_SEAT'] = 'ACCELERATION_SEAT'
    tl: int = 1
    description: Literal['Acceleration Seat'] = 'Acceleration Seat'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 0.5

    @property
    def cost(self) -> float:
        return 30_000.0


type AnyDroneSystem = Annotated[
    ProbeDrones | AdvancedProbeDrones | RepairDrones | MiningDrones,
    Field(discriminator='drone_type'),
]

type AnyInternalSystem = Annotated[
    Armoury
    | Biosphere
    | CommercialZone
    | MedicalBay
    | Laboratory
    | LibraryFacility
    | BriefingRoom
    | CommandBridge
    | GravScreen
    | TrainingFacility
    | UNREPSystem
    | Workshop
    | TowCable
    | GrapplingArm
    | AccelerationSeat,
    Field(discriminator='system_type'),
]


class SystemsSection(CeresModel):
    internal_systems: list[AnyInternalSystem] = Field(default_factory=list)
    drones: list[AnyDroneSystem] = Field(default_factory=list)

    def internal_systems_of_type(self, system_cls: type[_T]) -> list[_T]:
        return [system for system in self.internal_systems if isinstance(system, system_cls)]

    @property
    def armouries(self) -> list[Armoury]:
        return self.internal_systems_of_type(Armoury)

    @property
    def biospheres(self) -> list[Biosphere]:
        return self.internal_systems_of_type(Biosphere)

    @property
    def commercial_zones(self) -> list[CommercialZone]:
        return self.internal_systems_of_type(CommercialZone)

    @property
    def medical_bays(self) -> list[MedicalBay]:
        return self.internal_systems_of_type(MedicalBay)

    @property
    def laboratories(self) -> list[Laboratory]:
        return self.internal_systems_of_type(Laboratory)

    @property
    def libraries(self) -> list[LibraryFacility]:
        return self.internal_systems_of_type(LibraryFacility)

    @property
    def briefing_rooms(self) -> list[BriefingRoom]:
        return self.internal_systems_of_type(BriefingRoom)

    @property
    def command_bridges(self) -> list[CommandBridge]:
        return self.internal_systems_of_type(CommandBridge)

    @property
    def training_facilities(self) -> list[TrainingFacility]:
        return self.internal_systems_of_type(TrainingFacility)

    @property
    def workshops(self) -> list[Workshop]:
        return self.internal_systems_of_type(Workshop)

    def _all_parts(self) -> list[ShipPart]:
        return [*self.internal_systems, *self.drones]

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for row in ship._grouped_spec_rows(SpecSection.SYSTEMS, self.internal_systems):
            spec.add_row(row)
        for drone in self.drones:
            spec.add_row(ship._spec_row_for_part(SpecSection.SYSTEMS, drone))
            if isinstance(drone, ProbeDrones | MiningDrones):
                spec.rows_for_section(SpecSection.SYSTEMS)[-1].quantity = optional_count(drone.count)
