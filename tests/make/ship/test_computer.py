import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.computer import (
    AdvancedFireControl,
    AntiHijack,
    AutoRepair,
    BattleNetwork,
    BattleSystem,
    BroadSpectrumEW,
    Computer,
    ComputerSection,
    ConsciousIntelligence,
    Core,
    ElectronicWarfare,
    Evade,
    FireControl,
    Intellect,
    JumpControl,
    LaunchSolution,
    Library,
    Manoeuvre,
    PointDefence,
    ScreenOptimiser,
    VirtualCrew,
    VirtualGunner,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_computer_5_cost():
    c = Computer(5)
    c.bind(DummyOwner(12, 6))
    assert c.tl == 7
    assert c.ship_tl == 12
    assert c.processing == 5
    assert c.jump_control_processing == 5
    assert float(c.cost) == 30_000


def test_computer_10_cost():
    c = Computer(10)
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 160_000


def test_computer_15_cost():
    c = Computer(15)
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 2_000_000


def test_computer_rejects_invalid_score():
    with pytest.raises(ValueError, match='Unsupported Computer score 23'):
        Computer(23)


def test_computer_tons_zero():
    c = Computer(5)
    c.bind(DummyOwner(12, 6))
    assert float(c.tons) == 0


def test_computer_power_zero():
    c = Computer(5)
    c.bind(DummyOwner(12, 6))
    assert c.power == 0


def test_computer_5_min_tl():
    c = Computer(5)
    c.bind(DummyOwner(6, 100))
    assert ('error', 'Requires TL7, ship is TL6') in [(note.category.value, note.message) for note in c.notes]


def test_computer_recomputes_cost_from_input():
    c = Computer.model_validate({'kind': 'computer', 'score': 5, 'cost': 999})
    c.bind(DummyOwner(12, 6))
    assert c.cost == 30_000


def test_computer_bis_increases_cost_and_jump_control_processing():
    c = Computer(5, bis=True)
    c.bind(DummyOwner(12, 6))
    assert c.processing == 5
    assert c.jump_control_processing == 10
    assert c.cost == 45_000


def test_computer_fib_increases_cost():
    c = Computer(5, fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 45_000


def test_computer_bis_and_fib_double_cost():
    c = Computer(5, bis=True, fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 60_000


def test_core_40_hardware():
    c = Core(40)
    c.bind(DummyOwner(12, 100))
    assert c.tl == 9
    assert c.processing == 40
    assert c.jump_control_processing == 40
    assert c.cost == 45_000_000


def test_core_40_fib_hardware():
    c = Core(40, fib=True)
    c.bind(DummyOwner(13, 100))
    assert c.build_item() == 'Core/40/fib'
    assert c.cost == pytest.approx(67_500_000.0)


def test_included_software_packages():
    c = Computer(5)
    c.bind(DummyOwner(12, 100))
    assert [type(package) for package in c.included_software] == [Library, Manoeuvre, Intellect]
    assert [package.cost for package in c.included_software] == [0.0, 0.0, 0.0]


def test_jump_control_2_data():
    p = JumpControl(2)
    assert p.description == 'Jump Control/2'
    assert p.tl == 11
    assert p.bandwidth == 10
    assert p.cost == 200_000
    assert p.rating == 2


def test_advanced_fire_control_1_data():
    p = AdvancedFireControl(1)
    assert p.description == 'Advanced Fire Control/1'
    assert p.tl == 10
    assert p.bandwidth == 15
    assert p.cost == 12_000_000
    assert p.rating == 1


def test_anti_hijack_1_data():
    p = AntiHijack(1)
    assert p.description == 'Anti-Hijack/1'
    assert p.tl == 11
    assert p.bandwidth == 2
    assert p.cost == 6_000_000


def test_broad_spectrum_ew_data():
    p = BroadSpectrumEW()
    assert p.description == 'Broad Spectrum EW'
    assert p.tl == 13
    assert p.bandwidth == 12
    assert p.cost == 14_000_000


def test_battle_network_2_data():
    p = BattleNetwork(2)
    assert p.description == 'Battle Network/2'
    assert p.tl == 14
    assert p.bandwidth == 10
    assert p.cost == 10_000_000


def test_battle_system_3_data():
    p = BattleSystem(3)
    assert p.description == 'Battle System/3'
    assert p.tl == 15
    assert p.bandwidth == 15
    assert p.cost == 36_000_000


def test_conscious_intelligence_1_data():
    p = ConsciousIntelligence(1)
    assert p.description == 'Conscious Intelligence/1'
    assert p.tl == 16
    assert p.bandwidth == 40
    assert p.cost == 25_000_000


def test_electronic_warfare_1_data():
    p = ElectronicWarfare(1)
    assert p.description == 'Electronic Warfare/1'
    assert p.tl == 10
    assert p.bandwidth == 10
    assert p.cost == 15_000_000


def test_launch_solution_3_data():
    p = LaunchSolution(3)
    assert p.description == 'Launch Solution/3'
    assert p.tl == 12
    assert p.bandwidth == 15
    assert p.cost == 16_000_000


def test_point_defence_2_data():
    p = PointDefence(2)
    assert p.description == 'Point Defence/2'
    assert p.tl == 12
    assert p.bandwidth == 15
    assert p.cost == 12_000_000


def test_screen_optimiser_data():
    p = ScreenOptimiser()
    assert p.description == 'Screen Optimiser'
    assert p.tl == 10
    assert p.bandwidth == 10
    assert p.cost == 5_000_000


def test_virtual_crew_2_data():
    p = VirtualCrew(2)
    assert p.description == 'Virtual Crew/2'
    assert p.tl == 15
    assert p.bandwidth == 15
    assert p.cost == 10_000_000


def test_virtual_gunner_1_data():
    p = VirtualGunner(1)
    assert p.description == 'Virtual Gunner/1'
    assert p.tl == 12
    assert p.bandwidth == 10
    assert p.cost == 5_000_000


def test_evade_3_matches_core_values():
    p = Evade(3)
    assert p.description == 'Evade/3'
    assert p.tl == 13
    assert p.bandwidth == 25
    assert p.cost == 3_000_000


def test_jump_control_rejects_invalid_rating():
    with pytest.raises(ValueError, match='Unsupported JumpControl rating 7'):
        JumpControl(7)


def test_computer_5_cannot_run_jump_control_2():
    c = Computer(5)
    c.bind(DummyOwner(12, 100))
    assert not c.can_run(JumpControl(2))


def test_computer_5_bis_can_run_jump_control_2():
    c = Computer(5, bis=True)
    c.bind(DummyOwner(12, 100))
    assert c.can_run(JumpControl(2))


def test_software_packages_keep_highest_singleton_rank():
    hardware = Computer(5, bis=True)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(2), JumpControl(3)])

    assert [package.description for package in section.software_packages.values()] == [
        'Library',
        'Manoeuvre/0',
        'Intellect',
        'Jump Control/3',
    ]

    assert isinstance(section.software_packages[JumpControl], JumpControl)
    assert section.software_packages[JumpControl].bandwidth == 15


def test_software_packages_warn_about_redundant_lower_singleton():
    hardware = Computer(5, bis=True)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(2), JumpControl(3)])

    jump_control = section.software_packages[JumpControl]
    assert [(note.category.value, note.message) for note in jump_control.notes] == [
        ('item', 'Jump Control/3'),
        ('warning', 'Redundant Jump Control/2 added'),
    ]


