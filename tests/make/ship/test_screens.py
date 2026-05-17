import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.parts import HighTechnology, SizeReduction
from ceres.make.ship.screens import MesonScreen, NuclearDamper, ScreensSection


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


@pytest.mark.parametrize(
    ('screen', 'tl', 'tons', 'cost', 'power', 'damage_reduction'),
    [
        (MesonScreen(), 13, 10.0, 20_000_000.0, 30.0, '2D × 10'),
        (NuclearDamper(), 12, 10.0, 10_000_000.0, 20.0, '2D'),
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
