"""Approval snapshot for the Poseidon Cargo Boat (TL9, TL10, TL12 variants)."""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL8, FusionPlantTL12, MDrive3, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.storage import FuelSection, OperationFuel
from ceres.make.ship.systems import Aerofins, Airlock, CommonArea
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot

POSEIDON_HULL = hull.streamlined_hull.model_copy(
    update={'light': True, 'description': 'Light Streamlined Hull'},
)


def build_poseidon_cargo_boat(tl: int) -> ship.Ship:
    fusion_plant = FusionPlantTL8(output=50) if tl < 12 else FusionPlantTL12(output=50)
    return ship.Ship(
        ship_class='Poseidon',
        ship_type='Cargo Boat',
        tl=tl,
        displacement=100,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(configuration=POSEIDON_HULL, airlocks=[Airlock()], aerofins=Aerofins()),
        drives=DriveSection(m_drive=MDrive3()),
        power=PowerSection(plant=fusion_plant),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=[Stateroom()], common_area=CommonArea(tons=1.0)),
    )


def build_poseidon_cargo_boat_tl9() -> ship.Ship:
    return build_poseidon_cargo_boat(9)


def build_poseidon_cargo_boat_tl10() -> ship.Ship:
    return build_poseidon_cargo_boat(10)


def build_poseidon_cargo_boat_tl12() -> ship.Ship:
    return build_poseidon_cargo_boat(12)


@pytest.mark.approval
def test_poseidon_cargo_boat_tl9(snapshot):
    snap = AnnotatedSnapshot(build_poseidon_cargo_boat_tl9().build_spec().model_dump(mode='json'))
    snap.annotate('error', 'M-Drive shows "Requires TL10, ship is TL9" — expected error for TL9 variant')
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_poseidon_cargo_boat_tl10(snapshot):
    snap = AnnotatedSnapshot(build_poseidon_cargo_boat_tl10().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_poseidon_cargo_boat_tl12(snapshot):
    snap = AnnotatedSnapshot(build_poseidon_cargo_boat_tl12().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
