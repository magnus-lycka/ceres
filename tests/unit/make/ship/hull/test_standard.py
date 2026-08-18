"""Unit tests for hull configuration computed properties."""

import pytest

from ceres.make.ship import hull, hull as hull_module
from ceres.make.ship.base import ShipBase
from ceres.make.ship.ship import Ship
from ceres.make.ship.spec import ShipSpec, SpecRow
from ceres.make.ship.systems import Aerofins, Airlock


class _Ship(ShipBase):
    hull: hull_module.Hull | None = None

    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


class _SpecShip:
    displacement = 100
    hull_cost = 5_000_000.0
    basic_hull_power_load = -20.0

    def __init__(self, bulkheads=None):
        self._bulkheads = [] if bulkheads is None else bulkheads

    def _item_text(self, part, fallback):
        return part.item_description() or fallback

    def _display_notes(self, part):
        return part.notes

    def _spec_row_for_part(self, section, part):
        return SpecRow(section=section, item=f'part:{type(part).__name__}')

    def _grouped_spec_rows(self, section, parts):
        return [SpecRow(section=section, item=f'group:{type(part).__name__}') for part in parts]

    def armoured_bulkhead_parts(self):
        return self._bulkheads


class TestMassiveShipHullPoints:
    def test_large_ship_bracing_scale_starts_at_25000_tons(self):
        assert hull.standard_hull.points(24_999) == 9_999
        assert hull.standard_hull.points(25_000) == 12_500

    def test_capital_ship_bracing_scale_starts_at_100000_tons(self):
        assert hull.standard_hull.points(99_999) == 49_999
        assert hull.standard_hull.points(100_000) == 66_666

    def test_reinforced_modifier_preserved_at_large_scale(self):
        assert hull.standard_hull.model_copy(update={'reinforced': True}).points(25_000) == 13_750

    def test_light_modifier_preserved_at_capital_scale(self):
        assert hull.standard_hull.model_copy(update={'light': True}).points(100_000) == 60_000


class TestArmouredBulkheadSerialization:
    def test_computed_properties_not_in_dump(self):
        bulkhead = hull.ArmouredBulkhead.model_validate(
            {'protected_tonnage': 30.0, 'protected_item': 'M-Drive', 'tons': 999, 'cost': 999, 'power': 999}
        )
        bulkhead.bind(_Ship(12, 100))
        dump = bulkhead.model_dump()
        assert bulkhead.tons == 3.0
        assert bulkhead.cost == 600_000
        assert bulkhead.power == 0.0
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump

    def test_default_item_and_warning_notes(self):
        bulkhead = hull.ArmouredBulkhead(protected_tonnage=20.0)

        assert bulkhead.item_description() == 'Armoured Bulkhead'
        assert 'Critical hit severity reduced by 1 if critical hit severity >1' in bulkhead.notes.infos
        assert 'Prefer armoured_bulkhead=True on the protected part over manual ArmouredBulkhead' in (
            bulkhead.notes.warnings
        )

    def test_bulkhead_created_from_ship_part_omits_manual_warning(self):
        bulkhead = hull.ArmouredBulkhead(protected_tonnage=20.0, from_ship_part=True)

        assert 'Prefer armoured_bulkhead=True on the protected part over manual ArmouredBulkhead' not in (
            bulkhead.notes.warnings
        )


class TestStealthSerialization:
    def test_computed_properties_not_in_dump(self):
        stealth = hull.BasicStealth.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        stealth.bind(_Ship(12, 100))
        dump = stealth.model_dump()
        assert stealth.tons == 2.0
        assert stealth.cost == 4_000_000
        assert stealth.power == 0.0
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestHullConfigurationCosts:
    def test_cost_modifiers_combine_without_losing_non_gravity_discount_boundary(self):
        configuration = hull.standard_hull.model_copy(
            update={
                'hull_cost_modifier': 2.0,
                'reinforced': True,
                'light': True,
                'military': True,
                'non_gravity': True,
            }
        )

        assert configuration.hull_cost_modifier_without_non_gravity() == pytest.approx(2.8125)
        assert configuration.effective_hull_cost_modifier == pytest.approx(1.40625)
        assert configuration.cost(100) == pytest.approx(7_031_250)

    def test_automation_basis_cost_excludes_non_gravity_discount(self):
        configuration = hull.standard_hull.model_copy(update={'non_gravity': True})

        assert configuration.cost(100) == 2_500_000
        assert configuration.automation_basis_cost(100) == 5_000_000


