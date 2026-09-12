"""Vehicle Size: the band a vehicle's Spaces put it in, and what that costs it.

Rules: refs/vehicle/03_vehicle_design.md — Vehicle Size
"""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class _SizeEntry:
    """One row of the Vehicle Size table."""

    min_spaces: int
    speed_band_modifier: int
    agility_modifier: int
    armour_volume: float
    traits: tuple[str, ...] = ()


class VehicleSize(StrEnum):
    """A vehicle's size band, determined by its Spaces.

    The band sets baseline performance penalties and how much volume a point of
    armour occupies: a small vehicle needs proportionally more armour to cover
    its surface area than a large one does.
    """

    SMALL = 'Small'
    LIGHT = 'Light'
    HEAVY = 'Heavy'
    HUGE = 'Huge'
    MASSIVE = 'Massive'

    @classmethod
    def for_spaces(cls, spaces: int) -> VehicleSize:
        if spaces < 1:
            raise ValueError(f'a vehicle needs at least one Space, got {spaces}')
        # Largest band whose minimum the vehicle reaches.
        return next(size for size in reversed(cls) if spaces >= _SIZES[size].min_spaces)

    @property
    def speed_band_modifier(self) -> int:
        """Speed Bands lost to bulk. Aeroplanes and submersibles are exempt."""
        return _SIZES[self].speed_band_modifier

    @property
    def agility_modifier(self) -> int:
        return _SIZES[self].agility_modifier

    @property
    def armour_volume(self) -> float:
        """Multiplier on the Spaces a point of armour consumes."""
        return _SIZES[self].armour_volume

    @property
    def traits(self) -> tuple[str, ...]:
        return _SIZES[self].traits


# refs/vehicle/03_vehicle_design.md — Vehicle Size table
_SIZES: dict[VehicleSize, _SizeEntry] = {
    VehicleSize.SMALL: _SizeEntry(min_spaces=1, speed_band_modifier=0, agility_modifier=0, armour_volume=4.0),
    VehicleSize.LIGHT: _SizeEntry(min_spaces=4, speed_band_modifier=0, agility_modifier=0, armour_volume=2.0),
    VehicleSize.HEAVY: _SizeEntry(min_spaces=20, speed_band_modifier=-1, agility_modifier=-1, armour_volume=1.0),
    VehicleSize.HUGE: _SizeEntry(
        min_spaces=200, speed_band_modifier=-1, agility_modifier=-2, armour_volume=0.5, traits=('Unresponsive',)
    ),
    VehicleSize.MASSIVE: _SizeEntry(
        min_spaces=2000, speed_band_modifier=-1, agility_modifier=-4, armour_volume=0.5, traits=('Unresponsive',)
    ),
}
