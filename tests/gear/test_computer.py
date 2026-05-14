import pytest

from ceres.gear.computer import (
    ComputerChip,
    ComputerTerminal,
    InterfaceDevice,
    MainframeComputer,
    MicroscopicChip,
    MidSizedComputer,
    PortableComputer,
    SpecialisedComputer,
    SpecialisedTablet,
    Tablet,
)
from ceres.gear.software import Expert


def test_portable_computer_zero_matches_csc_values():
    pc = PortableComputer(processing=0)
    assert pc.tl == 7
    assert pc.mass_kg == 5.0
    assert pc.cost == 500.0


def test_portable_retro_computer_is_not_supported():
    with pytest.raises(ValueError, match='Retro-tech not supported for PortableComputer'):
        PortableComputer(processing=0, tl=9)


def test_portable_computer_three_matches_csc_values():
    pc = PortableComputer(processing=3)
    assert pc.tl == 12
    assert pc.mass_kg == 0.5
    assert pc.cost == 1_000.0


def test_portable_proto_1_computer_three_matches_csc_values():
    pc = PortableComputer(processing=3, tl=11)
    assert pc.tl == 11
    assert pc.mass_kg == 5.0
    assert pc.cost == 10_000.0


def test_portable_proto_2_computer_three_matches_csc_values():
    pc = PortableComputer(processing=3, tl=10)
    assert pc.tl == 10
    assert pc.mass_kg == 50.0
    assert pc.cost == 100_000.0


def test_portable_proto_3_computer_fails():
    with pytest.raises(ValueError, match='Proto tech not available for 3 TLs'):
        PortableComputer(processing=3, tl=9)


def test_portable_computer_rejects_invalid_processing():
    with pytest.raises(ValueError, match='Unsupported PortableComputer processing 6'):
        PortableComputer(processing=6)


def test_mid_sized_computer_one_matches_csc_values():
    pc = MidSizedComputer(processing=1)
    assert pc.tl == 7
    assert pc.mass_kg == 50.0
    assert pc.cost == 50_000.0


def test_mid_sized_computer_four_matches_csc_values():
    pc = MidSizedComputer(processing=4)
    assert pc.tl == 10
    assert pc.mass_kg == 5.0
    assert pc.cost == 10_000.0


def test_mid_sized_computer_rejects_invalid_processing():
    with pytest.raises(ValueError, match='Unsupported MidSizedComputer processing 5'):
        MidSizedComputer(processing=5)


def test_tablet_matches_csc_values():
    t = Tablet(processing=1)
    assert t.tl == 9
    assert t.mass_kg == 0.25
    assert t.cost == 125.0


def test_tablet_rejects_invalid_processing():
    with pytest.raises(ValueError, match='Unsupported Tablet processing 6'):
        Tablet(processing=6)


def test_tablet_rejects_retro_tech():
    with pytest.raises(ValueError, match='Retro-tech not supported for Tablet'):
        Tablet(processing=1, tl=11)


def test_tablet_rejects_proto_tech():
    with pytest.raises(ValueError, match='Proto-tech not supported for Tablet'):
        Tablet(processing=1, tl=8)


def test_computer_chip_rejects_retro_tech():
    with pytest.raises(ValueError, match='Retro-tech not supported for ComputerChip'):
        ComputerChip(processing=1, tl=13)


def test_computer_chip_rejects_proto_tech():
    with pytest.raises(ValueError, match='Proto-tech not supported for ComputerChip'):
        ComputerChip(processing=1, tl=10)


def test_microscopic_chip_rejects_retro_tech():
    with pytest.raises(ValueError, match='Retro-tech not supported for MicroscopicChip'):
        MicroscopicChip(processing=1, tl=14)


def test_microscopic_chip_rejects_proto_tech():
    with pytest.raises(ValueError, match='Proto-tech not supported for MicroscopicChip'):
        MicroscopicChip(processing=1, tl=11)


def test_computer_terminal_matches_csc_values():
    t = ComputerTerminal(processing=0)
    assert t.tl == 6
    assert t.mass_kg == 2.0
    assert t.cost == 200.0


def test_interface_device_matches_csc_values():
    d = InterfaceDevice(processing=0)
    assert d.tl == 8
    assert d.mass_kg == 0.0
    assert d.cost == 100.0


def test_mainframe_basic_matches_csc_values():
    m = MainframeComputer(processing=0)
    assert m.tl == 5
    assert m.mass_kg == 5_000.0
    assert m.cost == 2_000_000.0


def test_mainframe_advanced_matches_csc_values():
    m = MainframeComputer(processing=2)
    assert m.tl == 7
    assert m.mass_kg == 1_000.0
    assert m.cost == 5_000_000.0


def test_computer_chip_matches_csc_values():
    c = ComputerChip(processing=3)
    assert c.tl == 15
    assert c.mass_kg == 0.0
    assert c.cost == 125.0


def test_microscopic_chip_matches_csc_values():
    c = MicroscopicChip(processing=3)
    assert c.tl == 16
    assert c.mass_kg == 0.0
    assert c.cost == 62.5


