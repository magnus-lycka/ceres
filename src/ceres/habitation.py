import math
from typing import ClassVar

from .base import CeresModel
from .parts import ShipPart
from .spec import ShipSpec, SpecSection
from .systems import CommonArea


class Staterooms(ShipPart):
    tons_per_stateroom: ClassVar[float] = 4.0
    cost_per_stateroom: ClassVar[float] = 500_000.0
    life_support_per_stateroom: ClassVar[float] = 1_000.0
    occupants_per_stateroom: ClassVar[int] = 2
    life_support_per_occupant: ClassVar[float] = 1_000.0

    count: int

    def compute_tons(self) -> float:
        return self.count * self.tons_per_stateroom

    def compute_cost(self) -> float:
        return self.count * self.cost_per_stateroom

    @property
    def occupancy(self) -> int:
        return self.count * self.occupants_per_stateroom

    @property
    def life_support_cost(self) -> float:
        return self.count * self.life_support_per_stateroom + self.occupancy * self.life_support_per_occupant


class LowBerths(ShipPart):
    tons_per_berth: ClassVar[float] = 0.5
    cost_per_berth: ClassVar[float] = 50_000.0

    count: int

    def compute_tons(self) -> float:
        return self.count * self.tons_per_berth

    def compute_cost(self) -> float:
        return self.count * self.cost_per_berth

    def compute_power(self) -> float:
        return float(math.ceil(self.count / 10))


class HabitationSection(CeresModel):
    staterooms: Staterooms | None = None
    low_berths: LowBerths | None = None
    common_area: CommonArea | None = None

    def validate_common_area(self) -> None:
        if self.staterooms is None:
            return
        recommended_common_area = self.staterooms.tons / 4
        actual_common_area = 0.0 if self.common_area is None else self.common_area.tons
        if actual_common_area < recommended_common_area:
            self.warning(f'Recommended common area is {recommended_common_area:.2f} tons')

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        for part in (self.staterooms, self.low_berths, self.common_area):
            if part is not None:
                parts.append(part)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.staterooms is not None:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.HABITATION,
                    self.staterooms,
                    item='Staterooms' if self.staterooms.count > 1 else 'Stateroom',
                )
            )
            spec.rows_for_section(SpecSection.HABITATION)[-1].quantity = (
                self.staterooms.count if self.staterooms.count > 1 else None
            )
        if self.low_berths is not None:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.HABITATION,
                    self.low_berths,
                    item='Low Berths' if self.low_berths.count > 1 else 'Low Berth',
                )
            )
            spec.rows_for_section(SpecSection.HABITATION)[-1].quantity = (
                self.low_berths.count if self.low_berths.count > 1 else None
            )
        for habitation_part in [part for part in [self.common_area] if part is not None]:
            spec.add_row(ship._spec_row_for_part(SpecSection.HABITATION, habitation_part))
        habitation_rows = spec.rows_for_section(SpecSection.HABITATION)
        if habitation_rows:
            habitation_rows[-1].notes.extend(ship._display_notes(self))
