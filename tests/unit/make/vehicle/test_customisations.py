"""Customisations: power, speed and range, and the Spaces they cost or free.

Rules: refs/vehicle/06_customisation.md
"""

from ceres.make.vehicle.customisations import (
    FuelCapacity,
    FuelEfficiency,
    FusionPlusPlant,
    SlowerSpeed,
)
from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.speed import SpeedBand
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle
from tests.unit.make.vehicle.helpers import a_vehicle


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


class TestFuelEfficiency:
    """A more or less efficient engine: range for money, at no cost in Spaces.

    Each positive step multiplies Range by a further half, each negative step
    takes away a quarter, and the Cost is a fraction of the vehicle's base.
    """

    def test_two_steps_double_the_range(self):
        assert a_vehicle(customisations=[FuelEfficiency(steps=2)]).range_km == 2000

    def test_one_step_adds_half_again(self):
        assert a_vehicle(customisations=[FuelEfficiency(steps=1)]).range_km == 1500

    def test_a_negative_step_takes_a_quarter_away(self):
        assert a_vehicle(customisations=[FuelEfficiency(steps=-1)]).range_km == 750

    def test_it_costs_a_share_of_the_base(self):
        assert a_vehicle(customisations=[FuelEfficiency(steps=1)]).cost == 15_000 * 1.25
        assert a_vehicle(customisations=[FuelEfficiency(steps=2)]).cost == 15_000 * 1.50
        assert a_vehicle(customisations=[FuelEfficiency(steps=-1)]).cost == 15_000 * 0.90

    def test_it_takes_no_spaces(self):
        assert a_vehicle(customisations=[FuelEfficiency(steps=2)]).available_spaces == 20


class TestFuelCapacity:
    """Bigger or smaller tanks, measured in Spaces.

    Range changes by 2.5 times the share of the vehicle given over to fuel, so a
    tenth of the vehicle is worth the +25% the rules quote. Fuel capacity costs
    Spaces, never money.
    """

    def test_a_tenth_of_the_vehicle_is_a_quarter_more_range(self):
        assert a_vehicle(customisations=[FuelCapacity(spaces=2)]).range_km == 1250

    def test_it_scales_with_the_share_given_over_to_fuel(self):
        assert a_vehicle(customisations=[FuelCapacity(spaces=4)]).range_km == 1500
        assert a_vehicle(customisations=[FuelCapacity(spaces=8)]).range_km == 2000

    def test_taking_fuel_out_gives_spaces_back(self):
        vehicle = a_vehicle(customisations=[FuelCapacity(spaces=-2)])
        assert vehicle.range_km == 750
        assert vehicle.available_spaces == 22

    def test_adding_fuel_consumes_spaces(self):
        assert a_vehicle(customisations=[FuelCapacity(spaces=4)]).available_spaces == 16

    def test_it_never_costs_money(self):
        assert a_vehicle(customisations=[FuelCapacity(spaces=4)]).cost == 15_000


class TestThePublishedDesigns:
    def test_the_atv_range(self):
        atv = a_vehicle(
            features=[Feature.ATV, Feature.FAST],
            customisations=[FusionPlusPlant(), FuelCapacity(spaces=-4), SlowerSpeed()],
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
            # Two steps of efficiency give exactly the published 2,000km. They
            # also add 50% of base Cost, which puts the design well above its
            # published Cr250,000 — see RIV-009.
            customisations=[FuelEfficiency(steps=2)],
        )
        assert air_raft.range_km == 2000
        assert air_raft.cruise_range_km == 3000
        assert air_raft.speed is SpeedBand.HIGH