class TestAdjustableHull:
    def test_tl12_adjustable_hull_uses_larger_tonnage_and_tenth_hull_cost(self):
        ship = _Ship(tl=12, displacement=100)
        ship.hull = hull.Hull(configuration=hull.standard_hull)
        adjustable_hull = hull.AdjustableHull(tl=12)

        adjustable_hull.bind(ship)

        assert adjustable_hull.tons == 5.0
        assert adjustable_hull.cost == 500_000
        assert adjustable_hull.power == 0.0
        assert adjustable_hull.item_description() == 'Adjustable Hull (TL12)'
        assert 'All weapons have pop-up mountings at no additional cost' in adjustable_hull.notes.infos

    def test_tl15_adjustable_hull_uses_smaller_tonnage_and_full_hull_cost(self):
        ship = _Ship(tl=15, displacement=100)
        ship.hull = hull.Hull(configuration=hull.standard_hull)
        adjustable_hull = hull.AdjustableHull(tl=15)

        adjustable_hull.bind(ship)

        assert adjustable_hull.tons == 1.0
        assert adjustable_hull.cost == 5_000_000

    def test_adjustable_hull_without_bound_hull_has_no_cost(self):
        adjustable_hull = hull.AdjustableHull(tl=12)

        adjustable_hull.bind(_Ship(tl=12, displacement=100))

        assert adjustable_hull.cost == 0.0


class TestHullValidation:
    def test_hull_cannot_be_both_reinforced_and_light(self):
        my_ship = Ship(
            tl=12,
            displacement=100,
            hull=hull.Hull(configuration=hull.standard_hull.model_copy(update={'reinforced': True, 'light': True})),
        )
        assert 'Hull cannot be both reinforced and light' in my_ship.notes.errors

    def test_military_hull_requires_capital_ship_displacement(self):
        my_ship = Ship(
            tl=14,
            displacement=5_000,
            hull=hull.Hull(configuration=hull.standard_hull.model_copy(update={'military': True})),
        )
        assert 'Military hull requires capital ship displacement: 5,000 <= 5,000 tons' in my_ship.notes.errors

    def test_military_hull_allowed_above_five_thousand_tons(self):
        my_ship = Ship(
            tl=14,
            displacement=5_001,
            hull=hull.Hull(configuration=hull.standard_hull.model_copy(update={'military': True})),
        )
        assert 'Military hull requires capital ship displacement' not in '\n'.join(my_ship.notes.errors)


