from typing import Annotated, TypeVar

from pydantic import Field

from ceres.shared import CeresModel

from ..parts import ShipPart
from ..spec import ShipSpec, SpecSection
from ..text import optional_count
from .acceleration import AccelerationBench, AccelerationSeat
from .access import BreachingTube, ForcedLinkageApparatus
from .advanced import GravityWellGenerator, GravScreen, JumpFilter
from .command import BriefingRoom, CommandBridge
from .common_areas import (
    Brewery,
    CommercialZone,
    GourmetKitchen,
    MultiEnvironmentSpace,
    ZeroGRoom,
)
from .drones import AdvancedProbeDrones, MiningDrones, ProbeDrones, RepairDrones
from .external import GrapplingArm, HolographicHull, TowCable
from .facilities import ConstructionDeck, Laboratory, LibraryFacility, TrainingFacility, Workshop
from .logistics import UNREPSystem
from .medical import Biosphere, MedicalBay
from .reentry import (
    AssaultReEntryCapsule,
    BasicReEntryCapsule,
    HighSurvivabilityReEntryCapsule,
    ReEntryPod,
)
from .security import AdvancedPsionicShielding, Armoury, PsionicShielding, Vault

_T = TypeVar('_T', bound=ShipPart)


type AnyDroneSystem = Annotated[
    ProbeDrones | AdvancedProbeDrones | RepairDrones | MiningDrones,
    Field(discriminator='drone_type'),
]

type AnyInternalSystem = Annotated[
    Armoury
    | Biosphere
    | CommercialZone
    | MultiEnvironmentSpace
    | Vault
    | MedicalBay
    | Laboratory
    | LibraryFacility
    | BriefingRoom
    | CommandBridge
    | ConstructionDeck
    | GravScreen
    | GravityWellGenerator
    | JumpFilter
    | PsionicShielding
    | AdvancedPsionicShielding
    | TrainingFacility
    | UNREPSystem
    | Workshop
    | TowCable
    | GrapplingArm
    | HolographicHull
    | BreachingTube
    | ForcedLinkageApparatus
    | Brewery
    | GourmetKitchen
    | ZeroGRoom
    | AccelerationBench
    | AccelerationSeat
    | BasicReEntryCapsule
    | AssaultReEntryCapsule
    | HighSurvivabilityReEntryCapsule
    | ReEntryPod,
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
