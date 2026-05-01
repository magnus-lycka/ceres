import pytest

from ceres.gear.computer import (
    Agent,
    ComputerChip,
    Expert,
    Intellect,
    IntelligentInterface,
    Interface,
    MicroscopicChip,
    MidSizedComputer,
    MobileComm,
    PortableComputer,
    Security,
    Tablet,
    Translator,
)


def test_interface_matches_csc_values():
    package = Interface()
    assert package.description == 'Interface'
    assert package.bandwidth == 0
    assert package.tl == 7
    assert package.cost == 0.0


def test_intelligent_interface_matches_csc_values():
    package = IntelligentInterface()
    assert package.description == 'Intelligent Interface'
    assert package.bandwidth == 1
    assert package.tl == 11
    assert package.cost == 100.0


def test_intellect_zero_represents_included_ship_intellect():
    package = Intellect(0)
    assert package.description == 'Intellect/0'
    assert package.bandwidth == 0
    assert package.tl == 11
    assert package.cost == 0.0


def test_intellect_three_matches_csc_values():
    package = Intellect(3)
    assert package.description == 'Intellect/3'
    assert package.bandwidth == 3
    assert package.tl == 14
    assert package.cost == 200_000.0


def test_expert_broad_science_planetology_matches_skill_table():
    package = Expert(1, skill='Space Sciences (Planetology)')
    assert package.description == 'Expert (Space Sciences (Planetology))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_higher_rating_increases_tl_and_cost_from_base_skill():
    package = Expert(3, skill='Admin')
    assert package.description == 'Expert (Admin)/3'
    assert package.bandwidth == 3
    assert package.tl == 10
    assert package.cost == 10_000.0


def test_expert_supports_all_companion_science_subskills():
    package = Expert(2, skill='Physical Sciences (Jumpspace Physics)')
    assert package.description == 'Expert (Physical Sciences (Jumpspace Physics))/2'
    assert package.bandwidth == 2
    assert package.tl == 10
    assert package.cost == 2_000.0


def test_expert_known_specialised_skill_uses_flat_lookup():
    package = Expert(1, skill='Electronics (Computers)')
    assert package.description == 'Expert (Electronics (Computers))/1'
    assert package.bandwidth == 1
    assert package.tl == 8
    assert package.cost == 100.0


def test_expert_known_broad_profession_subskill_uses_flat_lookup():
    package = Expert(1, skill='Spacer Profession (Crewmember)')
    assert package.description == 'Expert (Spacer Profession (Crewmember))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_known_worker_profession_subskill_uses_flat_lookup():
    package = Expert(1, skill='Worker Profession (Polymers)')
    assert package.description == 'Expert (Worker Profession (Polymers))/1'
    assert package.bandwidth == 1
    assert package.tl == 9
    assert package.cost == 200.0


def test_expert_unknown_skill_uses_csc_fallback_and_warns():
    package = Expert(1, skill='Cementology')
    assert package.description == 'Expert (Cementology)/1'
    assert package.bandwidth == 1
    assert package.tl == 11
    assert package.cost == 1_000.0
    assert ('warning', 'Unfamiliar Expert skill Cementology uses CSC fallback values') in [
        (note.category.value, note.message) for note in package.notes
    ]


def test_expert_tactics_any_falls_back_like_unknown_skill():
    cementology = Expert(1, skill='Cementology')
    tactics_any = Expert(1, skill='Tactics (Any)')
    assert tactics_any.description == 'Expert (Tactics (Any))/1'
    assert tactics_any.bandwidth == cementology.bandwidth
    assert tactics_any.tl == cementology.tl
    assert tactics_any.cost == cementology.cost
    assert ('warning', 'Unfamiliar Expert skill Tactics (Any) uses CSC fallback values') in [
        (note.category.value, note.message) for note in tactics_any.notes
    ]


def test_expert_language_vilani_uses_known_lookup():
    package = Expert(1, skill='Language Vilani')
    assert package.description == 'Expert (Language Vilani)/1'
    assert package.tl == 9
    assert package.cost == 200.0
    assert package.bandwidth == 1


def test_expert_tactics_military_uses_known_lookup():
    package = Expert(1, skill='Tactics (Military)')
    assert package.description == 'Expert (Tactics (Military))/1'
    assert package.tl == 8
    assert package.cost == 100.0
    assert package.bandwidth == 1