class TestHull:
    def test_cost_helpers_return_zero_when_option_absent(self):
        ship_hull = hull.Hull(configuration=hull.standard_hull)

        assert ship_hull.radiation_shielding_cost(100) == 0.0
        assert ship_hull.reflec_cost(100) == 0.0
        assert ship_hull.pressure_hull_tons(100) == 0.0
        assert ship_hull.heat_shielding_cost(100) == 0.0
        assert ship_hull.breakaway_tons(100) == 0.0
        assert ship_hull.breakaway_cost(100) == 0.0
        assert ship_hull.total_cost(100) == 5_000_000
        assert ship_hull.item_description() == 'Standard Hull'
        assert ship_hull.build_notes().errors == []
        assert ship_hull._all_parts() == []

    def test_enabled_option_cost_helpers_return_values(self):
        ship_hull = hull.Hull(
            configuration=hull.standard_hull.model_copy(update={'breakaway': True}),
            pressure_hull=True,
            heat_shielding=True,
            radiation_shielding=True,
            reflec=True,
        )

        assert ship_hull.radiation_shielding_cost(100) == 2_500_000
        assert ship_hull.reflec_cost(100) == 10_000_000
        assert ship_hull.pressure_hull_tons(100) == 25.0
        assert ship_hull.heat_shielding_cost(100) == 10_000_000
        assert ship_hull.breakaway_tons(100) == 2.0
        assert ship_hull.breakaway_cost(100) == 4_000_000
        assert ship_hull.total_cost(100) == 50_000_000
        assert ship_hull.item_description() == 'Standard Hull, Pressure Hull'

    def test_reflec_with_stealth_reports_error_note(self):
        ship_hull = hull.Hull(
            configuration=hull.standard_hull,
            stealth=hull.BasicStealth(),
            reflec=True,
        )

        assert 'Reflec cannot be combined with stealth' in ship_hull.build_notes().errors

    def test_all_parts_returns_optional_parts_in_display_order(self):
        armour = hull.TitaniumSteelArmour(protection=1)
        stealth = hull.BasicStealth()
        adjustable_hull = hull.AdjustableHull()
        bulkhead = hull.ArmouredBulkhead(protected_tonnage=10)
        airlock = Airlock()
        aerofins = Aerofins()
        ship_hull = hull.Hull(
            configuration=hull.standard_hull,
            armour=armour,
            stealth=stealth,
            adjustable_hull=adjustable_hull,
            armoured_bulkheads=[bulkhead],
            airlocks=[airlock],
            aerofins=aerofins,
        )

        assert ship_hull._all_parts() == [armour, stealth, adjustable_hull, bulkhead, airlock, aerofins]

    def test_empty_armoured_bulkheads_are_omitted_from_model_dump(self):
        assert 'armoured_bulkheads' not in hull.Hull(configuration=hull.standard_hull).model_dump()

    def test_non_empty_armoured_bulkheads_are_kept_in_model_dump(self):
        ship_hull = hull.Hull(
            configuration=hull.standard_hull,
            armoured_bulkheads=[hull.ArmouredBulkhead(protected_tonnage=10)],
        )

        dumped_bulkhead = ship_hull.model_dump()['armoured_bulkheads'][0]
        assert dumped_bulkhead['protected_tonnage'] == 10.0
        assert dumped_bulkhead['protected_item'] is None
        assert dumped_bulkhead['from_ship_part'] is False

    def test_add_spec_rows_includes_all_optional_hull_rows(self):
        bulkhead = hull.ArmouredBulkhead(protected_tonnage=20)
        ship_hull = hull.Hull(
            configuration=hull.standard_hull.model_copy(update={'breakaway': True}),
            armour=hull.TitaniumSteelArmour(protection=1),
            stealth=hull.BasicStealth(),
            adjustable_hull=hull.AdjustableHull(),
            airlocks=[Airlock()],
            aerofins=Aerofins(),
            heat_shielding=True,
            radiation_shielding=True,
            reflec=True,
        )
        spec = ShipSpec()

        ship_hull.add_spec_rows(_SpecShip(bulkheads=[bulkhead]), spec)

        assert [row.item for row in spec.rows] == [
            'Standard Hull',
            'Basic Ship Systems',
            'part:TitaniumSteelArmour',
            'part:BasicStealth',
            'part:AdjustableHull',
            'Breakaway Hull Connections',
            'Heat Shielding',
            'Radiation Shielding: Reduce Rads by 1,000',
            'Reflec',
            'Armoured Bulkheads',
            'group:Airlock',
            'group:Aerofins',
        ]
        assert spec.row('Standard Hull').emphasize_tons
        assert spec.row('Breakaway Hull Connections').tons == 2.0
        assert spec.row('Armoured Bulkheads').tons == 2.0

    def test_pressure_hull_spec_row_provides_armour_when_no_armour_part_exists(self):
        ship_hull = hull.Hull(configuration=hull.standard_hull, pressure_hull=True)
        spec = ShipSpec()

        ship_hull.add_spec_rows(_SpecShip(), spec)

        assert spec.row('Armour: 4').tons == 25.0

    def test_plain_hull_spec_rows_do_not_include_armour_row(self):
        ship_hull = hull.Hull(configuration=hull.standard_hull)
        spec = ShipSpec()

        ship_hull.add_spec_rows(_SpecShip(), spec)

        assert [row.item for row in spec.rows] == ['Standard Hull', 'Basic Ship Systems']

    def test_spinext_configuration_dict_deserializes_to_source_specific_model(self):
        ship_hull = hull.Hull.model_validate(
            {
                'configuration': {
                    'description': 'SpinExt Primitive Hull',
                    'streamlined': hull.Streamlined.NO,
                    'spinext_material': 'wood',
                }
            }
        )

        assert type(ship_hull.configuration).__name__ == 'SpinExtPrimitiveHull'
