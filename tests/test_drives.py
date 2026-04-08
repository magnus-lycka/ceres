import pytest

from ceres import ship
from ceres.base import ShipBase
from ceres.drives import (
    FusionPlantTL8,
    FusionPlantTL12,
    FusionPlantTL15,
    JumpDrive1,
    JumpDrive2,
    JumpDrive3,
    JumpDrive4,
    JumpDrive5,
    JumpDrive6,
    JumpDrive7,
    JumpDrive8,
    JumpDrive9,
    MDrive6,
)
from ceres.storage import FuelSection, OperationFuel


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


# --- JumpDrive ---


@pytest.mark.parametrize('cls, rating, tl, pct', [
    (JumpDrive1, 1, 9, 0.025),
    (JumpDrive2, 2, 11, 0.05),
    (JumpDrive3, 3, 12, 0.075),
    (JumpDrive4, 4, 13, 0.10),
    (JumpDrive5, 5, 14, 0.125),
    (JumpDrive6, 6, 15, 0.15),
    (JumpDrive7, 7, 16, 0.175),
    (JumpDrive8, 8, 17, 0.20),
    (JumpDrive9, 9, 18, 0.225),
])
def test_jump_drive_tons_cost_tl(cls, rating, tl, pct):
    d = cls()
    d.bind(DummyOwner(tl, 200))
    expected_tons = 200 * pct + 5
    assert d.minimum_tl == tl
    assert d.rating == rating
    assert float(d.tons) == pytest.approx(expected_tons)
    assert float(d.cost) == pytest.approx(expected_tons * 1_500_000)


# --- MDrive ---


def test_mdrive_standard_tons():
    d = MDrive6()
    d.bind(DummyOwner(12, 6))
    assert d.minimum_tl == 12
    assert d.ship_tl == 12
    assert d.effective_tl == 12
    assert float(d.tons) == pytest.approx(0.36)


def test_mdrive_standard_cost():
    d = MDrive6()
    d.bind(DummyOwner(12, 6))
    assert float(d.cost) == pytest.approx(720_000)


def test_mdrive_power():
    d = MDrive6()
    d.bind(DummyOwner(12, 6))
    assert d.power == 4  # ceil(0.1 * 6 * 6) = ceil(3.6) = 4



def test_mdrive_tl_too_low():
    d = MDrive6()
    d.bind(DummyOwner(11, 6))
    assert ('error', 'Requires TL12, ship is TL11') in [
        (note.category.value, note.message) for note in d.notes
    ]


def test_mdrive_recomputes_cost_from_input():
    d = MDrive6.model_validate({'cost': 999})
    d.bind(DummyOwner(12, 6))
    assert d.cost == pytest.approx(720_000)


def test_mdrive_recomputes_tons_from_input():
    d = MDrive6.model_validate({'tons': 999})
    d.bind(DummyOwner(12, 6))
    assert d.tons == pytest.approx(0.36)


# --- FusionPlant ---


def test_fusion_plant_base_tons():
    p = FusionPlantTL12(output=8)
    p.bind(DummyOwner(12, 6))
    assert p.minimum_tl == 12
    assert p.ship_tl == 12
    assert p.effective_tl == 12
    assert float(p.tons) == pytest.approx(8 / 15)


def test_fusion_plant_base_cost():
    p = FusionPlantTL12(output=8)
    p.bind(DummyOwner(12, 6))
    assert float(p.cost) == pytest.approx(8 / 15 * 1_000_000)


def test_fusion_plant_output():
    p = FusionPlantTL12(output=8)
    assert p.output == 8


def test_fusion_plant_power_zero():
    # Power plant generates power; it does not consume it
    p = FusionPlantTL12(output=8)
    p.bind(DummyOwner(12, 6))
    assert p.power == 0



def test_fusion_plant_recomputes_tons_from_input():
    p = FusionPlantTL12.model_validate({'output': 8, 'tons': 999})
    p.bind(DummyOwner(12, 6))
    assert p.tons == pytest.approx(8 / 15)


def test_fusion_plant_tl8_variant():
    p = FusionPlantTL8(output=8)
    p.bind(DummyOwner(12, 6))
    assert p.minimum_tl == 8
    assert p.effective_tl == 8
    assert float(p.tons) == pytest.approx(0.8)
    assert float(p.cost) == pytest.approx(400_000)


def test_fusion_plant_tl15_variant():
    p = FusionPlantTL15(output=8)
    p.bind(DummyOwner(15, 6))
    assert p.minimum_tl == 15
    assert p.effective_tl == 15
    assert float(p.tons) == pytest.approx(0.4)
    assert float(p.cost) == pytest.approx(800_000)


def test_fusion_plant_rejects_ship_below_minimum_tl():
    plant = FusionPlantTL12(output=8)
    plant.bind(DummyOwner(11, 6))
    assert ('error', 'Requires TL12, ship is TL11') in [
        (note.category.value, note.message) for note in plant.notes
    ]


def _make_ship_with_plant():
    fuel = OperationFuel(weeks=1)
    s = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        fusion_plant=FusionPlantTL12(output=8),
        fuel=FuelSection(operation_fuel=fuel),
    )
    return s, s.operation_fuel


def test_operation_fuel_1_week_tons():
    # 10% of plant tons / 4 weeks, ceil to 2 decimal places
    # plant tons = 8/15 ≈ 0.5333, monthly = 0.0533, weekly = 0.01333, ceil_2dp = 0.02
    _, fuel = _make_ship_with_plant()
    assert float(fuel.tons) == pytest.approx(0.02)


def test_operation_fuel_cost_zero():
    _, fuel = _make_ship_with_plant()
    assert fuel.cost == 0


def test_operation_fuel_power_zero():
    _, fuel = _make_ship_with_plant()
    assert fuel.power == 0


def test_operation_fuel_requires_plant():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
    )
    assert my_ship.operation_fuel is not None
    assert my_ship.operation_fuel.tons == 0.0
    assert ('error', 'Ship must have a FusionPlant to compute OperationFuel') in [
        (note.category.value, note.message) for note in my_ship.operation_fuel.notes
    ]