def test_specialised_portable_ii_admin_cost():
    sc = SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Admin'), variant='intelligent_interface')
    assert sc.tl == 8
    assert sc.mass_kg == 2.0
    assert sc.cost == 1_350.0  # 5 * 250 + 100


def test_specialised_portable_intellect_broker3_cost():
    sc = SpecialisedComputer(processing=3, expert=Expert(rating=3, skill='Broker'), variant='intellect')
    assert sc.tl == 12
    assert sc.mass_kg == 0.5
    assert sc.cost == 30_000.0  # 10 * 1000 + 100 * 200


def test_specialised_portable_ii_astrogation2_cost():
    sc = SpecialisedComputer(
        processing=2, expert=Expert(rating=2, skill='Astrogation'), variant='intelligent_interface'
    )
    assert sc.tl == 13  # max(PC/2 TL10, Expert Astrogation/2 TL13)
    assert sc.cost == 5 * 500.0 + 5_000.0  # 5 * Cr500 + Expert Astrogation/2


def test_specialised_computer_insufficient_processing_gives_error_note():
    sc = SpecialisedComputer(processing=1, expert=Expert(rating=3, skill='Admin'), variant='intellect')
    error_notes = [n for n in sc.notes if n.category == 'error']
    assert len(error_notes) == 1
    assert 'Processing 1' in error_notes[0].message
    assert 'Admin/3' in error_notes[0].message


def test_specialised_ii_computer_has_one_info_note():
    sc = SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Admin'), variant='intelligent_interface')
    info_notes = [n for n in sc.notes if n.category == 'info']
    assert len(info_notes) == 1
    assert 'DM+1 on Admin' in info_notes[0].message
    assert 'Average (8+)' in info_notes[0].message


def test_specialised_intellect_computer_has_two_info_notes():
    sc = SpecialisedComputer(processing=3, expert=Expert(rating=3, skill='Broker'), variant='intellect')
    info_notes = [n for n in sc.notes if n.category == 'info']
    assert len(info_notes) == 2
    assert 'DM+1 on Broker' in info_notes[0].message
    assert 'Very Difficult (12+)' in info_notes[0].message
    assert 'Broker-2 for unskilled' in info_notes[1].message
    assert 'Very Difficult (12+)' in info_notes[1].message


def test_specialised_tablet_intellect_medic_cost():
    sc = SpecialisedTablet(processing=2, expert=Expert(rating=2, skill='Medic'), variant='intellect')
    assert sc.tl == 11
    assert sc.mass_kg == 0.25
    assert sc.cost == 10 * 250.0 + 2_000.0  # 10 * Cr250 + Expert Medic/2


def test_specialised_computer_processing_in_part():
    sc = SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Admin'), variant='intelligent_interface')
    assert sc.parts[0].processing == 1


def test_specialised_tablet_processing_in_part():
    sc = SpecialisedTablet(processing=3, expert=Expert(rating=1, skill='Steward'), variant='intelligent_interface')
    assert sc.parts[0].processing == 3
    assert sc.tl == 13


def test_specialised_computer_item_note_full_name():
    sc = SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Admin'), variant='intelligent_interface')
    assert sc.notes[0].message == 'Specialised Portable Computer Admin/1 Intelligent Interface'


def test_specialised_tablet_item_note_full_name():
    sc = SpecialisedTablet(processing=2, expert=Expert(rating=2, skill='Broker'), variant='intellect')
    assert sc.notes[0].message == 'Specialised Tablet Broker/2 Intellect'


def test_specialised_computer_roundtrip():
    sc = SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Admin'), variant='intelligent_interface')
    sc2 = SpecialisedComputer.model_validate_json(sc.model_dump_json())
    assert sc2.cost == 1_350.0
    assert sc2.expert.skill == 'Admin'
    assert sc2.parts[0].processing == 1


def test_specialised_tablet_roundtrip():
    sc = SpecialisedTablet(processing=2, expert=Expert(rating=2, skill='Broker'), variant='intellect')
    sc2 = SpecialisedTablet.model_validate_json(sc.model_dump_json())
    assert sc2.cost == sc.cost
    assert sc2.expert.skill == 'Broker'
    assert sc2.parts[0].processing == 2


def test_portable_computer_is_equipment():
    from ceres.shared import Equipment

    pc = PortableComputer(processing=3)
    assert isinstance(pc, Equipment)


def test_portable_computer_processing_lives_in_part():
    pc = PortableComputer(processing=3)
    assert pc.parts[0].processing == 3


def test_portable_computer_part_tl_matches_equipment_tl():
    pc = PortableComputer(processing=3)
    assert pc.parts[0].tl == pc.tl


def test_portable_computer_roundtrip():
    pc = PortableComputer(processing=3)
    pc2 = PortableComputer.model_validate_json(pc.model_dump_json())
    assert pc2.tl == 12
    assert pc2.cost == 1_000.0
    assert pc2.mass_kg == 0.5
    assert pc2.parts[0].processing == 3
