from typing import Annotated, ClassVar, Literal, TypeVar

from pydantic import Field

from .base import CeresModel, NoteList, _Note
from .parts import ShipPart
from .spec import ShipSpec, SpecSection
from .text import optional_count

_T = TypeVar('_T', bound=ShipPart)


class Workshop(ShipPart):
    system_type: Literal['WORKSHOP'] = 'WORKSHOP'

    def build_item(self) -> str | None:
        return 'Workshop'

    def compute_tons(self) -> float:
        return 6.0

    def compute_cost(self) -> float:
        return 900_000.0


class Laboratory(ShipPart):
    system_type: Literal['LABORATORY'] = 'LABORATORY'

    def build_item(self) -> str | None:
        return 'Laboratory'

    def compute_tons(self) -> float:
        return 4.0

    def compute_cost(self) -> float:
        return 1_000_000.0


class LibraryFacility(ShipPart):
    system_type: Literal['LIBRARY'] = 'LIBRARY'
    tl: int = 8

    def build_item(self) -> str | None:
        return 'Library'

    def compute_tons(self) -> float:
        return 4.0

    def compute_cost(self) -> float:
        return 4_000_000.0


class BriefingRoom(ShipPart):
    system_type: Literal['BRIEFING_ROOM'] = 'BRIEFING_ROOM'

    def build_item(self) -> str | None:
        return 'Briefing Room'

    def compute_tons(self) -> float:
        return 4.0

    def compute_cost(self) -> float:
        return 500_000.0


class Armoury(ShipPart):
    system_type: Literal['ARMOURY'] = 'ARMOURY'

    def build_item(self) -> str | None:
        return 'Armoury'

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 250_000.0


class CommonArea(ShipPart):
    def build_item(self) -> str | None:
        return 'Common Area'

    def compute_cost(self) -> float:
        return self.tons * 100_000.0


