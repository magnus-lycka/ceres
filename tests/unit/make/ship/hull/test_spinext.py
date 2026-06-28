"""Unit tests for SpinExt primitive hull."""

from ceres.make.ship import hull
from ceres.make.ship.drives import DriveSection, RDrive2, SpinExtPlasmaDrive
from ceres.make.ship.ship import Ship


class TestSpinExtPrimitiveHull:
    def test_basic_values(self):
        hull_config = hull.SpinExtPrimitiveHull(streamlined=hull.Streamlined.PARTIAL)
        my_ship = Ship(tl=8, displacement=100, hull=hull.Hull(configuration=hull_config))
        assert hull_config.cost(100) == 1_500_000
        assert hull_config.points(100) == 20
        assert my_ship.hull_cost == 1_500_000
        assert my_ship.hull_points == 20
        assert my_ship.basic_hull_power_load == 1

    def test_tl5_costs_double(self):
        hull_config = hull.SpinExtPrimitiveHull(streamlined=hull.Streamlined.PARTIAL)
        my_ship = Ship(tl=5, displacement=100, hull=hull.Hull(configuration=hull_config))
        assert hull_config.cost(100, tl=5) == 3_000_000
        assert my_ship.hull_cost == 3_000_000

    def test_rejects_reaction_drive_above_thrust_3(self):
        from ceres.make.ship.drives import RDrive4

        my_ship = Ship(
            tl=8,
            displacement=100,
            hull=hull.Hull(configuration=hull.SpinExtPrimitiveHull(streamlined=hull.Streamlined.PARTIAL)),
            drives=DriveSection(r_drive=RDrive4()),
        )
        assert 'Primitive hull cannot support reaction drive Thrust above 3: 4 > 3' in my_ship.notes.errors

    def test_rejects_plasma_thrust_above_3(self):
        my_ship = Ship(
            tl=8,
            displacement=100,
            hull=hull.Hull(configuration=hull.SpinExtPrimitiveHull(streamlined=hull.Streamlined.PARTIAL)),
            drives=DriveSection(plasma_drive=SpinExtPlasmaDrive(thrust=4)),
        )
        assert 'Primitive hull cannot support plasma drive Thrust above 3: 4 > 3' in my_ship.notes.errors

    def test_tl5_rejects_reaction_thrust_above_1(self):
        my_ship = Ship(
            tl=5,
            displacement=100,
            hull=hull.Hull(configuration=hull.SpinExtPrimitiveHull(streamlined=hull.Streamlined.PARTIAL)),
            drives=DriveSection(r_drive=RDrive2()),
        )
        assert 'Primitive TL5 hull cannot support reaction drive Thrust above 1: 2 > 1' in my_ship.notes.errors

    def test_tl5_rejects_plasma_thrust_above_1(self):
        my_ship = Ship(
            tl=5,
            displacement=100,
            hull=hull.Hull(configuration=hull.SpinExtPrimitiveHull(streamlined=hull.Streamlined.PARTIAL)),
            drives=DriveSection(plasma_drive=SpinExtPlasmaDrive(thrust=1.5)),
        )
        assert 'Primitive TL5 hull cannot support plasma drive Thrust above 1: 1.5 > 1' in my_ship.notes.errors
