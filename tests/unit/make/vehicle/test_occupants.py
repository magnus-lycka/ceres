"""Crew, passengers, how comfortable they are, and what else fits.

Rules: refs/vehicle/02_new_rules.md — Crew and Passenger Comfort;
refs/vehicle/03_vehicle_design.md — steps 11 and 12.
"""

from ceres.make.vehicle.options import Bunk, EntertainmentSystem, Fresher, Galley
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle
from tests.unit.make.vehicle.helpers import a_vehicle


class TestOccupants:
    """Each occupant is assumed to need one Space."""

    def test_seats_take_a_space_each(self):
        assert a_vehicle(crew=1, passengers=7).occupant_spaces == 8

    def test_they_come_out_of_the_available_spaces(self):
        assert a_vehicle(crew=1, passengers=7).available_spaces == 12

    def test_a_design_with_nobody_aboard_uses_none(self):
        assert a_vehicle().occupant_spaces == 0


class TestCargo:
    """One Space of cargo is a quarter of a displacement ton, about 250kg."""

    def test_cargo_is_a_quarter_ton_per_space(self):
        assert a_vehicle(cargo_spaces=6).cargo_tons == 1.5
        assert a_vehicle(cargo_spaces=1).cargo_tons == 0.25

    def test_it_comes_out_of_the_available_spaces(self):
        assert a_vehicle(cargo_spaces=6).available_spaces == 14


class TestComfort:
    """Comfort Points divided by the occupants they have to serve.

    Each standard seat Space is worth one Comfort Point, and some fittings carry
    their own. Where the result sits on a boundary, the better level applies.
    """

    def test_seats_alone_are_basic_seating(self):
        vehicle = a_vehicle(crew=1, passengers=5)
        assert vehicle.comfort_points == 6
        assert vehicle.comfort_level == 1
        assert vehicle.comfort_label == 'Basic Seating'

    def test_fittings_add_their_comfort_points(self):
        vehicle = a_vehicle(crew=1, passengers=7, options=[Bunk(count=2), Fresher(), Galley()])
        # Eight seats, two bunks, a standard fresher worth two and a mini galley.
        assert vehicle.comfort_points == 13
        assert vehicle.comfort_level == 13 / 8
        assert vehicle.comfort_label == 'Extended Seating'

    def test_a_boundary_takes_the_better_level(self):
        # Exactly 1.5 is the boundary of Long Duration and Extended Seating.
        vehicle = a_vehicle(crew=2, passengers=0, options=[Bunk(count=1)])
        assert vehicle.comfort_level == 1.5
        assert vehicle.comfort_label == 'Extended Seating'

    def test_an_empty_vehicle_has_no_comfort_level(self):
        assert a_vehicle().comfort_level is None
        assert a_vehicle().comfort_label is None


class TestThePublishedDesigns:
    def test_the_atv_is_extended_seating(self):
        atv = a_vehicle(crew=1, passengers=7, options=[Bunk(count=2), Fresher(), Galley()])
        assert atv.comfort_label == 'Extended Seating'
        assert atv.cargo_tons == 0

    def test_the_air_raft_is_basic_seating(self):
        air_raft = Vehicle(
            name='Air/Raft',
            vehicle_type=VehicleType.GRAV_VEHICLE,
            spaces=8,
            tl=8,
            crew=1,
            passengers=5,
            cargo_spaces=1,
            options=[EntertainmentSystem()],
        )
        assert air_raft.comfort_label == 'Basic Seating'
        assert air_raft.cargo_tons == 0.25


class TestFitting:
    """A design cannot spend more Spaces than it has."""

    def test_overspending_spaces_is_an_error(self):
        vehicle = a_vehicle(spaces=4, tl=12, crew=1, passengers=5)
        assert vehicle.available_spaces < 0
        assert any('Space' in error for error in vehicle.notes.errors)

    def test_a_design_that_fits_reports_nothing(self):
        assert a_vehicle(crew=1, passengers=7).notes.errors == []