class CommercialZone(ShipPart):
    system_type: Literal['COMMERCIAL_ZONE'] = 'COMMERCIAL_ZONE'

    def build_item(self) -> str | None:
        return 'Commercial Zone'

    def compute_cost(self) -> float:
        return self.tons * 200_000.0

    def compute_power(self) -> float:
        return float(max(1, int(self.tons // 200)))


class SwimmingPool(CommonArea):
    def build_item(self) -> str | None:
        return 'Swimming Pool'

    def compute_cost(self) -> float:
        return self.tons * 20_000.0


class Theatre(CommonArea):
    advanced: bool = False

    def build_item(self) -> str | None:
        return 'Theatre'

    def compute_cost(self) -> float:
        if self.advanced:
            return self.tons * 200_000.0
        return self.tons * 100_000.0


class WetBar(ShipPart):
    def build_item(self) -> str | None:
        return 'Wet Bar'

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return 2_000.0


class HotTub(CommonArea):
    users: int = 1

    def build_item(self) -> str | None:
        label = 'User' if self.users == 1 else 'Users'
        return f'Hot Tub ({self.users} {label})'

    def compute_tons(self) -> float:
        return self.users * 0.25

    def compute_cost(self) -> float:
        return self.compute_tons() * 12_000.0


class BasicAutodoc(CeresModel):
    def build_item(self) -> str | None:
        return 'Basic Autodoc'

    @property
    def cost(self) -> float:
        return 100_000.0


class MedicalBay(ShipPart):
    system_type: Literal['MEDICAL_BAY'] = 'MEDICAL_BAY'
    autodoc: BasicAutodoc | None = None

    def build_item(self) -> str | None:
        if self.autodoc is not None:
            return 'Medical Bay, Basic Autodoc'
        return 'Medical Bay'

    def compute_tons(self) -> float:
        return 4.0

    def compute_cost(self) -> float:
        cost = 2_000_000.0
        if self.autodoc is not None:
            cost += self.autodoc.cost
        return cost

    def compute_power(self) -> float:
        return 1.0


class Biosphere(ShipPart):
    system_type: Literal['BIOSPHERE'] = 'BIOSPHERE'

    def build_item(self) -> str | None:
        return 'Biosphere'

    def compute_cost(self) -> float:
        return self.tons * 200_000.0

    def compute_power(self) -> float:
        return self.tons


class Airlock(ShipPart):
    size: float = 2.0

    def build_item(self) -> str | None:
        return f'Airlock ({self.size:g} tons)'

    def am_i_for_free(self) -> bool:
        if self.assembly.displacement < 100:
            return False
        free_airlocks = self.assembly.displacement // 100
        siblings = self.assembly.parts_of_type(Airlock)
        index = next((i for i, sibling in enumerate(siblings) if sibling is self), -1)
        if index < 0:
            return False
        return index < free_airlocks

    def compute_tons(self) -> float:
        if self.am_i_for_free():
            return 0.0
        return max(self.size, 2.0)

    def compute_cost(self) -> float:
        if self.am_i_for_free():
            return 0.0
        return self.compute_tons() * 100_000.0


class Aerofins(ShipPart):
    @property
    def atmospheric_pilot_dm(self) -> int:
        return 2

    def build_item(self) -> str | None:
        return 'Aerofins'

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +2 to Pilot checks in atmosphere')
        return notes

    def compute_tons(self) -> float:
        return self.assembly.displacement * 0.05

    def compute_cost(self) -> float:
        return self.compute_tons() * 100_000.0


class ProbeDrones(ShipPart):
    drone_type: Literal['PROBE_DRONES'] = 'PROBE_DRONES'
    tl: int = 9
    drones_per_ton: ClassVar[int] = 5
    cost_per_ton: ClassVar[float] = 500_000.0
    count: int

    def build_item(self) -> str | None:
        if self.count == 1:
            return 'Probe Drone'
        return 'Probe Drones'

    def compute_tons(self) -> float:
        return self.count / self.drones_per_ton

    def compute_cost(self) -> float:
        return (self.count / self.drones_per_ton) * self.cost_per_ton


class AdvancedProbeDrones(ProbeDrones):
    drone_type: Literal['ADVANCED_PROBE_DRONES'] = 'ADVANCED_PROBE_DRONES'
    tl: int = 12
    cost_per_ton: ClassVar[float] = 800_000.0

    def build_item(self) -> str | None:
        if self.count == 1:
            return 'Advanced Probe Drone'
        return 'Advanced Probe Drones'


class RepairDrones(ShipPart):
    """Repair drones: 1 ton per 100 tons of displacement, Cr200,000 per ton."""

    drone_type: Literal['REPAIR_DRONES'] = 'REPAIR_DRONES'

    def build_item(self) -> str | None:
        return 'Repair Drones'

    def compute_tons(self) -> float:
        return self.assembly.displacement / 100

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0


class MiningDrones(ShipPart):
    drone_type: Literal['MINING_DRONES'] = 'MINING_DRONES'
    count: int

    def build_item(self) -> str | None:
        if self.count == 1:
            return 'Mining Drone'
        return 'Mining Drones'

    def compute_tons(self) -> float:
        return self.count * 2.0

    def compute_cost(self) -> float:
        return self.count * 200_000.0


class TrainingFacility(ShipPart):
    system_type: Literal['TRAINING_FACILITY'] = 'TRAINING_FACILITY'
    trainees: int

    def build_item(self) -> str | None:
        return f'Training Facility: {self.trainees}-person capacity'

    def compute_tons(self) -> float:
        return self.trainees * 2.0

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0


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
    | TrainingFacility
    | Workshop,
    Field(discriminator='system_type'),
]


class SystemsSection(CeresModel):
    internal_systems: list[AnyInternalSystem] = Field(default_factory=list)
    drones: list[AnyDroneSystem] = Field(default_factory=list)

    def internal_systems_of_type(self, system_cls: type[_T]) -> list[_T]:
        return [system for system in self.internal_systems if isinstance(system, system_cls)]

    def first_internal_system_of_type(self, system_cls: type[_T]) -> _T | None:
        matches = self.internal_systems_of_type(system_cls)
        return None if not matches else matches[0]

    @property
    def armouries(self) -> list[Armoury]:
        return self.internal_systems_of_type(Armoury)

    @property
    def biosphere(self) -> Biosphere | None:
        return self.first_internal_system_of_type(Biosphere)

    @property
    def commercial_zone(self) -> CommercialZone | None:
        return self.first_internal_system_of_type(CommercialZone)

    @property
    def medical_bay(self) -> MedicalBay | None:
        return self.first_internal_system_of_type(MedicalBay)

    @property
    def medical_bays(self) -> list[MedicalBay]:
        return self.internal_systems_of_type(MedicalBay)

    @property
    def laboratories(self) -> list[Laboratory]:
        return self.internal_systems_of_type(Laboratory)

    @property
    def library(self) -> LibraryFacility | None:
        return self.first_internal_system_of_type(LibraryFacility)

    @property
    def briefing_room(self) -> BriefingRoom | None:
        return self.first_internal_system_of_type(BriefingRoom)

    @property
    def training_facility(self) -> TrainingFacility | None:
        return self.first_internal_system_of_type(TrainingFacility)

    @property
    def workshop(self) -> Workshop | None:
        return self.first_internal_system_of_type(Workshop)

    def _all_parts(self) -> list[ShipPart]:
        return [*self.internal_systems, *self.drones]

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for row in ship._grouped_spec_rows(SpecSection.SYSTEMS, self.internal_systems):
            spec.add_row(row)
        for drone in self.drones:
            spec.add_row(ship._spec_row_for_part(SpecSection.SYSTEMS, drone))
            if isinstance(drone, ProbeDrones | MiningDrones):
                spec.rows_for_section(SpecSection.SYSTEMS)[-1].quantity = optional_count(drone.count)
