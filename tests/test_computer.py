import pytest

from ceres.base import ShipBase
from ceres.computer import (
    AutoRepair,
    AutoRepair1,
    AutoRepair2,
    Computer5,
    Computer10,
    Computer15,
    ComputerSection,
    Core40,
    Evade,
    Evade1,
    Evade2,
    FireControl,
    FireControl1,
    FireControl2,
    Intellect,
    JumpControl,
    JumpControl1,
    JumpControl2,
    JumpControl3,
    Library,
    Manoeuvre,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_computer_5_cost():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert c.minimum_tl == 7
    assert c.ship_tl == 12
    assert c.effective_tl == 12
    assert c.processing == 5
    assert c.jump_control_processing == 5
    assert float(c.cost) == 30_000


def test_computer_10_cost():
    c = Computer10()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 160_000


def test_computer_15_cost():
    c = Computer15()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 2_000_000


def test_computer_tons_zero():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert float(c.tons) == 0


def test_computer_power_zero():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert c.power == 0


def test_computer_5_min_tl():
    c = Computer5()
    c.bind(DummyOwner(6, 100))
    assert ('error', 'Requires TL7, ship is TL6') in [
        (note.category.value, note.message) for note in c.notes
    ]


def test_computer_recomputes_cost_from_input():
    c = Computer5.model_validate({'cost': 999})
    c.bind(DummyOwner(12, 6))
    assert c.cost == 30_000


def test_computer_bis_increases_cost_and_jump_control_processing():
    c = Computer5(bis=True)
    c.bind(DummyOwner(12, 6))
    assert c.processing == 5
    assert c.jump_control_processing == 10
    assert c.cost == 45_000


def test_computer_fib_increases_cost():
    c = Computer5(fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 45_000


def test_computer_bis_and_fib_double_cost():
    c = Computer5(bis=True, fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 60_000


def test_core_40_hardware():
    c = Core40()
    c.bind(DummyOwner(12, 100))
    assert c.minimum_tl == 9
    assert c.processing == 40
    assert c.jump_control_processing == 40
    assert c.cost == 45_000_000


def test_core_40_retro_hardware():
    c = Core40(fib=True, retro=True)
    c.bind(DummyOwner(13, 100))
    assert c.build_item() == 'Core/40/fib, (Retro*)'
    assert c.cost == pytest.approx(4_218_750.0)


def test_included_software_packages():
    c = Computer5()
    c.bind(DummyOwner(12, 100))
    assert [type(package) for package in c.included_software] == [Library, Manoeuvre, Intellect]
    assert [package.cost for package in c.included_software] == [0.0, 0.0, 0.0]


def test_jump_control_2_data():
    p = JumpControl2()
    assert p.description == 'Jump Control/2'
    assert p.minimum_tl == 11
    assert p.bandwidth == 10
    assert p.cost == 200_000


def test_computer_5_cannot_run_jump_control_2():
    c = Computer5()
    c.bind(DummyOwner(12, 100))
    assert not c.can_run(JumpControl2())


def test_computer_5_bis_can_run_jump_control_2():
    c = Computer5(bis=True)
    c.bind(DummyOwner(12, 100))
    assert c.can_run(JumpControl2())


def test_software_packages_keep_highest_singleton_rank():
    hardware = Computer5(bis=True)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl2(), JumpControl3()])

    assert [package.description for package in section.software_packages.values()] == [
        'Library',
        'Manoeuvre/0',
        'Intellect',
        'Jump Control/3',
    ]

    assert isinstance(section.software_packages[JumpControl], JumpControl3)


def test_software_packages_warn_about_redundant_lower_singleton():
    hardware = Computer5(bis=True)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl2(), JumpControl3()])

    jump_control = section.software_packages[JumpControl]
    assert [(note.category.value, note.message) for note in jump_control.notes] == [
        ('item', 'Jump Control/3'),
        ('warning', 'Redundant Jump Control/2 added'),
    ]


def test_software_singleton_lookup_uses_family_types():
    hardware = Computer10()
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(
        hardware=hardware,
        software=[Evade1(), Evade2(), FireControl1(), FireControl2(), AutoRepair1(), AutoRepair2()],
    )

    assert isinstance(section.software_packages[Evade], Evade2)
    assert isinstance(section.software_packages[FireControl], FireControl2)
    assert isinstance(section.software_packages[AutoRepair], AutoRepair2)


def test_validate_software_warns_when_ship_has_no_hardware():
    section = ComputerSection(software=[JumpControl1()])

    section.validate_software(ship_tl=12)

    jump_control = section.software_packages[JumpControl]
    assert ('warning', 'Ship software requires a computer') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]


def test_validate_software_adds_tl_error():
    hardware = Computer5(bis=True)
    hardware.bind(DummyOwner(10, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl2()])

    section.validate_software(ship_tl=10)

    jump_control = section.software_packages[JumpControl]
    assert ('error', 'Jump Control/2 requires TL11') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]


def test_validate_software_adds_cannot_run_error():
    hardware = Computer5()
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl2()])

    section.validate_software(ship_tl=12)

    jump_control = section.software_packages[JumpControl]
    assert ('error', 'Computer/5 cannot run Jump Control/2') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]
