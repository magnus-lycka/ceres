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
    """Speed and Range from a given Tech Level upwards.

    `km` is None where the source states no Range at all, which is an absence of
    stated endurance rather than a range of zero.
    """

    from_tl: int
    speed: SpeedBand
    km: int | None


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
        # Below the type's own Tech Level there is no row to read, and the design
        # is illegal — but that is reported as an error on the vehicle, not raised
        # here, so the vehicle stays renderable. It performs as the earliest row.
        thresholds = [row.from_tl for row in self.performance]
        return self.performance[max(bisect_right(thresholds, tl) - 1, 0)]

    def speed_at(self, tl: int) -> SpeedBand:
        """Maximum Speed Band before Size and features are applied."""
        return self._performance_at(tl).speed

    def range_at(self, tl: int) -> int | None:
        """Range in kilometres before features are applied, or None if unstated."""
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
        _Performance(from_tl=1, speed=SpeedBand.IDLE, km=None),
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


# refs/vehicle/04_vehicle_types.md — Aeroplane
AEROPLANE = VehicleType(
    name='Aeroplane',
    tl=4,
    skill='Flyer (wing)',
    agility=1,
    hull_per_space=0.5,
    shipping_per_space=1,
    cost_per_space=15000,
    performance=(
        _Performance(from_tl=4, speed=SpeedBand.MEDIUM, km=300),
        _Performance(from_tl=5, speed=SpeedBand.HIGH, km=600),
        _Performance(from_tl=7, speed=SpeedBand.FAST, km=1200),
        _Performance(from_tl=9, speed=SpeedBand.VERY_FAST, km=2400),
        _Performance(from_tl=11, speed=SpeedBand.VERY_FAST, km=4800),
    ),
    allowed_features=frozenset(
        {
            'Agile',
            'Fast',
            'Floats',
            'Folding Wings',
            'Hypersonic',
            'Jet Engines',
            'Open Frame',
            'Open-Topped',
            'Responsive',
            'Slow',
            'STOL',
            'Supersonic',
            'Tilt Engines',
            'Unresponsive',
        }
    ),
    examples=('Light aircraft', 'bomber', 'transport'),
)

# refs/vehicle/04_vehicle_types.md — Airship
# Shipping is 0.1 tons per Space disassembled, 0.5 assembled; the assembled
# figure is the one a ship must find room for.
AIRSHIP = VehicleType(
    name='Airship',
    tl=3,
    skill='Flyer (airship)',
    agility=-3,
    hull_per_space=0.2,
    shipping_per_space=0.5,
    cost_per_space=300,
    traits=('VTOL',),
    performance=(
        # The TL3 row is an unpowered balloon, whose speed and range are dictated
        # by atmospheric conditions rather than the vehicle.
        _Performance(from_tl=3, speed=SpeedBand.IDLE, km=100),
        _Performance(from_tl=4, speed=SpeedBand.SLOW, km=4000),
        _Performance(from_tl=5, speed=SpeedBand.MEDIUM, km=6000),
        _Performance(from_tl=8, speed=SpeedBand.MEDIUM, km=8000),
        _Performance(from_tl=10, speed=SpeedBand.MEDIUM, km=12000),
        _Performance(from_tl=12, speed=SpeedBand.MEDIUM, km=18000),
    ),
    allowed_features=frozenset(
        {'Agile', 'Fast', 'Open Frame', 'Responsive', 'Rigid', 'Slow', 'Streamlined', 'Unresponsive'}
    ),
    examples=('Balloon', 'blimp', 'zeppelin'),
)

# refs/vehicle/04_vehicle_types.md — Grav Vehicle
GRAV_VEHICLE = VehicleType(
    name='Grav Vehicle',
    tl=8,
    skill='Flyer (grav)',
    agility=1,
    hull_per_space=2,
    shipping_per_space=0.5,
    cost_per_space=30000,
    traits=('VTOL',),
    performance=(
        _Performance(from_tl=8, speed=SpeedBand.HIGH, km=1000),
        _Performance(from_tl=9, speed=SpeedBand.FAST, km=2000),
        _Performance(from_tl=11, speed=SpeedBand.FAST, km=3000),
        _Performance(from_tl=13, speed=SpeedBand.VERY_FAST, km=4000),
        _Performance(from_tl=15, speed=SpeedBand.VERY_FAST, km=5000),
    ),
    allowed_features=frozenset(
        {
            'AFV',
            'Agile',
            'Fast',
            'Open Frame',
            'Open-Topped',
            'Responsive',
            'Slow',
            'Streamlined',
            'Unresponsive',
        }
    ),
    examples=('G/bike', 'air/raft', 'G/carrier'),
)

# refs/vehicle/04_vehicle_types.md — Hovercraft
HOVERCRAFT = VehicleType(
    name='Hovercraft',
    tl=5,
    skill='Drive (hovercraft)',
    agility=1,
    hull_per_space=0.5,
    shipping_per_space=0.5,
    cost_per_space=10000,
    performance=(
        _Performance(from_tl=5, speed=SpeedBand.SLOW, km=300),
        _Performance(from_tl=6, speed=SpeedBand.MEDIUM, km=400),
        _Performance(from_tl=8, speed=SpeedBand.HIGH, km=500),
        _Performance(from_tl=10, speed=SpeedBand.HIGH, km=600),
        _Performance(from_tl=12, speed=SpeedBand.FAST, km=800),
    ),
    allowed_features=frozenset({'Agile', 'Fast', 'Open Frame', 'Open-Topped', 'Responsive', 'Slow', 'Unresponsive'}),
    examples=('Hover jeep', 'landing craft', 'ferry'),
)

