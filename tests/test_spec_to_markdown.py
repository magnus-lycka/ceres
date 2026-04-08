"""
Focused tests for the ShipSpec → markdown rendering contract.

These tests verify that markdown_table() correctly renders spec data, not
that Ship.build_spec() computes correct values.
"""

from typing import Any

from ceres import hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import Computer5, ComputerSection
from ceres.drives import FusionPlantTL12, MDrive1
from ceres.habitation import HabitationSection, Staterooms


def _minimal_ship(**kwargs) -> ship.Ship:
    defaults: dict[str, Any] = dict(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
    )
    defaults.update(kwargs)
    return ship.Ship(**defaults)


def test_heading_format():
    my_ship = _minimal_ship(ship_class='Foo', ship_type='Bar')
    assert '## *Foo* Bar | TL12 | Hull 40' in my_ship.markdown_table()


def test_heading_without_ship_class():
    my_ship = _minimal_ship(ship_type='Unnamed')
    assert '## Unnamed | TL12 | Hull 40' in my_ship.markdown_table()


def test_hull_tons_is_bold():
    my_ship = _minimal_ship()
    table = my_ship.markdown_table()
    assert '| Hull | Streamlined Hull | **100.00** |' in table


def test_power_plant_output_is_bold():
    my_ship = _minimal_ship(fusion_plant=FusionPlantTL12(output=30))
    table = my_ship.markdown_table()
    assert '**30.00**' in table


def test_section_header_shown_on_first_row_in_section():
    my_ship = _minimal_ship(m_drive=MDrive1())
    table = my_ship.markdown_table()
    assert '| Propulsion | ' in table


def test_section_header_collapsed_for_continuation_rows():
    # Hull has at least two rows: hull config + Basic Ship Systems.
    my_ship = _minimal_ship()
    lines = my_ship.markdown_table().splitlines()
    hull_config_idx = next(i for i, line in enumerate(lines) if '| Hull | Streamlined Hull |' in line)
    basic_systems_idx = next(i for i, line in enumerate(lines) if 'Basic Ship Systems' in line)
    assert basic_systems_idx > hull_config_idx
    assert lines[basic_systems_idx].startswith('|  |')


def test_info_note_rendered_with_bullet():
    my_ship = _minimal_ship()
    table = my_ship.markdown_table()
    # Basic sensors always produce an info note
    assert '|  | • ' in table


def test_warning_note_rendered_with_italic_prefix():
    from ceres.systems import Airlock

    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=Staterooms(count=1)),
    )
    table = my_ship.markdown_table()
    assert '|  | *WARNING:* Recommended common area is 1.00 tons |  |  |  |' in table


def test_error_note_rendered_with_bold_prefix():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=Staterooms(count=1)),
    )
    table = my_ship.markdown_table()
    assert '|  | **ERROR:** No airlock installed |  |  |  |' in table


def test_cost_formatted_in_kcr():
    my_ship = _minimal_ship(m_drive=MDrive1())
    table = my_ship.markdown_table()
    # MDrive1 costs 2_000_000 → 2000.00 kCr
    assert '2000.00' in table


def test_expenses_table_present():
    my_ship = _minimal_ship()
    table = my_ship.markdown_table()
    assert '| Cost | Amount |' in table
    assert '| Production Cost |' in table


def test_crew_table_present_when_crew_exists():
    my_ship = _minimal_ship(command=CommandSection(bridge=Bridge()), computer=ComputerSection(hardware=Computer5()))
    table = my_ship.markdown_table()
    assert '| Crew | Salary |' in table
    assert '| PILOT |' in table
