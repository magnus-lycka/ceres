"""Rendering a design: the context that reaches the template.

The stat block's paired figures — 'High (Medium)' — and its formatted Cost are
composed here, not carried by the spec.
"""

from typing import Any

from ceres.make.vehicle.armour import Face
from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.mounts import Turret
from ceres.make.vehicle.report import _build_context, render_vehicle_pdf, render_vehicle_typst
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


def rows(vehicle: Vehicle) -> dict[str, str]:
    return {row['label']: row['value'] for row in _build_context(vehicle.build_spec())['stats']}


class TestTypeLine:
    def test_it_reads_as_the_catalogue_prints_it(self):
        context = _build_context(a_vehicle().build_spec())
        assert context['type_line'] == 'Heavy Ground Vehicle (20 Spaces, DM+2 to hit)'

    def test_features_and_traits_are_one_line(self):
        context = _build_context(a_vehicle(features=[Feature.ATV, Feature.FAST]).build_spec())
        assert context['features_and_traits'] == 'ATV, Fast'

    def test_a_design_with_neither_says_so(self):
        context = _build_context(a_vehicle(spaces=6, tl=7).build_spec())
        assert context['features_and_traits'] == 'None'


class TestStatRows:
    def test_speed_pairs_maximum_with_cruise(self):
        assert rows(a_vehicle())['SPEED (CRUISE)'] == 'High (Medium)'

    def test_range_pairs_and_is_grouped(self):
        assert rows(a_vehicle())['RANGE (CRUISE)'] == '1,000 (1,500)'

    def test_a_design_with_no_range_shows_a_dash(self):
        assert rows(a_vehicle(spaces=6, tl=2))['RANGE (CRUISE)'] == '—'

    def test_agility_is_signed(self):
        assert rows(a_vehicle())['AGILITY'] == '-1'
        assert rows(a_vehicle(spaces=6))['AGILITY'] == '+0'

    def test_cost_is_credits(self):
        assert rows(a_vehicle())['COST'] == 'Cr15,000'

    def test_shipping_drops_a_pointless_decimal(self):
        assert rows(a_vehicle())['SHIPPING'] == '10 tons'
        assert rows(a_vehicle(spaces=3))['SHIPPING'] == '1.5 tons'


class TestArmourTable:
    def test_each_face_pairs_protection_with_the_small_arms_figure(self):
        # The ATV at TL12 prints 6 (18) on every face.
        armour = _build_context(a_vehicle().build_spec())['armour']

        assert [row['face'] for row in armour] == ['Forward', 'Port', 'Dorsal', 'Aft', 'Starboard', 'Ventral']
        assert {row['value'] for row in armour} == {'6 (18)'}

    def test_a_lower_tech_design_prints_its_own_figures(self):
        # The Air/Raft at TL8 prints 3 (11).
        armour = _build_context(a_vehicle(vehicle_type=VehicleType.GRAV_VEHICLE, spaces=8, tl=8).build_spec())['armour']

        assert {row['value'] for row in armour} == {'3 (11)'}


class TestOpenToppedArmour:
    def test_the_open_top_prints_as_a_dash(self):
        # refs/vehicle/26_wehicle_catalogue.md — the Gecko, Grav Chair and
        # Gunskiff, all Open-Topped, print "Dorsal —".
        vehicle = a_vehicle(vehicle_type=VehicleType.GRAV_VEHICLE, spaces=8, tl=8, features=[Feature.OPEN_TOPPED])
        rows = {row['face']: row['value'] for row in _build_context(vehicle.build_spec())['armour']}
        assert rows['Dorsal'] == '—'
        assert rows['Forward'] == '3 (11)'


class TestWeaponsTable:
    """refs/vehicle/26_wehicle_catalogue.md — the ATV prints an empty turret as
    "Turret: Dorsal, can hold 4 Spaces of weapons", every other column a dash.
    """

    def test_an_empty_turret_reads_as_the_catalogue_prints_it(self):
        (row,) = _build_context(a_vehicle(mounts=[Turret(face=Face.DORSAL, weapon_spaces=4)]).build_spec())['weapons']
        assert row['weapon'] == 'Turret: Dorsal, can hold 4 Spaces of weapons'
        assert [row[column] for column in ('range', 'damage', 'magazine', 'cost', 'traits', 'fire_control')] == [
            '—'
        ] * 6

    def test_a_design_without_weapons_has_no_table(self):
        assert _build_context(a_vehicle().build_spec())['weapons'] == []


class TestTypstOutput:
    def test_it_renders_the_design(self):
        source = render_vehicle_typst(a_vehicle(name='Test ATV', features=[Feature.ATV]))

        assert 'TEST ATV' in source
        assert 'Heavy Ground Vehicle' in source
        assert 'STRUCTURE' in source

    def test_the_template_compiles_to_a_pdf(self):
        # The Typst source can be well-formed and still fail to typeset, so this
        # is the only check that the template itself is valid.
        pdf = render_vehicle_pdf(a_vehicle(name='Test ATV', features=[Feature.ATV]))

        assert pdf.startswith(b'%PDF-')

    def test_a_design_with_a_turret_still_typesets(self):
        # The Typst source embeds the whole context, so asserting text in it
        # proves nothing about what the template prints. This only guards the
        # template's handling of weapons data against typesetting errors.
        vehicle = a_vehicle(name='Test ATV', mounts=[Turret(face=Face.DORSAL, weapon_spaces=4)])
        assert render_vehicle_pdf(vehicle).startswith(b'%PDF-')