def test_expert_tactics_naval_uses_known_lookup():
    package = Expert(1, skill='Tactics (Naval)')
    assert package.description == 'Expert (Tactics (Naval))/1'
    assert package.tl == 8
    assert package.cost == 100.0
    assert package.bandwidth == 1


def test_security_zero_matches_csc_values():
    package = Security(0)
    assert package.description == 'Security/0'
    assert package.bandwidth == 0
    assert package.tl == 8
    assert package.cost == 0.0


def test_security_three_matches_csc_values():
    package = Security(3)
    assert package.description == 'Security/3'
    assert package.bandwidth == 3
    assert package.tl == 12
    assert package.cost == 20_000.0


def test_security_rejects_invalid_rating():
    with pytest.raises(ValueError, match='Unsupported Security rating 4'):
        Security(4)


def test_agent_zero_matches_csc_values():
    package = Agent(0)
    assert package.description == 'Agent/0'
    assert package.bandwidth == 0
    assert package.tl == 11
    assert package.cost == 500.0


def test_agent_three_matches_csc_values():
    package = Agent(3)
    assert package.description == 'Agent/3'
    assert package.bandwidth == 3
    assert package.tl == 14
    assert package.cost == 250_000.0


def test_translator_zero_matches_csc_values():
    package = Translator(0)
    assert package.description == 'Translator/0'
    assert package.bandwidth == 0
    assert package.tl == 9
    assert package.cost == 50.0


def test_translator_one_matches_csc_values():
    package = Translator(1)
    assert package.description == 'Translator/1'
    assert package.bandwidth == 1
    assert package.tl == 10
    assert package.cost == 500.0


def test_portable_computer_zero_matches_csc_values():
    pc = PortableComputer(0)
    assert pc.tl == 7
    assert pc.mass_kg == 5.0
    assert pc.cost == 500.0


def test_portable_computer_three_matches_csc_values():
    pc = PortableComputer(3)
    assert pc.tl == 12
    assert pc.mass_kg == 0.5
    assert pc.cost == 1_000.0


def test_portable_computer_rejects_invalid_processing():
    with pytest.raises(ValueError, match='Unsupported PortableComputer processing 6'):
        PortableComputer(6)


def test_mid_sized_computer_one_matches_csc_values():
    pc = MidSizedComputer(1)
    assert pc.tl == 7
    assert pc.mass_kg == 50.0
    assert pc.cost == 50_000.0


def test_mid_sized_computer_four_matches_csc_values():
    pc = MidSizedComputer(4)
    assert pc.tl == 10
    assert pc.mass_kg == 5.0
    assert pc.cost == 10_000.0


def test_mid_sized_computer_rejects_invalid_processing():
    with pytest.raises(ValueError, match='Unsupported MidSizedComputer processing 5'):
        MidSizedComputer(5)


def test_computer_can_run_within_processing():
    pc = PortableComputer(3)
    assert pc.can_run(Security(2), Translator(1))


def test_computer_cannot_run_exceeding_processing():
    pc = PortableComputer(2)
    assert not pc.can_run(Security(2), Translator(1))


def test_computer_can_run_bandwidth_zero_packages_always_fit():
    pc = PortableComputer(0)
    assert pc.can_run(Interface(), Security(0))


def test_tablet_matches_csc_values():
    t = Tablet(1)
    assert t.tl == 9
    assert t.mass_kg == 0.25
    assert t.cost == 125.0


def test_tablet_rejects_invalid_processing():
    with pytest.raises(ValueError, match='Unsupported Tablet processing 6'):
        Tablet(6)


def test_mobile_comm_matches_csc_values():
    m = MobileComm(2)
    assert m.tl == 12
    assert m.mass_kg == 0.0
    assert m.cost == 125.0


def test_computer_chip_matches_csc_values():
    c = ComputerChip(3)
    assert c.tl == 15
    assert c.mass_kg == 0.0
    assert c.cost == 125.0


def test_microscopic_chip_matches_csc_values():
    c = MicroscopicChip(5)
    assert c.tl == 18
    assert c.mass_kg == 0.0
    assert c.cost == 312.5


def test_size_variants_can_run_like_base():
    assert Tablet(3).can_run(Security(2), Translator(1))
    assert not MobileComm(2).can_run(Security(2), Translator(1))
