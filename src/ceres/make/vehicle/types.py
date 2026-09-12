"""Vehicle types: the baseline every design starts from.

A type is chosen mostly for its locomotion, and fixes the per-Space figures the
rest of the design scales: Hull, shipping tonnage and Cost. It also sets the
performance the vehicle would have at a given Tech Level before Size and
features move it.

Rules: refs/vehicle/04_vehicle_types.md
"""

from bisect import bisect_right
from dataclasses import dataclass
from enum import StrEnum

from .speed import SpeedBand
from .traits import Trait


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
class _TypeEntry:
    """One vehicle type's row of the type tables."""

    tl: int
    skill: str
    agility: int
    hull_per_space: float
    shipping_per_space: float
    cost_per_space: int
    performance: tuple[_Performance, ...]
    allowed_features: frozenset[str]
    traits: tuple[Trait, ...] = ()


class VehicleType(StrEnum):
    """One of the ten vehicle types, including Structure.

    A type is chosen mostly for its locomotion and fixes the per-Space figures a
    design scales: Hull, shipping tonnage and Cost. None of those is a final
    value — features and customisations go on to modify them.

    A design records which type it is; the tables stay here, so a design carries
    only the type's name through JSON.
    """

    GROUND_VEHICLE = 'Ground Vehicle'
    AEROPLANE = 'Aeroplane'
    AIRSHIP = 'Airship'
    GRAV_VEHICLE = 'Grav Vehicle'
    HOVERCRAFT = 'Hovercraft'
    ROTORCRAFT = 'Rotorcraft'
    STRUCTURE = 'Structure'
    SUBMERSIBLE = 'Submersible'
    WALKER = 'Walker'
    WATERCRAFT = 'Watercraft'

    @property
    def _entry(self) -> _TypeEntry:
        return _TYPES[self]

    @property
    def tl(self) -> int:
        """The earliest Tech Level at which this type can be built."""
        return self._entry.tl

    @property
    def skill(self) -> str:
        return self._entry.skill

    @property
    def agility(self) -> int:
        return self._entry.agility

    @property
    def hull_per_space(self) -> float:
        return self._entry.hull_per_space

    @property
    def shipping_per_space(self) -> float:
        return self._entry.shipping_per_space

    @property
    def cost_per_space(self) -> int:
        return self._entry.cost_per_space

    @property
    def traits(self) -> tuple[Trait, ...]:
        return self._entry.traits

    def _performance_at(self, tl: int) -> _Performance:
        # Below the type's own Tech Level there is no row to read, and the design
        # is illegal — but that is reported as an error on the vehicle, not raised
        # here, so the vehicle stays renderable. It performs as the earliest row.
        rows = self._entry.performance
        thresholds = [row.from_tl for row in rows]
        return rows[max(bisect_right(thresholds, tl) - 1, 0)]

    def speed_at(self, tl: int) -> SpeedBand:
        """Maximum Speed Band before Size and features are applied."""
        return self._performance_at(tl).speed

    def range_at(self, tl: int) -> int | None:
        """Range in kilometres before features are applied, or None if unstated."""
        return self._performance_at(tl).km

    def allows(self, feature: str) -> bool:
        return feature in self._entry.allowed_features


_TYPES: dict[VehicleType, _TypeEntry] = {
    VehicleType.GROUND_VEHICLE: _TypeEntry(
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
    ),
    VehicleType.AEROPLANE: _TypeEntry(
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
    ),
    # Shipping is the disassembled figure. An airship is non-rigid by default and
    # is deflated for transport, so an inflated envelope is not what anyone ships
    # (RIV-010). A Rigid airship cannot be compacted and would ship far larger.
    VehicleType.AIRSHIP: _TypeEntry(
        tl=3,
        skill='Flyer (airship)',
        agility=-3,
        hull_per_space=0.2,
        shipping_per_space=0.1,
        cost_per_space=300,
        traits=(Trait.VTOL,),
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
    ),
    VehicleType.GRAV_VEHICLE: _TypeEntry(
        tl=8,
        skill='Flyer (grav)',
        agility=1,
        hull_per_space=2,
        shipping_per_space=0.5,
        cost_per_space=30000,
        traits=(Trait.VTOL,),
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
    ),
    VehicleType.HOVERCRAFT: _TypeEntry(
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
        allowed_features=frozenset(
            {'Agile', 'Fast', 'Open Frame', 'Open-Topped', 'Responsive', 'Slow', 'Unresponsive'}
        ),
    ),
    VehicleType.ROTORCRAFT: _TypeEntry(
        tl=5,
        skill='Flyer (rotor)',
        agility=0,
        hull_per_space=0.5,
        shipping_per_space=1,
        cost_per_space=25000,
        traits=(Trait.VTOL,),
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
    ),
    VehicleType.STRUCTURE: _TypeEntry(
        tl=0,
        skill='n/a',
        agility=-6,
        hull_per_space=1,
        shipping_per_space=0.5,
        cost_per_space=50,
        performance=(_Performance(from_tl=0, speed=SpeedBand.STOPPED, km=0),),
        allowed_features=frozenset({'AFV', 'Open Frame', 'Open-Topped', 'Streamlined'}),
    ),
    VehicleType.SUBMERSIBLE: _TypeEntry(
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
    ),
    VehicleType.WALKER: _TypeEntry(
        tl=8,
        skill='Drive (walker)',
        agility=0,
        hull_per_space=2,
        shipping_per_space=0.5,
        cost_per_space=10000,
        traits=(Trait.ATV,),
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
    ),
    VehicleType.WATERCRAFT: _TypeEntry(
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
    ),
}
