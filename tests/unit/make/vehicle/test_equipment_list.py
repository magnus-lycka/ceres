"""The EQUIPMENT block: what a design carries, and what that lets it do.

The catalogue prints one alphabetical list naming every customisation and option
installed, followed by a small table of the figures they confer.
"""

from typing import Any

from ceres.make.vehicle.customisations import AquaticDrive, FusionPlusPlant
from ceres.make.vehicle.options import (
    AirLock,
    Autopilot,
    Bunk,
    CollisionProtection,
    ControlSystem,
    SensorSystem,
    VehicleTransceiver,
)
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


class TestEquipmentNames:
    def test_an_option_names_its_quality(self):
        assert a_vehicle(options=[ControlSystem(quality='improved')]).equipment == ['Control System (improved)']

    def test_an_option_without_qualities_is_named_plainly(self):
        assert a_vehicle(options=[AirLock()]).equipment == ['Air Lock']

    def test_several_of_a_thing_are_counted(self):
        assert a_vehicle(options=[Bunk(count=2)]).equipment == ['Bunk x2']

    def test_collision_protection_counts_the_spaces_it_covers(self):
        vehicle = a_vehicle(options=[CollisionProtection(quality='improved', spaces_protected=16)])
        assert vehicle.equipment == ['Collision Protection (improved) x16']

    def test_customisations_are_listed_too(self):
        # The catalogue prints a power plant among the equipment, with its output.
        assert a_vehicle(customisations=[FusionPlusPlant()]).equipment == ['Fusion+ (basic) PP 2']

    def test_the_list_is_alphabetical(self):
        vehicle = a_vehicle(options=[SensorSystem(), AirLock(), ControlSystem()])
        assert vehicle.equipment == ['Air Lock', 'Control System (basic)', 'Sensor System (basic)']

    def test_a_design_with_nothing_installed_lists_nothing(self):
        assert a_vehicle().equipment == []


class TestAquaticDrive:
    """A secondary drive performs as an equivalent watercraft, one band and one
    Agility lower, with a tenth of the range.
    """

    def test_it_reports_the_water_performance_it_confers(self):
        # The published ATV: a TL12 Heavy ground vehicle with an aquatic drive
        # crosses water at Very Slow for 600km.
        from ceres.make.vehicle.features import Feature

        atv = a_vehicle(features=[Feature.FAST], customisations=[AquaticDrive()])
        assert atv.equipment == ['Aquatic Drive (Very Slow, 600km)']


class TestDerivedFigures:
    """The small table beneath the equipment list."""

    def test_it_reports_what_the_fittings_confer(self):
        vehicle = a_vehicle(
            options=[
                Autopilot(quality='basic'),
                SensorSystem(quality='improved'),
                VehicleTransceiver(range_km=500, satellite_uplink=True, tightbeam=True, encryption=True),
            ]
        )
        figures = vehicle.build_spec().derived_figures

        assert figures['Autopilot (skill level)'] == '+0'
        assert figures['Sensors (Electronics (sensors) DM)'] == '+1, 5km'
        assert figures['Communications (range)'] == '500km, tightbeam, satellite uplink, encrypted'

    def test_what_a_design_lacks_shows_as_a_dash(self):
        figures = a_vehicle().build_spec().derived_figures

        assert figures['Autopilot (skill level)'] == '—'
        assert figures['Camouflage (Recon DM)'] == '—'
        assert figures['Stealth (Electronics (sensors) DM)'] == '—'
