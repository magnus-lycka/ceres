import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.computer import (
    Computer5,
    Computer10,
    Computer15,
    Computer35,
    ComputerSection,
    Core40,
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
    c = Computer5()
    c.bind(DummyOwner(12, 100))
    jc.validate_on_computer(c)
    assert jc.effective_rating == 1
    assert any('degraded' in note.message for note in jc.notes)


def test_jump_control_2_runs_at_full_rating_on_computer_5_bis():
    jc = JumpControl(rating=2)
    c = Computer5(bis=True)
    c.bind(DummyOwner(12, 100))
    jc.validate_on_computer(c)
    assert jc.effective_rating == 2
    assert not jc.notes.warnings


def test_software_packages_keep_installed_duplicates():
    hardware = Computer5(bis=True)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2), JumpControl(rating=3)])

    assert [package.description for package in section.software_packages] == [
        'Library',
        'Manoeuvre/0',
        'Intellect',
        'Jump Control/2',
        'Jump Control/3',
    ]

    jump_controls = [package for package in section.software_packages if isinstance(package, JumpControl)]
    assert [package.bandwidth for package in jump_controls] == [10, 15]


def test_software_packages_do_not_warn_about_redundant_lower_singleton():
    hardware = Computer5(bis=True)
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2), JumpControl(rating=3)])

    jump_controls = [package for package in section.software_packages if isinstance(package, JumpControl)]
    assert [package.notes.items for package in jump_controls] == [['Jump Control/2'], ['Jump Control/3']]
    assert [package.notes.warnings for package in jump_controls] == [[], []]


def test_software_packages_keep_repeated_family_types():
    hardware = Computer10()
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

    evades = [package for package in section.software_packages if isinstance(package, Evade)]
    assert [package.rating for package in evades] == [1, 2]
    fire_controls = [package for package in section.software_packages if isinstance(package, FireControl)]
    assert [package.rating for package in fire_controls] == [1, 2]
    auto_repairs = [package for package in section.software_packages if isinstance(package, AutoRepair)]
    assert [package.rating for package in auto_repairs] == [1, 2]


def test_software_packages_keep_repeated_new_software_families():
    hardware = Computer35()
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

    afcs = [package for package in section.software_packages if isinstance(package, AdvancedFireControl)]
    assert [package.rating for package in afcs] == [1, 2]
    anti_hijacks = [package for package in section.software_packages if isinstance(package, AntiHijack)]
    assert [package.rating for package in anti_hijacks] == [1, 2]
    ews = [package for package in section.software_packages if isinstance(package, ElectronicWarfare)]
    assert [package.rating for package in ews] == [1, 2]
    virtual_gunners = [package for package in section.software_packages if isinstance(package, VirtualGunner)]
    assert [package.rating for package in virtual_gunners] == [0, 1]


def test_validate_software_adds_tl_error():
    hardware = Computer5(bis=True)
    hardware.bind(DummyOwner(10, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2)])

    section.validate_software()

    jump_control = next(package for package in section.software_packages if isinstance(package, JumpControl))
    assert 'Jump Control/2 requires TL11' in jump_control.notes.errors


def test_jump_control_degrades_when_processing_insufficient():
    hardware = Computer5()
    hardware.bind(DummyOwner(12, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2)])

    section.validate_software()

    jump_control = next(package for package in section.software_packages if isinstance(package, JumpControl))
    assert isinstance(jump_control, JumpControl)
    assert jump_control.effective_rating == 1
    assert 'Computer/5 can only run Jump Control/1 (degraded from 2)' in jump_control.notes.warnings


def test_jump_control_runs_at_full_on_core():
    jc = JumpControl(rating=6)
    c = Core40()
    c.bind(DummyOwner(15, 100))
    jc.validate_on_computer(c)
    assert jc.effective_rating == 6


def test_retro_computer_software_tl_cap_is_not_error():
    # Software validation uses ship TL for hard errors; effective TL only triggers a warning.
    # Computer10 (TL9) retro_levels=2 in TL11 ship: ship TL=11 ≥ JC/2 TL11 → no error.
    hardware = Computer10(retro_levels=2)
    hardware.bind(DummyOwner(11, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2)])
    section.validate_software()
    jc = next(p for p in section.software_packages if isinstance(p, JumpControl))
    assert not jc.notes.errors


def test_retro_computer_software_warns_when_exceeds_effective_tl():
    # Computer10 (TL9) retro_levels=2 in TL13 ship: effective TL=11. JC/2 requires TL11 → at boundary, no warning.
    # JC/3 requires TL12 > effective TL11 → warning.
    hardware = Computer10(retro_levels=2)
    hardware.bind(DummyOwner(13, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=3)])
    section.validate_software()
    jc = next(p for p in section.software_packages if isinstance(p, JumpControl))
    assert not jc.notes.errors
    assert any('effective TL' in w for w in jc.notes.warnings)


def test_retro_computer_software_no_warning_at_effective_tl_boundary():
    # Computer10 (TL9) retro_levels=2 in TL13 ship: effective TL=11. JC/2 requires TL11 → no warning.
    hardware = Computer10(retro_levels=2)
    hardware.bind(DummyOwner(13, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2)])
    section.validate_software()
    jc = next(p for p in section.software_packages if isinstance(p, JumpControl))
    assert not jc.notes.errors
    assert not jc.notes.warnings


def test_non_retro_computer_software_validates_against_ship_tl():
    # Computer15 (TL11) in TL11 ship, JumpControl/2 requires TL11 → passes.
    hardware = Computer15(bis=True)
    hardware.bind(DummyOwner(11, 100))
    section = ComputerSection(hardware=hardware, software=[JumpControl(rating=2)])
    section.validate_software()
    jc = next(p for p in section.software_packages if isinstance(p, JumpControl))
    assert not jc.notes.errors
    assert not jc.notes.warnings
