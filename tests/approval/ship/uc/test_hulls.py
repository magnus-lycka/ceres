"""Approval snapshots for ship hull components.

Hull configuration table values (cost, points, modifiers) are the primary data.
Integration with the Ship model is exercised via validation errors and spec rows.
Pure property tests (computed fields not serialized, bracing scale breakpoints)
live in tests/unit/make/ship/hull/test_standard.py and test_spinext.py.
"""

import pytest

from ceres.make.ship import hull
from ceres.make.ship.drives import DriveSection, JDrive1, MDrive1, RDrive4, SpinExtPlasmaDrive
from ceres.make.ship.ship import Ship
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def _hull_row(config, displacement=100) -> dict:
    return {
        'streamlined': config.streamlined.value,
        'armour_volume_modifier': config.armour_volume_modifier,
        'cost': config.cost(displacement),
        'points': config.points(displacement),
    }


@pytest.mark.approval
def test_hull_configuration_table(snapshot):
    """Table values for all standard hull configurations at 100 tons."""
    snap = AnnotatedSnapshot(
        {
            'standard': _hull_row(hull.standard_hull),
            'streamlined': _hull_row(hull.streamlined_hull),
            'light_streamlined': _hull_row(hull.streamlined_hull.model_copy(update={'light': True})),
            'sphere': _hull_row(hull.sphere),
            'close_structure': _hull_row(hull.close_structure),
            'dispersed_structure': _hull_row(hull.dispersed_structure),
        }
    )
    snap.annotate('light_streamlined_cost_6ton', str(hull.streamlined_hull.model_copy(update={'light': True}).cost(6)))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_spinext_primitive_hull(snapshot):
    """SpinExt primitive hull — base values and drive validation errors."""
    hull_config = hull.SpinExtPrimitiveHull(streamlined=hull.Streamlined.PARTIAL)
    base = Ship(tl=8, displacement=100, hull=hull.Hull(configuration=hull_config))
    tl5 = Ship(tl=5, displacement=100, hull=hull.Hull(configuration=hull_config))
    with_drives = Ship(
        tl=8,
        displacement=100,
        hull=hull.Hull(configuration=hull_config),
        drives=DriveSection(m_drive=MDrive1(), j_drive=JDrive1(), r_drive=RDrive4()),
    )
    plasma_excess = Ship(
        tl=8,
        displacement=100,
        hull=hull.Hull(configuration=hull_config),
        drives=DriveSection(plasma_drive=SpinExtPlasmaDrive(thrust=4)),
    )
    snap = AnnotatedSnapshot(
        {
            'base_hull_cost': base.hull_cost,
            'base_hull_points': base.hull_points,
            'base_power_load': base.basic_hull_power_load,
            'tl5_hull_cost': tl5.hull_cost,
        }
    )
    snap.annotate('base_errors', str(base.notes.errors))
    snap.annotate('with_drives_errors', str(sorted(with_drives.notes.errors)))
    snap.annotate('plasma_excess_errors', str(plasma_excess.notes.errors))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_hull_options(snapshot):
    """Hull options: stealth, reflec, radiation shielding, adjustable hull, breakaway, pressure hull."""
    reflec_ship = Ship(tl=12, displacement=400, hull=hull.Hull(configuration=hull.standard_hull, reflec=True))
    adj12_ship = Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull, adjustable_hull=hull.AdjustableHull(tl=12)),
    )
    adj15_ship = Ship(
        tl=15,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull, adjustable_hull=hull.AdjustableHull(tl=15)),
    )
    breakaway_ship = Ship(
        tl=12,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull.model_copy(update={'breakaway': True})),
    )
    pressure_hull = hull.Hull(configuration=hull.standard_hull, pressure_hull=True)

    reflec_row = reflec_ship.build_spec().row('Reflec', section='Hull')
    adj12_row = adj12_ship.build_spec().row('Adjustable Hull (TL12)', section='Hull')
    adj15_row = adj15_ship.build_spec().row('Adjustable Hull (TL15)', section='Hull')
    breakaway_row = breakaway_ship.build_spec().row('Breakaway Hull Connections', section='Hull')

    snap = AnnotatedSnapshot(
        {
            'reflec_row': {'tons': reflec_row.tons, 'cost': reflec_row.cost, 'infos': reflec_row.notes.infos},
            'adjustable_tl12_row': {'tons': adj12_row.tons, 'cost': adj12_row.cost},
            'adjustable_tl15_row': {'tons': adj15_row.tons, 'cost': adj15_row.cost},
            'breakaway_row': {'tons': breakaway_row.tons, 'cost': breakaway_row.cost},
            'pressure_hull_tons_400': pressure_hull.pressure_hull_tons(400),
            'pressure_hull_total_cost_400': pressure_hull.total_cost(400),
        }
    )
    snap.annotate('reflec_production_cost', str(reflec_ship.expenses.production_cost))
    snap.annotate('adjustable_12_production_cost', str(adj12_ship.expenses.production_cost))
    snap.annotate(
        'reflec_stealth_error',
        str(
            'Reflec cannot be combined with stealth'
            in Ship(
                tl=12,
                displacement=400,
                hull=hull.Hull(configuration=hull.standard_hull, reflec=True, stealth=hull.BasicStealth()),
            ).notes.errors
        ),
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
