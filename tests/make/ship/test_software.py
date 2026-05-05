import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.computer import (
    Computer,
    ComputerSection,
    Core,
)
from ceres.make.ship.software import (
    AdvancedFireControl,
    AntiHijack,
    AutoRepair,
    BattleNetwork,
    BattleSystem,
    BroadSpectrumEW,
    ConsciousIntelligence,
    ElectronicWarfare,
    Evade,
    FireControl,
    JumpControl,
    LaunchSolution,
    PointDefence,
    ScreenOptimiser,
    VirtualCrew,
    VirtualGunner,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_jump_control_2_data():
    p = JumpControl(rating=2)
    assert p.description == 'Jump Control/2'
    assert p.tl == 11
    assert p.bandwidth == 10
    assert p.cost == 200_000
    assert p.rating == 2


def test_advanced_fire_control_1_data():
    p = AdvancedFireControl(rating=1)
    assert p.description == 'Advanced Fire Control/1'
    assert p.tl == 10
    assert p.bandwidth == 15
    assert p.cost == 12_000_000
    assert p.rating == 1


def test_anti_hijack_1_data():
    p = AntiHijack(rating=1)
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
    p = BattleNetwork(rating=2)
    assert p.description == 'Battle Network/2'
    assert p.tl == 14
    assert p.bandwidth == 10
    assert p.cost == 10_000_000


def test_battle_system_3_data():
    p = BattleSystem(rating=3)
    assert p.description == 'Battle System/3'
    assert p.tl == 15
    assert p.bandwidth == 15
    assert p.cost == 36_000_000


def test_conscious_intelligence_1_data():
    p = ConsciousIntelligence(rating=1)
    assert p.description == 'Conscious Intelligence/1'
    assert p.tl == 16
    assert p.bandwidth == 40
    assert p.cost == 25_000_000


def test_electronic_warfare_1_data():
    p = ElectronicWarfare(rating=1)
    assert p.description == 'Electronic Warfare/1'
    assert p.tl == 10
    assert p.bandwidth == 10
    assert p.cost == 15_000_000


def test_launch_solution_3_data():
    p = LaunchSolution(rating=3)
    assert p.description == 'Launch Solution/3'
    assert p.tl == 12
    assert p.bandwidth == 15
    assert p.cost == 16_000_000


def test_point_defence_2_data():
    p = PointDefence(rating=2)
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
    p = VirtualCrew(rating=2)
    assert p.description == 'Virtual Crew/2'
    assert p.tl == 15
    assert p.bandwidth == 15
    assert p.cost == 10_000_000


def test_virtual_gunner_1_data():
    p = VirtualGunner(rating=1)
    assert p.description == 'Virtual Gunner/1'
    assert p.tl == 12
    assert p.bandwidth == 10
    assert p.cost == 5_000_000


def test_evade_3_matches_core_values():
    p = Evade(rating=3)
    assert p.description == 'Evade/3'
    assert p.tl == 13
    assert p.bandwidth == 25
    assert p.cost == 3_000_000


def test_jump_control_rejects_invalid_rating():
    with pytest.raises(ValueError, match='Unsupported JumpControl rating 7'):
        JumpControl(rating=7)


def test_jump_control_2_degrades_on_computer_5():
    jc = JumpControl(rating=2)
    c = Computer(processing=5)
    c.bind(DummyOwner(12, 100))
    jc.validate_on_computer(c)
    assert jc.effective_rating == 1
    assert any('degraded' in note.message for note in jc.notes)


def test_jump_control_2_runs_at_full_rating_on_computer_5_bis():
    jc = JumpControl(rating=2)
    c = Computer(processing=5, bis=True)
    c.bind(DummyOwner(12, 100))
    jc.validate_on_computer(c)
    assert jc.effective_rating == 2
    assert not any(note.category.value == 'warning' for note in jc.notes)


def test_software_packages_keep_highest_singleton_rank():
    hardware = Computer(processing=5, bis=True)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2), JumpControl(rating=3)])

    assert [package.description for package in section.software_packages.values()] == [
        'Library',
        'Manoeuvre/0',
        'Intellect',
        'Jump Control/3',
    ]

    assert isinstance(section.software_packages[JumpControl], JumpControl)
    assert section.software_packages[JumpControl].bandwidth == 15


def test_software_packages_warn_about_redundant_lower_singleton():
    hardware = Computer(processing=5, bis=True)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2), JumpControl(rating=3)])

    jump_control = section.software_packages[JumpControl]
    assert [(note.category.value, note.message) for note in jump_control.notes] == [
        ('item', 'Jump Control/3'),
        ('warning', 'Redundant Jump Control/2 added'),
    ]


def test_software_singleton_lookup_uses_family_types():
    hardware = Computer(processing=10)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(
        hardware=hardware,
        software=[
            Evade(rating=1),
            Evade(rating=2),
            FireControl(rating=1),
            FireControl(rating=2),
            AutoRepair(rating=1),
            AutoRepair(rating=2),
        ],
    )

    evade = section.software_packages[Evade]
    assert isinstance(evade, Evade) and evade.rating == 2
    fire_control = section.software_packages[FireControl]
    assert isinstance(fire_control, FireControl) and fire_control.rating == 2
    auto_repair = section.software_packages[AutoRepair]
    assert isinstance(auto_repair, AutoRepair) and auto_repair.rating == 2


def test_software_singleton_lookup_uses_new_software_families():
    hardware = Computer(processing=35)
    hardware.bind(DummyOwner(15, 100))
    section = ComputerSection(
        hardware=hardware,
        software=[
            AdvancedFireControl(rating=1),
            AdvancedFireControl(rating=2),
            AntiHijack(rating=1),
            AntiHijack(rating=2),
            ElectronicWarfare(rating=1),
            ElectronicWarfare(rating=2),
            VirtualGunner(rating=0),
            VirtualGunner(rating=1),
        ],
    )

    afc = section.software_packages[AdvancedFireControl]
    assert isinstance(afc, AdvancedFireControl) and afc.rating == 2
    anti_hijack = section.software_packages[AntiHijack]
    assert isinstance(anti_hijack, AntiHijack) and anti_hijack.rating == 2
    ew = section.software_packages[ElectronicWarfare]
    assert isinstance(ew, ElectronicWarfare) and ew.rating == 2
    vg = section.software_packages[VirtualGunner]
    assert isinstance(vg, VirtualGunner) and vg.rating == 1


def test_validate_software_warns_when_ship_has_no_hardware():
    section = ComputerSection(software=[JumpControl(rating=1)])

    section.validate_software()

    jump_control = section.software_packages[JumpControl]
    assert ('warning', 'Ship software requires a computer') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]


def test_validate_software_adds_tl_error():
    hardware = Computer(processing=5, bis=True)
    hardware.bind(DummyOwner(10, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2)])

    section.validate_software()

    jump_control = section.software_packages[JumpControl]
    assert ('error', 'Jump Control/2 requires TL11') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]


def test_jump_control_degrades_when_processing_insufficient():
    hardware = Computer(processing=5)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2)])

    section.validate_software()

    jump_control = section.software_packages[JumpControl]
    assert isinstance(jump_control, JumpControl)
    assert jump_control.effective_rating == 1
    assert ('warning', 'Computer/5 can only run Jump Control/1 (degraded from 2)') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]


def test_jump_control_runs_at_full_on_core():
    jc = JumpControl(rating=6)
    c = Core(processing=40)
    c.bind(DummyOwner(15, 100))
    jc.validate_on_computer(c)
    assert jc.effective_rating == 6
    assert not any(note.category.value == 'warning' for note in jc.notes)
