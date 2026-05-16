"""Spinward Extents Acrux-class Heavy Cruiser source snapshot.

The source image header says `Acrux Heavy Cruiser`, while the class ribbon says
`Class: Heavy Scout`. The latter is retained here as a source value but treated
as a likely layout/copy error until a text source confirms otherwise.

This is a future capstone validation case rather than a buildable Ceres ship
today. It exercises several systems that are not fully modelled yet, including
spinal particle accelerators, command bridges at capital-ship scale, large
weapon bay groups with size reduction, point defence batteries, repair drones,
UNREP systems, and large craft berthing.
"""

from types import SimpleNamespace

import pytest

_expected = SimpleNamespace(
    source='Spinward Extents',
    ship_class='Acrux',
    ship_type='Heavy Cruiser',
    source_class_ribbon='Heavy Scout',
    source_class_ribbon_note='Likely source layout/copy error; title and caption say Acrux Heavy Cruiser.',
    tl=11,
    displacement=50_000,
    hull_description='50,000 tons, Close Structure, Reinforced, Radiation Shielding',
    hull_cost_mcr=4_625.0,
    hull_points=30_250,
    running_cost_maintenance_mcr=2.102215,
    purchase_cost_mcr=25_226.575,
    rows=(
        SimpleNamespace(section='Hull', item='50,000 tons, Close Structure, Reinforced', tons=None, cost_mcr=3375.0),
        SimpleNamespace(section='Hull', item='Radiation Shielding', tons=None, cost_mcr=1250.0),
        SimpleNamespace(section='Armour', item='Crystaliron, Armour 11', tons=6875.0, cost_mcr=1856.25),
        SimpleNamespace(section='M-Drive', item='Thrust 5', tons=2500.0, cost_mcr=5000.0),
        SimpleNamespace(section='J-Drive', item='Jump 2', tons=2505.0, cost_mcr=3757.5),
        SimpleNamespace(
            section='Power Plant', item='Fusion (TL8) (size reduction x3), Power: 52,500', tons=3676.0, cost_mcr=2756.25
        ),
        SimpleNamespace(section='Fuel Tanks', item='J-2, 8 weeks of operation', tons=10735.0, cost_mcr=None),
        SimpleNamespace(section='Bridge', item='Holographic Controls', tons=60.0, cost_mcr=312.5),
        SimpleNamespace(section='Bridge', item='Command, Holographic Controls', tons=80.0, cost_mcr=468.75),
        SimpleNamespace(section='Computer', item='Core/60 (primary)', tons=None, cost_mcr=75.0),
        SimpleNamespace(section='Computer', item='Core/50 (backup)', tons=None, cost_mcr=60.0),
        SimpleNamespace(section='Sensors', item='Military Grade x2', tons=4.0, cost_mcr=8.2),
        SimpleNamespace(section='Sensors', item='Distributed Arrays x2', tons=8.0, cost_mcr=16.4),
        SimpleNamespace(section='Sensors', item='Improved Signal Processing x2', tons=2.0, cost_mcr=8.0),
        SimpleNamespace(section='Weapons', item='Particle Accelerator Spinal Mount', tons=7000.0, cost_mcr=2000.0),
        SimpleNamespace(
            section='Weapons', item='Large Missile Bays (size reduction x3) x5', tons=1750.0, cost_mcr=937.5
        ),
        SimpleNamespace(
            section='Weapons', item='Large Torpedo Bays (size reduction x2) x5', tons=2000.0, cost_mcr=187.5
        ),
        SimpleNamespace(section='Weapons', item='Medium Particle Beam Bays x10', tons=1000.0, cost_mcr=400.0),
        SimpleNamespace(section='Weapons', item='Particle Barbettes x50', tons=250.0, cost_mcr=400.0),
        SimpleNamespace(section='Weapons', item='Plasma Barbettes x40', tons=200.0, cost_mcr=200.0),
        SimpleNamespace(
            section='Weapons', item='Triple Turrets (long range pulse lasers) x120', tons=120.0, cost_mcr=570.0
        ),
        SimpleNamespace(section='Weapons', item='Triple Turrets (beam lasers) x90', tons=90.0, cost_mcr=225.0),
        SimpleNamespace(section='Weapons', item='Triple Turrets (sandcasters) x60', tons=60.0, cost_mcr=105.0),
        SimpleNamespace(section='Weapons', item='Point Defence Batteries (type I) x10', tons=200.0, cost_mcr=50.0),
        SimpleNamespace(section='Ammunition', item='Missile Storage (28,800 missiles)', tons=2400.0, cost_mcr=None),
        SimpleNamespace(section='Ammunition', item='Torpedo Storage (7,200 torpedoes)', tons=2400.0, cost_mcr=None),
        SimpleNamespace(section='Ammunition', item='Sandcaster Storage (4,800 canisters)', tons=240.0, cost_mcr=None),
        SimpleNamespace(section='Systems', item='Fuel Scoops', tons=None, cost_mcr=1.0),
        SimpleNamespace(section='Systems', item='Fuel Processor (5,000 tons/day)', tons=250.0, cost_mcr=12.5),
        SimpleNamespace(section='Systems', item='Emergency Power', tons=367.5, cost_mcr=275.625),
        SimpleNamespace(section='Systems', item='Repair Drones', tons=500.0, cost_mcr=100.0),
        SimpleNamespace(section='Systems', item='Barracks (150 troops)', tons=300.0, cost_mcr=15.0),
        SimpleNamespace(section='Systems', item='Brigs x4', tons=16.0, cost_mcr=1.0),
        SimpleNamespace(section='Systems', item='Armoury', tons=50.0, cost_mcr=12.5),
        SimpleNamespace(section='Systems', item='Briefing Rooms x4', tons=16.0, cost_mcr=2.0),
        SimpleNamespace(section='Systems', item='Cargo Crane', tons=4.0, cost_mcr=4.0),
        SimpleNamespace(section='Systems', item='Medical Bays x6', tons=24.0, cost_mcr=12.0),
        SimpleNamespace(section='Systems', item='Training Facilities (50 personnel)', tons=100.0, cost_mcr=20.0),
        SimpleNamespace(section='Systems', item='UNREP System (500 tons/hour)', tons=25.0, cost_mcr=12.5),
        SimpleNamespace(section='Systems', item='Workshops x17', tons=102.0, cost_mcr=15.3),
        SimpleNamespace(section='Craft', item='Docking Space (1080 tons)', tons=1188.0, cost_mcr=297.0),
        SimpleNamespace(section='Craft', item='Full Hangar (360 tons)', tons=720.0, cost_mcr=144.0),
        SimpleNamespace(section='Staterooms', item='Standard x272', tons=1088.0, cost_mcr=136.0),
        SimpleNamespace(section='Staterooms', item='High x4', tons=24.0, cost_mcr=3.2),
        SimpleNamespace(section='Staterooms', item='Additional Crew (standard) x65', tons=260.0, cost_mcr=32.5),
        SimpleNamespace(section='Staterooms', item='Additional Crew (high) x5', tons=30.0, cost_mcr=4.0),
        SimpleNamespace(section='Staterooms', item='Low Berths x20', tons=10.0, cost_mcr=1.0),
        SimpleNamespace(section='Software', item='Manoeuvre/0', tons=None, cost_mcr=None),
        SimpleNamespace(section='Software', item='Library', tons=None, cost_mcr=None),
        SimpleNamespace(section='Software', item='Intellect', tons=None, cost_mcr=1.0),
        SimpleNamespace(section='Software', item='Auto-Repair/1', tons=None, cost_mcr=5.0),
        SimpleNamespace(section='Software', item='Evade/2', tons=None, cost_mcr=2.0),
        SimpleNamespace(section='Software', item='Advanced Fire Control/1', tons=None, cost_mcr=12.0),
        SimpleNamespace(section='Software', item='Anti-Hijack/1', tons=None, cost_mcr=6.0),
        SimpleNamespace(section='Software', item='Battle System/1', tons=None, cost_mcr=18.0),
        SimpleNamespace(section='Software', item='Electronic Warfare/1', tons=None, cost_mcr=15.0),
        SimpleNamespace(section='Software', item='Launch Solution/2', tons=None, cost_mcr=12.0),
        SimpleNamespace(section='Software', item='Virtual Crew/0', tons=None, cost_mcr=1.0),
        SimpleNamespace(section='Common Areas', item='Common Areas', tons=346.0, cost_mcr=34.6),
        SimpleNamespace(section='Cargo', item='Cargo', tons=424.5, cost_mcr=None),
    ),
    crew=(
        'Captain',
        'Officers x41',
        'Pilots x3',
        'Astrogator',
        'Medics x6',
        'Maintenance x33',
        'Engineers x83',
        "Ship's Troops x150",
        'Administrators x16',
        'Gunners x277',
    ),
    power_requirements=SimpleNamespace(
        basic_ship_systems=10_000,
        manoeuvre_drive=25_000,
        jump_drive=10_000,
        sensors=10,
        weapons=6_945,
    ),
    expected_errors=[],
    expected_warnings=[],
    unimplemented_reasons=(),
)

# Not yet implemented in Ceres.
_expected.unimplemented_reasons = (
    'capital-scale Spinward Extents source snapshot only',
    'particle accelerator spinal mount',
    'weapon bay size reduction groups',
    'point defence batteries',
    'large craft docking and full hangar bundle',
    'large crew/stateroom command model',
)


def build_acrux_heavy_cruiser():
    pytest.skip('Acrux-class Heavy Cruiser is a Spinward Extents source snapshot; Ceres build pending.')


def test_acrux_heavy_cruiser_source_snapshot():
    assert _expected.source == 'Spinward Extents'
    assert _expected.ship_class == 'Acrux'
    assert _expected.ship_type == 'Heavy Cruiser'
    assert _expected.source_class_ribbon == 'Heavy Scout'
    assert _expected.tl == 11
    assert _expected.displacement == 50_000
    assert _expected.hull_points == 30_250
    assert _expected.expected_errors == []
    assert _expected.expected_warnings == []
