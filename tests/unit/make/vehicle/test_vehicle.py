"""The vehicle design object: what a type and a number of Spaces produce.

Rules: refs/vehicle/03_vehicle_design.md, refs/vehicle/02_new_rules.md
"""

from typing import Any

import pytest

from ceres.make.vehicle.size import VehicleSize
from ceres.make.vehicle.speed import SpeedBand
from ceres.make.vehicle.traits import Trait
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


class TestSizing:
    def test_size_comes_from_spaces(self):
        assert a_vehicle(spaces=20).size is VehicleSize.HEAVY
        assert a_vehicle(spaces=6).size is VehicleSize.LIGHT

    def test_a_vehicle_needs_at_least_one_space(self):
        with pytest.raises(ValueError, match='at least one Space'):
            a_vehicle(spaces=0)

    def test_a_vehicle_cannot_be_built_below_its_type_tech_level(self):
        vehicle = a_vehicle(tl=0)
        assert any('TL1' in error for error in vehicle.notes.errors)

    def test_an_illegal_design_still_answers_for_its_performance(self):
        # The design is flagged, not refused: a rule violation is a note, so every
        # property stays answerable and the vehicle can still be rendered. A ground
        # vehicle below TL1 performs as one at TL1, which the table gives as Idle.
        assert a_vehicle(spaces=6, tl=0).speed is SpeedBand.IDLE


class TestStructure:
    """Hull is Spaces x the type's rate; Structure is a tenth of it, rounded up.

    refs/vehicle/02_new_rules.md — "A vehicle's Structure score is one-tenth of
    its Hull value, rounded up."
    """

    def test_hull_is_spaces_times_the_type_rate(self):
        # Ground Vehicle is Hull 2 per Space.
        assert a_vehicle(spaces=20).hull == 40

    def test_structure_is_a_tenth_of_hull_rounded_up(self):
        assert a_vehicle(spaces=20).structure == 4

    def test_structure_rounds_up(self):
        # 9 Spaces x 2 = Hull 18, a tenth of which rounds up to 2.
        assert a_vehicle(spaces=9).structure == 2

    def test_hull_is_never_less_than_one(self):
        # refs/vehicle/03_vehicle_design.md — "a vehicle's Hull cannot be less than 1"
        assert a_vehicle(spaces=1).hull >= 1

    def test_the_smallest_vehicle_still_has_structure(self):
        assert a_vehicle(spaces=1).structure == 1

    def test_hull_is_not_itself_rounded(self):
        # RIV-001: the rules license exactly one rounding, at Structure. A
        # rotorcraft is Hull 0.5 per Space, so 41 Spaces is Hull 20.5 and
        # Structure is a tenth of that rounded up: 2.05 -> 3. Rounding Hull first
        # would give Hull 20 and Structure 2.
        vehicle = a_vehicle(vehicle_type=VehicleType.ROTORCRAFT, spaces=41, tl=12)
        assert vehicle.hull == 20.5
        assert vehicle.structure == 3


class TestShipping:
    """What the vehicle displaces as cargo on a ship."""

    def test_shipping_is_spaces_times_the_type_rate(self):
        # Ground Vehicle ships at 0.5 tons per Space; the published ATV is 20
        # Spaces and 10 tons.
        assert a_vehicle(spaces=20).shipping_tons == 10


class TestCost:
    """Base Cost before features, customisations and options."""

    def test_base_cost_is_spaces_times_the_type_rate(self):
        assert a_vehicle(spaces=20).cost == 20 * 750


class TestPerformance:
    """Speed and Agility, before any customisation."""

    def test_agility_is_the_type_baseline_modified_by_size(self):
        # Ground Vehicle +0, Heavy -1.
        assert a_vehicle(spaces=20).agility == -1

    def test_a_light_vehicle_takes_no_size_penalty(self):
        assert a_vehicle(spaces=6).agility == 0

    def test_speed_is_the_type_speed_at_this_tl_modified_by_size(self):
        # Ground Vehicle at TL12 is Fast; Heavy costs one band.
        assert a_vehicle(spaces=20, tl=12).speed is SpeedBand.HIGH

    def test_a_light_vehicle_keeps_its_type_speed(self):
        assert a_vehicle(spaces=6, tl=12).speed is SpeedBand.FAST

    def test_cruise_is_one_band_below_maximum(self):
        assert a_vehicle(spaces=20, tl=12).cruise_speed is SpeedBand.MEDIUM

    def test_range_is_the_type_range_at_this_tl(self):
        assert a_vehicle(spaces=20, tl=12).range_km == 1000

    def test_a_type_with_no_stated_range_has_none(self):
        # refs/vehicle/04_vehicle_types.md gives the TL1-2 ground vehicle row a
        # Range of '-'. That is an absence of any stated endurance, which is not
        # the same claim as a range of zero kilometres.
        assert a_vehicle(spaces=6, tl=2).range_km is None


class TestTheTypeBaseline:
    """The per-Space figures a Ground Vehicle contributes, seen through a design.

    refs/vehicle/04_vehicle_types.md — Ground Vehicle: Hull 2 per Space,
    Shipping 0.5 tons per Space, Cost Cr750 per Space, Agility +0, TL1.
    """

    def test_one_space_of_ground_vehicle(self):
        vehicle = a_vehicle(spaces=1, tl=1)
        assert vehicle.hull == 2
        assert vehicle.shipping_tons == 0.5
        assert vehicle.cost == 750
        assert vehicle.agility == 0

    def test_a_ground_vehicle_has_no_baseline_traits(self):
        assert a_vehicle(spaces=1, tl=1).traits == ()


class TestPerformanceByTechLevel:
    """Speed and Range improve with technology. Sized Light, so no size penalty.

    refs/vehicle/04_vehicle_types.md — Ground Vehicle TL ladder.
    """

    @pytest.mark.parametrize(
        ('tl', 'speed', 'km'),
        [
            (1, SpeedBand.IDLE, None),
            (2, SpeedBand.IDLE, None),
            (3, SpeedBand.IDLE, 50),
            (4, SpeedBand.VERY_SLOW, 100),
            (5, SpeedBand.SLOW, 300),
            (6, SpeedBand.SLOW, 300),
            (7, SpeedBand.MEDIUM, 500),
            (8, SpeedBand.MEDIUM, 500),
            (9, SpeedBand.HIGH, 800),
            (10, SpeedBand.HIGH, 800),
            (11, SpeedBand.FAST, 1000),
            (15, SpeedBand.FAST, 1000),
        ],
    )
    def test_speed_and_range(self, tl, speed, km):
        vehicle = a_vehicle(spaces=6, tl=tl)
        assert vehicle.speed is speed
        assert vehicle.range_km == km


class TestTraits:
    """Traits arrive from the type and from the size band."""

    def test_a_huge_vehicle_is_unresponsive(self):
        assert Trait.UNRESPONSIVE in a_vehicle(spaces=500).traits

    def test_a_heavy_vehicle_is_not(self):
        assert Trait.UNRESPONSIVE not in a_vehicle(spaces=20).traits