# refs/vehicle/04_vehicle_types.md — Rotorcraft
ROTORCRAFT = VehicleType(
    name='Rotorcraft',
    tl=5,
    skill='Flyer (rotor)',
    agility=0,
    hull_per_space=0.5,
    shipping_per_space=1,
    cost_per_space=25000,
    traits=('VTOL',),
    performance=(
        _Performance(from_tl=5, speed=SpeedBand.MEDIUM, km=500),
        _Performance(from_tl=7, speed=SpeedBand.HIGH, km=1000),
        _Performance(from_tl=8, speed=SpeedBand.HIGH, km=2000),
        _Performance(from_tl=11, speed=SpeedBand.FAST, km=4000),
    ),
    allowed_features=frozenset(
        {
            'Aerodyne',
            'Agile',
            'Fast',
            'Floats',
            'Folding Wings',
            'Open Frame',
            'Open-Topped',
            'Ornithopter',
            'Responsive',
            'Slow',
            'Streamlined',
            'Unresponsive',
        }
    ),
    examples=('Helicopter', 'aerodyne', 'ornithopter'),
)

# refs/vehicle/04_vehicle_types.md — Structure
# Not a vehicle: stationary, and its Agility applies only if it later installs
# some form of auxiliary locomotion.
STRUCTURE = VehicleType(
    name='Structure',
    tl=0,
    skill='n/a',
    agility=-6,
    hull_per_space=1,
    shipping_per_space=0.5,
    cost_per_space=50,
    performance=(_Performance(from_tl=0, speed=SpeedBand.STOPPED, km=0),),
    allowed_features=frozenset({'AFV', 'Open Frame', 'Open-Topped', 'Streamlined'}),
    examples=('House', 'fortress', 'outpost', 'rocket stage'),
)

# refs/vehicle/04_vehicle_types.md — Submersible
SUBMERSIBLE = VehicleType(
    name='Submersible',
    tl=4,
    skill='Seafarer (submarine)',
    agility=-2,
    hull_per_space=3,
    shipping_per_space=0.5,
    cost_per_space=50000,
    performance=(
        _Performance(from_tl=4, speed=SpeedBand.IDLE, km=50),
        _Performance(from_tl=5, speed=SpeedBand.VERY_SLOW, km=100),
        _Performance(from_tl=6, speed=SpeedBand.SLOW, km=150),
        _Performance(from_tl=9, speed=SpeedBand.SLOW, km=200),
        _Performance(from_tl=12, speed=SpeedBand.MEDIUM, km=300),
        _Performance(from_tl=15, speed=SpeedBand.HIGH, km=500),
    ),
    allowed_features=frozenset(
        {
            'AFV',
            'Agile',
            'Fast',
            'Open Frame',
            'Open-Topped',
            'Responsive',
            'Slow',
            'Tunneller',
            'Unresponsive',
        }
    ),
    examples=('Submarine', 'diving bell'),
)

# refs/vehicle/04_vehicle_types.md — Walker
WALKER = VehicleType(
    name='Walker',
    tl=8,
    skill='Drive (walker)',
    agility=0,
    hull_per_space=2,
    shipping_per_space=0.5,
    cost_per_space=10000,
    traits=('ATV',),
    performance=(
        _Performance(from_tl=8, speed=SpeedBand.VERY_SLOW, km=150),
        _Performance(from_tl=9, speed=SpeedBand.SLOW, km=300),
        _Performance(from_tl=11, speed=SpeedBand.MEDIUM, km=450),
        _Performance(from_tl=13, speed=SpeedBand.HIGH, km=600),
        _Performance(from_tl=15, speed=SpeedBand.HIGH, km=750),
    ),
    allowed_features=frozenset(
        {
            'AFV',
            'Agile',
            'Fast',
            'Multi-Legged',
            'Open Frame',
            'Open-Topped',
            'Responsive',
            'Slow',
            'Tunneller',
            'Unresponsive',
        }
    ),
    examples=('Load lifter', 'AT-AT'),
)

# refs/vehicle/04_vehicle_types.md — Watercraft
WATERCRAFT = VehicleType(
    name='Watercraft',
    tl=0,
    skill='Seafarer (varies)',
    agility=-2,
    hull_per_space=2,
    shipping_per_space=0.5,
    cost_per_space=2000,
    performance=(
        _Performance(from_tl=0, speed=SpeedBand.IDLE, km=0),
        _Performance(from_tl=3, speed=SpeedBand.IDLE, km=100),
        _Performance(from_tl=4, speed=SpeedBand.VERY_SLOW, km=200),
        _Performance(from_tl=5, speed=SpeedBand.VERY_SLOW, km=400),
        _Performance(from_tl=6, speed=SpeedBand.SLOW, km=600),
        _Performance(from_tl=8, speed=SpeedBand.SLOW, km=800),
        _Performance(from_tl=12, speed=SpeedBand.MEDIUM, km=1200),
    ),
    allowed_features=frozenset(
        {
            'AFV',
            'Agile',
            'Fast',
            'Floats',
            'Hydrofoil',
            'Open Frame',
            'Open-Topped',
            'Responsive',
            'Slow',
            'Unresponsive',
        }
    ),
    examples=('Canoe', 'speedboat', 'sailboat', 'tanker'),
)
