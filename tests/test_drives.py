import pytest

from ceres import ship
from ceres.base import ShipBase
from ceres.drives import (
    FusionPlantTL8,
    FusionPlantTL12,
    FusionPlantTL15,
    MDrive,
    OperationFuel,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


# --- MDrive ---


def test_mdrive_standard_tons():
    d = MDrive(rating=6)
    d.bind(DummyOwner(12, 6))
    assert d.minimum_tl == 12
    assert d.ship_tl == 12
    assert d.effective_tl == 12
    assert float(d.tons) == pytest.approx(0.36)


def test_mdrive_standard_cost():
    d = MDrive(rating=6)
    d.bind(DummyOwner(12, 6))
    assert float(d.cost) == pytest.approx(720_000)


def test_mdrive_power():
    d = MDrive(rating=6)
    d.bind(DummyOwner(12, 6))
    assert d.power == 4  # ceil(0.1 * 6 * 6) = ceil(3.6) = 4


def test_mdrive_budget_increased_size_tons():
    d = MDrive(rating=6, budget=True, increased_size=True)
    d.bind(DummyOwner(12, 6))
    assert float(d.tons) == pytest.approx(0.45)  # 0.36 * 1.25


def test_mdrive_budget_increased_size_cost():
    d = MDrive(rating=6, budget=True, increased_size=True)
    d.bind(DummyOwner(12, 6))
    assert float(d.cost) == pytest.approx(540_000)  # 720_000 * 0.75


def test_mdrive_tl_too_low():
    # Rating 6 requires TL12; TL11 ship should fail at bind time
    with pytest.raises(ValueError):
        d = MDrive(rating=6)
        d.bind(DummyOwner(11, 6))


def test_mdrive_recomputes_cost_from_input():
    d = MDrive.model_validate({'rating': 6, 'cost': 999})
    d.bind(DummyOwner(12, 6))
    assert d.cost == pytest.approx(720_000)


def test_mdrive_recomputes_tons_from_input():
    d = MDrive.model_validate({'rating': 6, 'tons': 999})
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


def test_fusion_plant_budget_increased_size_tons():
    p = FusionPlantTL12(output=8, budget=True, increased_size=True)
    p.bind(DummyOwner(12, 6))
    assert float(p.tons) == pytest.approx(8 / 15 * 1.25)


def test_fusion_plant_budget_increased_size_cost():
    p = FusionPlantTL12(output=8, budget=True, increased_size=True)
    p.bind(DummyOwner(12, 6))
    assert float(p.cost) == pytest.approx(8 / 15 * 1_000_000 * 0.75)


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
    with pytest.raises(ValueError):
        FusionPlantTL12(output=8).bind(DummyOwner(11, 6))


# --- OperationFuel ---


def _make_ship_with_plant(**kwargs):
    fuel = OperationFuel(weeks=1)
    s = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        fusion_plant=FusionPlantTL12(output=8, **kwargs),
        operation_fuel=fuel,
    )
    return s, s.operation_fuel


def test_operation_fuel_1_week_tons():
    # 10% of plant modified tons / 4 weeks, ceil to 2 decimal places
    # plant modified tons = 8/15 * 1.25 ≈ 0.6667
    # monthly = 0.0667, weekly = 0.01667, ceil_2dp = 0.02
    _, fuel = _make_ship_with_plant(budget=True, increased_size=True)
    assert float(fuel.tons) == pytest.approx(0.02)


def test_operation_fuel_cost_zero():
    _, fuel = _make_ship_with_plant(budget=True, increased_size=True)
    assert fuel.cost == 0


def test_operation_fuel_power_zero():
    _, fuel = _make_ship_with_plant(budget=True, increased_size=True)
    assert fuel.power == 0


def test_operation_fuel_requires_plant():
    with pytest.raises(ValueError, match='FusionPlant'):
        ship.Ship(
            tl=12,
            displacement=6,
            hull=ship.Hull(configuration=ship.streamlined_hull),
            operation_fuel=OperationFuel(weeks=1),
        )
