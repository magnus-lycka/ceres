from pydantic import TypeAdapter
import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.automation import (
    AdvancedAutomation,
    AnyAutomation,
    CrewIntensiveAutomation,
    EnhancedAutomation,
    HighAutomation,
    LowAutomation,
    StandardAutomation,
)
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.drives import DriveSection, MDrive1
from ceres.make.ship.power import FusionPlantTL12, PowerSection


def _automation_test_ship(automation):
    return ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        automation=automation,
    )


def _automation_basis() -> float:
    hull_basis = 200 * 50_000
    m_drive = 200 * 0.01 * 2_000_000
    power_plant = 20 / 15 * 1_000_000
    return hull_basis + m_drive + power_plant


@pytest.mark.parametrize(
    ('automation', 'cost_percent', 'crew_factor', 'effect_note'),
    [
        (CrewIntensiveAutomation(), -0.40, 2.0, 'DM-4 on all shipboard tasks'),
        (LowAutomation(), -0.20, 1.4, 'DM-1 on all shipboard tasks after 1 week in space'),
        (StandardAutomation(), 0.0, 1.0, None),
        (EnhancedAutomation(), 0.25, 0.9, None),
        (AdvancedAutomation(), 0.50, 0.75, 'DM+1 on all shipboard tasks'),
        (HighAutomation(), 1.00, 0.6, 'DM+2 on all shipboard tasks'),
    ],
)
def test_automation_values(automation, cost_percent, crew_factor, effect_note):
    my_ship = _automation_test_ship(automation)

    assert automation.cost_percent == cost_percent
    assert automation.crew_factor == crew_factor
    assert automation.effect_note == effect_note
    assert my_ship.automation.cost == pytest.approx(_automation_basis() * cost_percent)


def test_standard_automation_emits_no_spec_row():
    spec = _automation_test_ship(StandardAutomation()).build_spec()

    assert spec.rows_matching('Standard Automation') == []


def test_non_standard_automation_emits_hull_spec_row():
    spec = _automation_test_ship(LowAutomation()).build_spec()

    row = spec.row('Low Automation', section='Hull')
    assert row.tons is None
    assert row.cost == pytest.approx(_automation_basis() * -0.20)
    assert row.notes.infos == ['DM-1 on all shipboard tasks after 1 week in space']


def test_automation_serialization_selects_subclass_from_level():
    loaded = TypeAdapter(AnyAutomation).validate_python({'level': 'high'})

    assert isinstance(loaded, HighAutomation)
    assert loaded.level == 'high'


def test_non_gravity_hull_discount_is_not_part_of_automation_basis():
    non_gravity = hull.standard_hull.model_copy(update={'non_gravity': True})

    assert non_gravity.cost(200) == 5_000_000
    assert non_gravity.automation_basis_cost(200) == 10_000_000
