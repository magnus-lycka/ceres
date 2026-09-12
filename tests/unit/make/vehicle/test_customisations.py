"""Customisations: power, speed and range, and the Spaces they cost or free.

Rules: refs/vehicle/06_customisation.md
"""

from typing import Any

from ceres.make.vehicle.customisations import DecreasedFuel, FusionPlusPlant, IncreasedEfficiency, SlowerSpeed
from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.speed import SpeedBand
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


class TestFusionPlus:
    """refs/vehicle/06_customisation.md — Fusion+ Power: basic is TL10, 10% of
    Spaces with a minimum of one, Range x5, Cr15000 per power plant Space.
    """

    def test_it_multiplies_range(self):
        assert a_vehicle(customisations=[FusionPlusPlant()]).range_km == 5000

    def test_it_consumes_a_tenth_of_the_vehicle(self):
        # 20 Spaces leaves 18 once the plant takes 2.
        assert a_vehicle(customisations=[FusionPlusPlant()]).available_spaces == 18

    def test_it_always_takes_at_least_one_space(self):
        assert a_vehicle(spaces=4, tl=12, customisations=[FusionPlusPlant()]).available_spaces == 3

    def test_it_costs_by_the_space_it_occupies(self):
        # 2 Spaces of plant at Cr15000 each, on top of the Cr15,000 base.
        assert a_vehicle(customisations=[FusionPlusPlant()]).cost == 15_000 + 30_000


class TestSpeedModification:
    """refs/vehicle/06_customisation.md — Slower: -1 band, +10% Spaces rounded
    down, -10% of base Cost.
    """

    def test_it_drops_a_speed_band(self):
        assert a_vehicle(customisations=[SlowerSpeed()]).speed is SpeedBand.MEDIUM

    def test_it_frees_spaces(self):
        assert a_vehicle(customisations=[SlowerSpeed()]).available_spaces == 22

    def test_it_reduces_cost_against_the_base(self):
        assert a_vehicle(customisations=[SlowerSpeed()]).cost == 15_000 * 0.90


class TestRangeModification:
    """Fuel percentages are summed and then applied to the Range already adjusted
    by features and power plants.
    """

    def test_increased_efficiency_adds_half_again_each_time(self):
        assert a_vehicle(customisations=[IncreasedEfficiency(steps=2)]).range_km == 2000

    def test_decreased_fuel_cuts_range_and_frees_spaces(self):
        vehicle = a_vehicle(customisations=[DecreasedFuel(steps=2)])
        assert vehicle.range_km == 500
        assert vehicle.available_spaces == 24

    def test_fuel_percentages_apply_after_features_and_power(self):
        # 1,000 base, halved by Fast, times five for Fusion+, then -50% fuel.
        vehicle = a_vehicle(
            features=[Feature.FAST],
            customisations=[FusionPlusPlant(), DecreasedFuel(steps=2)],
        )
        assert vehicle.range_km == 1250


class TestThePublishedDesigns:
    def test_the_atv_range(self):
        atv = a_vehicle(
            features=[Feature.ATV, Feature.FAST],
            customisations=[FusionPlusPlant(), DecreasedFuel(steps=2), SlowerSpeed()],
        )
        assert atv.range_km == 1250
        assert atv.cruise_range_km == 1875
        assert atv.speed is SpeedBand.HIGH
        assert atv.cruise_speed is SpeedBand.MEDIUM

    def test_the_air_raft_range(self):
        air_raft = Vehicle(
            name='Air/Raft',
            vehicle_type=VehicleType.GRAV_VEHICLE,
            spaces=8,
            tl=8,
            features=[Feature.OPEN_TOPPED],
            customisations=[IncreasedEfficiency(steps=2)],
        )
        assert air_raft.range_km == 2000
        assert air_raft.cruise_range_km == 3000
        assert air_raft.speed is SpeedBand.HIGH
