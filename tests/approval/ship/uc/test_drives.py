"""Approval snapshots for ship drive components.

Each snapshot captures a group of related drive configurations — their computed
properties (tons, cost, power, tl) are the primary data since those are derived
and not in model_dump. Serialization fidelity (derived values not stored) is
verified via the round_trip annotations.
"""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.drives import (
    DecreasedFuel,
    EarlyJump,
    FusionPlantTL8,
    FusionPlantTL12,
    FusionPlantTL15,
    JDrive1,
    JDrive2,
    JDrive3,
    JDrive4,
    JDrive5,
    JDrive6,
    MDrive1,
    MDrive2,
    MDrive5,
    MDrive6,
    RDrive2,
    RDrive3,
    RDrive4,
    SolarSail,
    SpinExtPlasmaDrive,
    SpinExtPlasmaDriveEnergyEfficient,
    SpinExtPlasmaDriveFuelEfficient,
    SpinExtPlasmaDriveSizeReduction,
    SpinExtSolarSailTL6,
    SpinExtSolarSailTL8,
    SpinExtSolarSailTL12,
    StealthJump,
)
from ceres.make.ship.parts import Advanced, VeryAdvanced
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


class _Ship(ShipBase):
    def __init__(self, tl, displacement, **kwargs):
        super().__init__(tl=tl, displacement=displacement, **kwargs)


def _bound(drive, tl, displacement=200):
    drive.bind(_Ship(tl, displacement))
    return drive


def _drive_row(d) -> dict:
    return {
        'tl': d.tl,
        'tons': round(float(d.tons), 4),
        'cost': round(float(d.cost), 2),
        'power': round(float(d.power), 4),
    }


