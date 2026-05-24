import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.parts import HighTechnology, SizeReduction
from ceres.make.ship.screens import (
    AdvancedEnergyShield,
    BlackGlobeCapacitorBank,
    BlackGlobeGenerator,
    DeflectorScreen,
    EnergyShield,
    ImprovedEnergyShield,
    MesonScreen,
    NuclearDamper,
    ScreensSection,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


@pytest.mark.parametrize(
    ('screen', 'tl', 'tons', 'cost', 'power', 'damage_reduction'),
    [
        (MesonScreen(), 13, 10.0, 20_000_000.0, 30.0, '2D × 10'),
        (NuclearDamper(), 12, 10.0, 10_000_000.0, 20.0, '2D'),
        (DeflectorScreen(), 10, 5.0, 5_000_000.0, 10.0, '1D'),
        (EnergyShield(), 14, 20.0, 25_000_000.0, 50.0, 'Energy buffer 10'),
        (ImprovedEnergyShield(), 16, 15.0, 35_000_000.0, 75.0, 'Energy buffer 20'),
        (AdvancedEnergyShield(), 18, 10.0, 60_000_000.0, 100.0, 'Energy buffer 50'),
        (BlackGlobeGenerator(), 15, 50.0, 100_000_000.0, 30.0, 'Absorbs attacks into capacitors'),
    ],
)
def test_screen_hg_table_values(screen, tl, tons, cost, power, damage_reduction):
    screen.bind(DummyOwner(15, 1_000))

    assert screen.tl == tl
    assert screen.tons == pytest.approx(tons)
    assert screen.cost == pytest.approx(cost)
    assert screen.power == pytest.approx(power)
    assert screen.damage_reduction == damage_reduction


def test_screen_size_reduction_values():
    screen = NuclearDamper(customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]))
    screen.bind(DummyOwner(15, 1_000))

    assert screen.tons == pytest.approx(7.0)
    assert screen.cost == pytest.approx(15_000_000.0)
    assert screen.power == pytest.approx(20.0)


def test_screens_appear_in_spec_rows():
    my_ship = ship.Ship(
        tl=15,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        screens=ScreensSection(screens=[NuclearDamper(), NuclearDamper()]),
    )

    spec = my_ship.build_spec()

    row = spec.row('Nuclear Damper', section='Screens')
    assert row.quantity == 2
    assert row.tons == pytest.approx(20.0)
    assert row.cost == pytest.approx(20_000_000.0)
    assert row.power == pytest.approx(-40.0)


def test_mixed_screen_installations_appear_as_separate_grouped_rows():
    my_ship = ship.Ship(
        tl=15,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        screens=ScreensSection(screens=[MesonScreen(), MesonScreen(), NuclearDamper(), DeflectorScreen()]),
    )

    spec = my_ship.build_spec()

    meson = spec.row('Meson Screen', section='Screens')
    assert meson.quantity == 2
    assert meson.tons == pytest.approx(20.0)
    assert meson.cost == pytest.approx(40_000_000.0)
    assert meson.power == pytest.approx(-60.0)

    nuclear = spec.row('Nuclear Damper', section='Screens')
    assert nuclear.quantity is None
    assert nuclear.tons == pytest.approx(10.0)
    assert nuclear.cost == pytest.approx(10_000_000.0)
    assert nuclear.power == pytest.approx(-20.0)

    deflector = spec.row('Deflector Screen', section='Screens')
    assert deflector.quantity is None
    assert deflector.tons == pytest.approx(5.0)
    assert deflector.cost == pytest.approx(5_000_000.0)
    assert deflector.power == pytest.approx(-10.0)


def test_black_globe_generator_spec_row_notes():
    my_ship = ship.Ship(
        tl=15,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        screens=ScreensSection(screens=[BlackGlobeGenerator()]),
    )

    row = my_ship.build_spec().row('Black Globe Generator', section='Screens')
    assert row.tons == pytest.approx(50.0)
    assert row.cost == pytest.approx(100_000_000.0)
    assert row.power == pytest.approx(-30.0)
    assert row.notes.infos == [
        'Not commercially available; availability is at Referee discretion',
        'Active globe prevents manoeuvre, dodging, jumping, weapons, and sensors',
        'Absorbed attacks require capacitor capacity; overload destroys the ship',
        'Flicker, capacitor discharge, and overload are operational combat rules not modelled in build specs',
    ]


def test_black_globe_capacitor_bank_spec_row_notes():
    my_ship = ship.Ship(
        tl=15,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        screens=ScreensSection(capacitor_banks=[BlackGlobeCapacitorBank(tons=4)]),
    )

    row = my_ship.build_spec().row('Black Globe Capacitor Bank', section='Screens')
    assert row.tons == pytest.approx(4.0)
    assert row.cost == pytest.approx(12_000_000.0)
    assert row.power is None
    assert row.notes.infos == ['Absorbs 200 points of damage for black globe generators']


def test_screen_union_accepts_deflector_and_energy_shield_from_json_shape():
    section = ScreensSection.model_validate(
        {
            'screens': [
                {'screen_type': 'deflector_screen'},
                {'screen_type': 'energy_shield'},
                {'screen_type': 'improved_energy_shield'},
                {'screen_type': 'advanced_energy_shield'},
                {'screen_type': 'black_globe_generator'},
            ]
        }
    )

    assert [type(screen) for screen in section.screens] == [
        DeflectorScreen,
        EnergyShield,
        ImprovedEnergyShield,
        AdvancedEnergyShield,
        BlackGlobeGenerator,
    ]
