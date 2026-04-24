from math import ceil
from typing import ClassVar

from .base import CeresModel, Note, NoteCategory
from .parts import ShipPart
from .spec import ShipSpec, SpecSection
from .text import optional_count


class Workshop(ShipPart):
    def build_item(self) -> str | None:
        return 'Workshop'

    def compute_tons(self) -> float:
        return 6.0

    def compute_cost(self) -> float:
        return 900_000.0


class Laboratory(ShipPart):
    def build_item(self) -> str | None:
        return 'Laboratory'

    def compute_tons(self) -> float:
        return 4.0

    def compute_cost(self) -> float:
        return 1_000_000.0


class BriefingRoom(ShipPart):
    def build_item(self) -> str | None:
        return 'Briefing Room'

    def compute_tons(self) -> float:
        return 4.0

    def compute_cost(self) -> float:
        return 500_000.0


class CrewArmory(ShipPart):
    capacity: int

    def build_item(self) -> str | None:
        return f'Crew Armory: Supports {self.capacity} Crew'

    def compute_tons(self) -> float:
        return self.capacity / 25

    def compute_cost(self) -> float:
        return self.compute_tons() * 250_000.0


class CommonArea(ShipPart):
    tons: float

    def build_item(self) -> str | None:
        return 'Common Area'

    def compute_cost(self) -> float:
        return self.tons * 100_000.0


class CommercialZone(ShipPart):
    tons: float

    def build_item(self) -> str | None:
        return 'Commercial Zone'

    def compute_cost(self) -> float:
        return self.tons * 200_000.0

    def compute_power(self) -> float:
        return float(max(1, int(self.tons // 200)))


class SwimmingPool(ShipPart):
    tons: float

    def build_item(self) -> str | None:
        return 'Swimming Pool'

    def compute_cost(self) -> float:
        return self.tons * 20_000.0


class Theatre(ShipPart):
    tons: float
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


class BasicAutodoc(CeresModel):
    def build_item(self) -> str | None:
        return 'Basic Autodoc'

    @property
    def cost(self) -> float:
        return 100_000.0


class MedicalBay(ShipPart):
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


class MedicalBays(ShipPart):
    count: int

    def build_item(self) -> str | None:
        return 'Medical Bays'

    def compute_tons(self) -> float:
        return self.count * 4.0

    def compute_cost(self) -> float:
        return self.count * 2_000_000.0

    def compute_power(self) -> float:
        return float(self.count)


class Biosphere(ShipPart):
    tons: float

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
        free_airlocks = ceil(self.ship.displacement / 100)
        siblings = self.ship.parts_of_type(Airlock)
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

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='DM +2 to Pilot checks in atmosphere')]

    def compute_tons(self) -> float:
        return self.ship.displacement * 0.05

    def compute_cost(self) -> float:
        return self.compute_tons() * 100_000.0


class ProbeDrones(ShipPart):
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


class RepairDrones(ShipPart):
    """Repair drones: 1 ton per 100 tons of displacement, Cr200,000 per ton."""

    def build_item(self) -> str | None:
        return 'Repair Drones'

    def compute_tons(self) -> float:
        return self.ship.displacement / 100

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0


class TrainingFacility(ShipPart):
    trainees: int

    def build_item(self) -> str | None:
        return f'Training Facility: {self.trainees}-person capacity'

    def compute_tons(self) -> float:
        return self.trainees * 2.0

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0


class SystemsSection(CeresModel):
    crew_armory: CrewArmory | None = None
    biosphere: Biosphere | None = None
    commercial_zone: CommercialZone | None = None
    medical_bay: MedicalBay | None = None
    medical_bays: MedicalBays | None = None
    laboratory: Laboratory | None = None
    briefing_room: BriefingRoom | None = None
    probe_drones: ProbeDrones | None = None
    repair_drones: RepairDrones | None = None
    training_facility: TrainingFacility | None = None
    workshop: Workshop | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        for part in (
            self.crew_armory,
            self.biosphere,
            self.commercial_zone,
            self.workshop,
            self.medical_bay,
            self.medical_bays,
            self.laboratory,
            self.briefing_room,
            self.probe_drones,
            self.repair_drones,
            self.training_facility,
        ):
            if part is not None:
                parts.append(part)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for system_part in self._all_parts():
            spec.add_row(ship._spec_row_for_part(SpecSection.SYSTEMS, system_part))
            if isinstance(system_part, ProbeDrones):
                spec.rows_for_section(SpecSection.SYSTEMS)[-1].quantity = optional_count(system_part.count)
