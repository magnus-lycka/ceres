"""Approval snapshot for the Botfly Ultralight Fighter.

Source: refs/tycho/BotflyUltralightFighter.txt.

Purpose:
- exercise a 6-ton light streamlined hull with MDrive6, Crystaliron armour,
  BasicStealth, and HighTechnology fixed mount pulse laser
- verify power_basic = 2 per RIS-013 (ceil(6 * 0.2) = 2; reference data uses floor = 1)
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Cockpit, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive6, PowerSection
from ceres.make.ship.parts import EnergyEfficient, HighTechnology
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.storage import FuelSection, OperationFuel
from ceres.make.ship.weapons import FixedMount, PulseLaser, VeryHighYield, WeaponsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_ultralight_fighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Botfly',
        military=True,
        ship_type='Ultralight Fighter',
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull.model_copy(
                update={'light': True, 'description': 'Light Streamlined Hull'},
            ),
            armour=armour.CrystalironArmour(protection=6),
            stealth=hull.BasicStealth(),
        ),
        drives=DriveSection(m_drive=MDrive6()),
        power=PowerSection(plant=FusionPlantTL12(output=8)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
        command=CommandSection(cockpit=Cockpit(holographic=True)),
        computer=ComputerSection(hardware=Computer5()),
        sensors=SensorsSection(primary=CivilianSensors()),
        weapons=WeaponsSection(
            fixed_mounts=[
                FixedMount(
                    weapons=[
                        PulseLaser(
                            customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]),
                        )
                    ]
                ),
            ],
        ),
    )


@pytest.mark.approval
def test_ultralight_fighter(snapshot):
    snap = AnnotatedSnapshot(build_ultralight_fighter().build_spec().model_dump(mode='json'))
    snap.annotate(
        'power_basic',
        'Reference data uses floor(6 * 0.2) = 1; Ceres uses ceil(6 * 0.2) = 2 per RIS-013',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
