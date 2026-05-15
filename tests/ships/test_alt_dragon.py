"""Reference ship case based on refs/tycho/alt_dragon.txt.

Purpose:
- preserve a source-derived alternate military Dragon variant
- exercise additional optional systems such as emergency power, rapid
  deployment arrays, biosphere support, autodoc, cabin space, and upgraded
  computing
- keep one explicit case where the source crew manifest is preserved verbatim
  while the remaining economic mismatches are called out rather than hidden

Source handling for this test case:
- supported: hull, stealth, radiation shielding, armour, drives, power,
  emergency power, fuel, bridge, most systems, habitation layout, crew
  manifest, fuel expense, and major power figures
- ignored for test-case modelling:
  - battle-load figures (`TCS-002`)
  - income / profit rows (`TCS-003`)
- normalized when mapping into Ceres:
  - source armored-bulkhead rows are represented as protected parts plus
    separate Hull bulkhead entries (`TCS-001`)
- deliberate interpretation:
  - the source crew manifest is preserved verbatim as explicit `ship.crew.roles` data
  - Ceres surfaces crew-rule mismatches as info/warning notes instead of
    silently normalizing the crew
  - point-defence batteries do not require dedicated gunners
- retro computer pricing from CSC-style `Retro*` source rows (`RIS-005`) is now modelled:
  - Core/40/fib uses retro_levels=2 (TL13 ship, effective TL 11 covers installed software): cost ÷4
  - Computer/20/fib uses retro_levels=1 (TL13 ship, 1 above TL12 standard): cost ÷2
  - retro_levels=2 (not 4) is chosen because effective TL 11 is the minimum needed to run
    AutoRepair/1 and FireControl/2 (both TL11) without software-TL warnings; retro_levels=4
    would drop the effective TL to 9, invalidating all TL10+ software on a military ship
- source inconsistency:
  - the source life-support total matches facilities alone and appears to omit
    life support for people entirely
- model interpretation rather than dedicated installed rows:
  - stores and spares (`RIS-001`)
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer20, ComputerSection, Core40
from ceres.make.ship.crew import (
    Captain,
    Engineer,
    Gunner,
    Maintenance,
    Medic,
    Officer,
    Pilot,
    SensorOperator,
    ShipCrew,
)
from ceres.make.ship.drives import (
    DriveSection,
    EmergencyPowerSystem,
    FusionPlantTL12,
    MDrive7,
    PowerSection,
)
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, CabinSpace, HabitationSection, Stateroom
from ceres.make.ship.hull import ImprovedStealth
from ceres.make.ship.parts import Advanced, Budget, HighTechnology, IncreasedSize, SizeReduction
from ceres.make.ship.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ImprovedSensors,
    RapidDeploymentExtendedArrays,
    SensorsSection,
)
from ceres.make.ship.software import (
    AutoRepair,
    Evade,
    FireControl,
)
from ceres.make.ship.storage import CargoSection, FuelProcessor, FuelSection, OperationFuel
from ceres.make.ship.systems import (
    Airlock,
    Armoury,
    BasicAutodoc,
    Biosphere,
    CommonArea,
    MedicalBay,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    Workshop,
)
from ceres.make.ship.weapons import (
    LaserPointDefenseBattery2,
    MissileStorage,
    ParticleBarbette,
    SmallMissileBay,
    WeaponsSection,
)
from ceres.report import render_ship_html

from ._output import write_html_output, write_json_output

# Values taken from refs/tycho/alt_dragon.txt unless noted.
_expected = SimpleNamespace(
    plant_tons=26.16,  # ref: Fusion TL 12 Output: 436 Reduced Size — 26.16 tons
    plant_cost_mcr=31.9733333333,  # ref: 31,973,333.33
    emergency_power_tons=2.616,  # ref: Emergency Power System — 2.62 tons (Ceres: 2.616)
    emergency_power_cost_mcr=3.1973333333,  # ref: 3,197,333.33
    operation_fuel_tons=11.0,  # ref: 16 Weeks of Operation — 10.46 tons; Ceres rounds up to 11.0
    fuel_processor_tons=1.0,  # ref: Fuel Processor 20 Tons Per Day — 1.00 ton
    # ref shows Core/40/fib (Retro*): 4,218,750 — that is ÷16 (retro_levels=4 implied by tool).
    # Ceres uses retro_levels=2 (÷4) per RIS-005 to keep effective TL ≥ 11 for AutoRepair/1 and
    # FireControl/2; base cost 67,500,000 ÷ 4 = 16,875,000
    computer_cost_mcr=16.875,  # ref: 4,218,750 (retro×4); Ceres: 16,875,000 (retro×2, RIS-005)
    # ref: 1x 1.82 Ton Cargo Bay (1.82) + Stores and Spares 4.48 = 6.30 total;
    # Ceres treats stores as guidance (RIS-001); remaining usable tonnage gives 5.8616
    cargo_tons=5.8616,  # ref: ~6.30; Ceres gives 5.8616 (fuel tons rounding, RIS-001)
    # ref: Design Cost 293,083,146.67; Ceres gives higher because computer cost
    # uses retro_levels=2 instead of retro_levels=4 (RIS-005)
    production_cost_mcr=305.7193966667,  # ref: 293,083,146.67; Ceres: 305,719,396.67 (RIS-005)
    sales_price_mcr=275.1474570,  # ref: 263,774,832.00; Ceres: 275,147,457.00 (RIS-005)
    available_power=436.0,  # ref: Available: 436 PP
    sensor_power_load=15.0,  # ref: Sensors 15 PP
    total_power_load=436.0,  # ref: Maximum Load 436 PP
)


def build_alt_dragon() -> ship.Ship:
    """Build the alternate Dragon reference case from refs/tycho/alt_dragon.txt."""

    fusion_plant = FusionPlantTL12(
        output=436, customisation=Advanced(modifications=[SizeReduction]), armoured_bulkhead=True
    )

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat, Alternate',
        military=True,
        tl=13,
        displacement=400,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull.model_copy(
                update={'reinforced': True},
            ),
            stealth=ImprovedStealth(),
            radiation_shielding=True,
            armour=armour.CrystalironArmour(protection=13),
            armoured_bulkheads=[],
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(
            m_drive=MDrive7(customisation=Budget(modifications=[IncreasedSize]), armoured_bulkhead=True)
        ),
        power=PowerSection(
            plant=fusion_plant,
            emergency_power_system=EmergencyPowerSystem.from_fusion_plant(fusion_plant),
        ),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=16, armoured_bulkhead=True),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge(holographic=True, armoured_bulkhead=True)),
        computer=ComputerSection(
            hardware=Core40(fib=True, retro_levels=2),
            backup_hardware=Computer20(fib=True, retro_levels=1),
            software=[AutoRepair(rating=1), FireControl(rating=2), Evade(rating=1)],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            extended_arrays=RapidDeploymentExtendedArrays(),
        ),
        weapons=WeaponsSection(
            barbettes=[
                ParticleBarbette(customisation=Advanced(modifications=[SizeReduction]), armoured_bulkhead=True),
                ParticleBarbette(customisation=Advanced(modifications=[SizeReduction]), armoured_bulkhead=True),
            ],
            bays=[
                SmallMissileBay(
                    customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[
                LaserPointDefenseBattery2(customisation=Advanced(modifications=[SizeReduction]), armoured_bulkhead=True)
            ],
            missile_storage=MissileStorage(count=720, armoured_bulkhead=True),
        ),
        systems=SystemsSection(
            internal_systems=[
                Armoury(),
                Biosphere(tons=4.0),
                MedicalBay(autodoc=BasicAutodoc()),
                TrainingFacility(trainees=2),
                Workshop(),
            ],
            drones=[RepairDrones()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 4,
            cabin_space=CabinSpace(tons=15.0),
            common_area=CommonArea(tons=10.0),
            entertainment=AdvancedEntertainmentSystem(cost=1_250),
        ),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 3,
                *[Engineer()] * 2,
                Maintenance(),
                Medic(),
                *[Gunner()] * 5,
                *[SensorOperator()] * 3,
                Officer(),
            ]
        ),
    )


def test_alt_dragon_modeled_subset_tracks_current_model():
    dragon = build_alt_dragon()

    assert dragon.power is not None
    assert dragon.power.plant is not None
    assert dragon.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert dragon.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)
    assert dragon.power.emergency_power_system is not None
    assert dragon.power.emergency_power_system.tons == pytest.approx(_expected.emergency_power_tons)
    assert dragon.power.emergency_power_system.cost == pytest.approx(_expected.emergency_power_cost_mcr * 1_000_000)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)
    assert dragon.fuel.fuel_processor is not None
    assert dragon.fuel.fuel_processor.build_item() == 'Fuel Processor (20 tons/day)'
    assert dragon.fuel.fuel_processor.tons == pytest.approx(_expected.fuel_processor_tons)

    assert dragon.computer is not None
    assert dragon.computer.hardware is not None
    assert dragon.computer.hardware.build_item() == 'Core/40/fib'
    assert dragon.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)  # retro-2: ÷4

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(_expected.cargo_tons)
    crew_infos = dragon.crew.notes.infos
    assert 'MAINTENANCE above recommended count: 1 > 0' in crew_infos
    assert 'MEDIC above recommended count: 1 > 0' in crew_infos

    assert dragon.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert dragon.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)
    assert dragon.available_power == pytest.approx(_expected.available_power)
    assert dragon.sensor_power_load == pytest.approx(_expected.sensor_power_load)
    assert dragon.total_power_load == pytest.approx(_expected.total_power_load)


def test_alt_dragon_has_no_errors():
    dragon = build_alt_dragon()
    assert not dragon.notes.errors


@pytest.mark.generated_output
def test_alt_dragon_report_html_output():
    dragon = build_alt_dragon()
    html = render_ship_html(dragon)
    write_html_output('test_alt_dragon', html)
    write_json_output('test_alt_dragon', dragon)

    assert '<title>Dragon</title>' in html
    assert '<p class="banner-meta">System Defense Boat, Alternate | TL13 | Hull 176</p>' in html
    assert '<header class="sidebar-card-title">Crew</header>' in html
    assert '<header class="sidebar-card-title">Power</header>' in html
    assert '<header class="sidebar-card-title">Costs</header>' in html
    assert 'Radiation Shielding: Reduce Rads by 1,000' in html
    assert 'Small Missile Bay (12 missiles per salvo)' in html
    assert 'Magazine: 144 missiles (12 full salvos)' in html
    assert 'High Technology: Size Reduction × 3' in html
    assert 'Life Support Facilities' in html
    assert 'Armoured Bulkheads<div class="admonition' in html
    assert 'Critical hit severity reduced by 1 if critical hit severity &gt;1' in html
    assert 'Improved Sensors' in html
    assert '<p class="eyebrow">' not in html
