"""The EQUIPMENT block: what a design carries, and what that lets it do.

The catalogue prints one alphabetical list naming every customisation and option
installed. The spec carries each item as what it is; the report words the list.
"""

from typing import Any

from ceres.make.vehicle.customisations import AquaticDrive, FusionPlusPlant, SlowerSpeed
from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.grades import Grade
from ceres.make.vehicle.options import (
    AirLock,
    Bunk,
    CollisionProtection,
    ControlSystem,
    SensorSystem,
)
from ceres.make.vehicle.report import _build_context
from ceres.make.vehicle.speed import SpeedBand
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


def printed(vehicle: Vehicle) -> list[str]:
    return _build_context(vehicle.build_spec())['equipment']


class TestEquipmentInTheSpec:
    """Each item as what it is: a name, a grade, how many, and what it does."""

    def test_an_option_carries_its_name_and_grade(self):
        (item,) = a_vehicle(options=[ControlSystem(quality=Grade.IMPROVED)]).build_spec().equipment
        assert (item.name, item.grade, item.quantity) == ('Control System', 'improved', 1)

    def test_a_count_is_a_quantity(self):
        (item,) = a_vehicle(options=[Bunk(count=2)]).build_spec().equipment
        assert (item.name, item.grade, item.quantity) == ('Bunk', None, 2)

    def test_collision_protection_counts_the_spaces_it_covers(self):
        (item,) = (
            a_vehicle(options=[CollisionProtection(quality=Grade.IMPROVED, spaces_protected=16)]).build_spec().equipment
        )
        assert (item.name, item.grade, item.quantity) == ('Collision Protection', 'improved', 16)

    def test_a_power_plant_carries_its_output(self):
        (item,) = a_vehicle(customisations=[FusionPlusPlant()]).build_spec().equipment
        assert (item.name, item.grade, item.power_points) == ('Fusion+', 'basic', 2)

    def test_an_aquatic_drive_carries_the_water_performance_it_confers(self):
        # The published ATV: a TL12 Heavy ground vehicle with Fast crosses water at
        # Very Slow for 600km.
        (item,) = a_vehicle(features=[Feature.FAST], customisations=[AquaticDrive()]).build_spec().equipment
        assert (item.name, item.speed, item.range_km) == ('Aquatic Drive', SpeedBand.VERY_SLOW, 600)

    def test_what_changes_the_vehicle_rather_than_adding_to_it_is_not_equipment(self):
        assert a_vehicle(customisations=[SlowerSpeed()]).build_spec().equipment == []


class TestPrintedEquipment:
    def test_a_grade_is_parenthesised(self):
        assert printed(a_vehicle(options=[ControlSystem(quality=Grade.IMPROVED)])) == ['Control System (improved)']

    def test_an_item_without_a_grade_is_named_plainly(self):
        assert printed(a_vehicle(options=[AirLock()])) == ['Air Lock']

    def test_a_quantity_is_a_multiplier(self):
        assert printed(a_vehicle(options=[Bunk(count=2)])) == ['Bunk x2']
        assert printed(a_vehicle(options=[CollisionProtection(quality=Grade.IMPROVED, spaces_protected=16)])) == [
            'Collision Protection (improved) x16'
        ]

    def test_a_power_plant_prints_its_output(self):
        assert printed(a_vehicle(customisations=[FusionPlusPlant()])) == ['Fusion+ (basic) PP 2']

    def test_an_aquatic_drive_prints_its_water_performance(self):
        vehicle = a_vehicle(features=[Feature.FAST], customisations=[AquaticDrive()])
        assert printed(vehicle) == ['Aquatic Drive (Very Slow, 600km)']

    def test_the_list_is_alphabetical(self):
        vehicle = a_vehicle(options=[SensorSystem(), AirLock(), ControlSystem()])
        assert printed(vehicle) == ['Air Lock', 'Control System (basic)', 'Sensor System (basic)']

    def test_a_design_with_nothing_installed_lists_nothing(self):
        assert printed(a_vehicle()) == []
