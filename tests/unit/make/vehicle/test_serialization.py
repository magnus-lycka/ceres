"""A vehicle design must survive a trip through JSON unchanged.

docs/ARCHITECTURE.md — "A complete design must serialize to JSON and deserialize
back to a functionally identical" design: same structure, same types, same field
values. Designs are stored, transferred and rendered from their JSON.
"""

from ceres.make.vehicle.customisations import FuelCapacity, FusionPlusPlant, SlowerSpeed
from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def test_a_design_roundtrips_through_json():
    original = Vehicle(name='Test ATV', vehicle_type=VehicleType.GROUND_VEHICLE, spaces=20, tl=12)

    restored = Vehicle.model_validate_json(original.model_dump_json())

    assert restored == original


def test_a_restored_design_derives_the_same_figures():
    original = Vehicle(name='Sky Dirge', vehicle_type=VehicleType.AIRSHIP, spaces=128, tl=12)

    restored = Vehicle.model_validate_json(original.model_dump_json())

    assert restored.hull == original.hull
    assert restored.structure == original.structure
    assert restored.speed is original.speed
    assert restored.shipping_tons == original.shipping_tons


def test_the_type_is_named_in_the_json_not_inlined():
    # The type table is reference data, not part of a design's identity: a design
    # records which type it is, and the table stays in code.
    payload = Vehicle(name='Air/Raft', vehicle_type=VehicleType.GRAV_VEHICLE, spaces=8, tl=10).model_dump()

    assert payload['vehicle_type'] == 'Grav Vehicle'


def test_features_and_customisations_survive_the_trip():
    original = Vehicle(
        name='ATV',
        vehicle_type=VehicleType.GROUND_VEHICLE,
        spaces=20,
        tl=12,
        features=[Feature.ATV, Feature.FAST],
        customisations=[FusionPlusPlant(), FuelCapacity(spaces=-4), SlowerSpeed()],
    )

    restored = Vehicle.model_validate_json(original.model_dump_json())

    assert restored == original
    assert restored.range_km == original.range_km
    assert restored.available_spaces == original.available_spaces
    # The union resolves back to the concrete customisation types, not the base.
    assert isinstance(restored.customisations[0], FusionPlusPlant)


def test_mounts_survive_the_trip():
    from ceres.make.vehicle.armour import Face
    from ceres.make.vehicle.mounts import Turret

    original = Vehicle(
        name='ATV',
        vehicle_type=VehicleType.GROUND_VEHICLE,
        spaces=20,
        tl=12,
        mounts=[Turret(face=Face.DORSAL, weapon_spaces=4)],
    )

    restored = Vehicle.model_validate_json(original.model_dump_json())

    assert restored == original
    assert isinstance(restored.mounts[0], Turret)
    assert restored.cost == original.cost


def test_options_survive_the_trip():
    # An installed option knows its vehicle; comparing designs must not follow
    # that reference back round in a circle.
    from ceres.make.vehicle.options import ControlSystem

    original = Vehicle(
        name='ATV',
        vehicle_type=VehicleType.GROUND_VEHICLE,
        spaces=20,
        tl=12,
        options=[ControlSystem(quality='improved')],
    )

    restored = Vehicle.model_validate_json(original.model_dump_json())

    assert restored == original
    assert restored.agility == original.agility