@pytest.mark.approval
def test_jdrive_table_values(snapshot):
    """JDrive levels 1-6: tl, tons, cost, power for a 200-ton ship."""
    snap = AnnotatedSnapshot(
        {
            'JDrive1': _drive_row(_bound(JDrive1(), 9)),
            'JDrive2': _drive_row(_bound(JDrive2(), 11)),
            'JDrive3': _drive_row(_bound(JDrive3(), 12)),
            'JDrive4': _drive_row(_bound(JDrive4(), 13)),
            'JDrive5': _drive_row(_bound(JDrive5(), 14)),
            'JDrive6': _drive_row(_bound(JDrive6(), 15)),
        }
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_jdrive_customisations(snapshot):
    """JDrive2 with key customisations — VeryAdvanced DecreasedFuel×2, Advanced EarlyJump, VeryAdvanced StealthJump."""
    decreased_fuel = _bound(JDrive2(customisation=VeryAdvanced(modifications=[DecreasedFuel, DecreasedFuel])), 15, 450)
    early_jump = _bound(JDrive2(customisation=Advanced(modifications=[EarlyJump])), 12)
    stealth_jump = _bound(JDrive2(customisation=VeryAdvanced(modifications=[StealthJump])), 13)
    snap = AnnotatedSnapshot(
        {
            'decreased_fuel_x2': _drive_row(decreased_fuel),
            'early_jump': _drive_row(early_jump),
            'stealth_jump': _drive_row(stealth_jump),
        }
    )
    snap.annotate('decreased_fuel_infos', str(decreased_fuel.notes.infos))
    snap.annotate('early_jump_infos', str(early_jump.notes.infos))
    snap.annotate('stealth_jump_infos', str(stealth_jump.notes.infos))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_mdrive_and_fusion_plant(snapshot):
    """MDrive levels 1-6 and FusionPlant variants (TL8, TL12, TL15) for a 200-ton ship."""
    fp8 = _bound(FusionPlantTL8(output=40), 8)
    fp12 = _bound(FusionPlantTL12(output=40), 12)
    fp15 = _bound(FusionPlantTL15(output=40), 15)
    snap = AnnotatedSnapshot(
        {
            'MDrive1': _drive_row(_bound(MDrive1(), 8)),
            'MDrive2': _drive_row(_bound(MDrive2(), 8)),
            'MDrive5': _drive_row(_bound(MDrive5(), 8)),
            'MDrive6': _drive_row(_bound(MDrive6(), 12)),
            'FusionPlantTL8_output40': {
                'tl': fp8.tl,
                'tons': round(float(fp8.tons), 4),
                'cost': round(float(fp8.cost), 2),
            },
            'FusionPlantTL12_output40': {
                'tl': fp12.tl,
                'tons': round(float(fp12.tons), 4),
                'cost': round(float(fp12.cost), 2),
            },
            'FusionPlantTL15_output40': {
                'tl': fp15.tl,
                'tons': round(float(fp15.tons), 4),
                'cost': round(float(fp15.cost), 2),
            },
        }
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_rdrive(snapshot):
    """RDrive levels — reaction drive for non-gravity ships."""
    snap = AnnotatedSnapshot(
        {
            'RDrive2': _drive_row(_bound(RDrive2(), 8)),
            'RDrive3': _drive_row(_bound(RDrive3(), 8)),
            'RDrive4': _drive_row(_bound(RDrive4(), 8)),
        }
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_solar_sail(snapshot):
    """Standard solar sail — tons, cost, power, and operational notes."""
    sail = _bound(SolarSail(), 9)
    snap = AnnotatedSnapshot(
        {
            'tons': round(float(sail.tons), 4),
            'cost': round(float(sail.cost), 2),
            'power': round(float(sail.power), 4),
            'item': sail.build_item(),
        }
    )
    snap.annotate('infos', str(sail.notes.infos))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_spinext_plasma_drive(snapshot):
    """SpinExt plasma drive — base values and all modifications."""
    base = SpinExtPlasmaDrive(thrust=0.5)
    base.bind(_Ship(8, 100))
    all_mods = SpinExtPlasmaDrive(
        thrust=0.5,
        modifications=[
            SpinExtPlasmaDriveEnergyEfficient,
            SpinExtPlasmaDriveFuelEfficient,
            SpinExtPlasmaDriveSizeReduction,
        ],
    )
    all_mods.bind(_Ship(8, 100))
    snap = AnnotatedSnapshot(
        {
            'base': {
                'tons': round(float(base.tons), 4),
                'cost': round(float(base.cost), 2),
                'power': round(float(base.power), 4),
                'fuel_per_hour': round(float(base.fuel_tons_per_hour), 4),
                'item': base.build_item(),
            },
            'with_mods': {
                'tons': round(float(all_mods.tons), 4),
                'cost': round(float(all_mods.cost), 2),
                'power': round(float(all_mods.power), 4),
                'fuel_per_hour': round(float(all_mods.fuel_tons_per_hour), 4),
                'item': all_mods.build_item(),
            },
        }
    )
    snap.annotate('base_infos', str(base.notes.infos))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_spinext_solar_sail(snapshot):
    """SpinExt solar sail table values — TL6, TL8, TL12, with and without solar-panel mode."""
    tl6 = SpinExtSolarSailTL6(tons=10)
    tl8 = SpinExtSolarSailTL8(tons=10)
    tl12 = SpinExtSolarSailTL12(tons=10)
    tl8_panel = SpinExtSolarSailTL8(tons=10, solar_panel_mode=True)
    for sail in [tl6, tl8, tl12, tl8_panel]:
        sail.bind(_Ship(sail.tl, 100))
    snap = AnnotatedSnapshot(
        {
            'TL6': {
                'thrust': round(float(tl6.effective_thrust), 4),
                'cost': round(float(tl6.cost), 2),
                'output': round(float(tl6.output), 4),
            },
            'TL8': {
                'thrust': round(float(tl8.effective_thrust), 4),
                'cost': round(float(tl8.cost), 2),
                'output': round(float(tl8.output), 4),
            },
            'TL12': {
                'thrust': round(float(tl12.effective_thrust), 4),
                'cost': round(float(tl12.cost), 2),
                'output': round(float(tl12.output), 4),
            },
            'TL8_panel_mode': {
                'thrust': round(float(tl8_panel.effective_thrust), 4),
                'cost': round(float(tl8_panel.cost), 2),
                'output': round(float(tl8_panel.output), 4),
            },
        }
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