def test_software_singleton_lookup_uses_family_types():
    hardware = Computer(10)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(
        hardware=hardware,
        software=[
            Evade(1),
            Evade(2),
            FireControl(1),
            FireControl(2),
            AutoRepair(1),
            AutoRepair(2),
        ],
    )

    assert isinstance(section.software_packages[Evade], Evade)
    assert section.software_packages[Evade].rating == 2
    assert isinstance(section.software_packages[FireControl], FireControl)
    assert section.software_packages[FireControl].rating == 2
    assert isinstance(section.software_packages[AutoRepair], AutoRepair)
    assert section.software_packages[AutoRepair].rating == 2


def test_software_singleton_lookup_uses_new_software_families():
    hardware = Computer(35)
    hardware.bind(DummyOwner(15, 100))
    section = ComputerSection(
        hardware=hardware,
        software=[
            AdvancedFireControl(1),
            AdvancedFireControl(2),
            AntiHijack(1),
            AntiHijack(2),
            ElectronicWarfare(1),
            ElectronicWarfare(2),
            VirtualGunner(0),
            VirtualGunner(1),
        ],
    )

    assert isinstance(section.software_packages[AdvancedFireControl], AdvancedFireControl)
    assert section.software_packages[AdvancedFireControl].rating == 2
    assert isinstance(section.software_packages[AntiHijack], AntiHijack)
    assert section.software_packages[AntiHijack].rating == 2
    assert isinstance(section.software_packages[ElectronicWarfare], ElectronicWarfare)
    assert section.software_packages[ElectronicWarfare].rating == 2
    assert isinstance(section.software_packages[VirtualGunner], VirtualGunner)
    assert section.software_packages[VirtualGunner].rating == 1


def test_validate_software_warns_when_ship_has_no_hardware():
    section = ComputerSection(software=[JumpControl(1)])

    section.validate_software(ship_tl=12)

    jump_control = section.software_packages[JumpControl]
    assert ('warning', 'Ship software requires a computer') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]


def test_validate_software_adds_tl_error():
    hardware = Computer(5, bis=True)
    hardware.bind(DummyOwner(10, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(2)])

    section.validate_software(ship_tl=10)

    jump_control = section.software_packages[JumpControl]
    assert ('error', 'Jump Control/2 requires TL11') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]


def test_validate_software_adds_cannot_run_error():
    hardware = Computer(5)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(2)])

    section.validate_software(ship_tl=12)

    jump_control = section.software_packages[JumpControl]
    assert ('error', 'Computer/5 cannot run Jump Control/2') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]
