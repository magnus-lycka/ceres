"""Vehicle types: the baseline every design starts from.

A type is chosen mostly for its locomotion, and fixes the per-Space figures the
rest of the design scales: Hull, shipping tonnage and Cost. It also sets the
performance the vehicle would have at a given Tech Level before Size and
features move it.

Rules: refs/vehicle/04_vehicle_types.md
"""

from bisect import bisect_right
from dataclasses import dataclass, field

from .speed import SpeedBand


@dataclass(frozen=True)
class _Performance:
    """Speed and Range from a given Tech Level upwards."""

    from_tl: int
    speed: SpeedBand
    km: int


@dataclass(frozen=True)
class VehicleType:
    """One of the ten vehicle types, including Structure.

    `hull_per_space`, `shipping_per_space` and `cost_per_space` are the figures
    a design multiplies by its Spaces; none of them is the vehicle's final
    value, which features and customisations go on to modify.
    """

    name: str
    tl: int
    skill: str
    agility: int
    hull_per_space: float
    shipping_per_space: float
    cost_per_space: int
    performance: tuple[_Performance, ...]
    allowed_features: frozenset[str]
    traits: tuple[str, ...] = ()
    examples: tuple[str, ...] = field(default=())

    def _performance_at(self, tl: int) -> _Performance:
        if tl < self.tl:
            raise ValueError(f'{self.name} requires TL{self.tl}, got TL{tl}')
        thresholds = [row.from_tl for row in self.performance]
        return self.performance[bisect_right(thresholds, tl) - 1]

    def speed_at(self, tl: int) -> SpeedBand:
        """Maximum Speed Band before Size and features are applied."""
        return self._performance_at(tl).speed

    def range_at(self, tl: int) -> int:
        """Range in kilometres before features are applied."""
        return self._performance_at(tl).km

    def allows(self, feature: str) -> bool:
        return feature in self.allowed_features


# refs/vehicle/04_vehicle_types.md — Ground Vehicle
GROUND_VEHICLE = VehicleType(
    name='Ground Vehicle',
    tl=1,
    skill='Drive (varies)',
    agility=0,
    hull_per_space=2,
    shipping_per_space=0.5,
    cost_per_space=750,
    performance=(
        # The TL1-2 row lists no Range at all: such a vehicle moves but has no
        # stated endurance, which is not the same as a Range of zero kilometres.
        _Performance(from_tl=1, speed=SpeedBand.IDLE, km=0),
        _Performance(from_tl=3, speed=SpeedBand.IDLE, km=50),
        _Performance(from_tl=4, speed=SpeedBand.VERY_SLOW, km=100),
        _Performance(from_tl=5, speed=SpeedBand.SLOW, km=300),
        _Performance(from_tl=7, speed=SpeedBand.MEDIUM, km=500),
        _Performance(from_tl=9, speed=SpeedBand.HIGH, km=800),
        _Performance(from_tl=11, speed=SpeedBand.FAST, km=1000),
    ),
    allowed_features=frozenset(
        {
            'AFV',
            'Agile',
            'ATV',
            'Fast',
            'Monowheel',
            'Off-Roader',
            'Open Frame',
            'Open-Topped',
            'Rail Rider',
            'Responsive',
            'Slow',
            'Smart Wheels',
            'Streamlined',
            'Tracks',
            'Tunneller',
            'Unresponsive',
        }
    ),
    examples=('Motorcycle', 'automobile', 'truck', 'tank'),
)
