"""Ultralight Fighter - Revised (refs/UltraLightFighter.md)

6-ton TL 12 streamlined fighter.

Expected totals from reference:
  Design Cost:   Cr 6,524,500
  Discount Cost: Cr 5,872,050
  Crew:          1 Pilot
  Power budget:  8 PP available
"""

from ceres import armour, ship
from ceres.bridge import Cockpit
from ceres.computer import Computer
from ceres.drives import FusionPlant, MDrive, OperationFuel
from ceres.sensors import CivilianGradeSensors
from ceres.weapons import FixedFirmpoint, PulseLaser

ultralight_fighter = ship.Ship(
    tl=12,
    displacement=6,
    hull=ship.Hull(
        configuration=ship.streamlined_hull,  # Streamlined-Wedge
        crystaliron_armour=armour.CrystalironArmour(tl=12, protection=6),
        # Expected: 2.16 tons, Cr 432,000
        basic_stealth=ship.BasicStealth(),
        # Expected: 0.12 tons, Cr 240,000
    ),
    m_drive=MDrive(rating=6, budget=True, increased_size=True),
    # Expected: 0.45 tons, Cr 540,000, 4 PP
    fusion_plant=FusionPlant(fusion_tl=12, output=8, budget=True, increased_size=True),
    # Expected: 0.67 tons, Cr 400,000, generates 8 PP
    operation_fuel=OperationFuel(weeks=1),
    # Expected: 0.02 tons, Cr 0
    cockpit=Cockpit(holographic=True),
    # Expected: 1.50 tons, Cr 12,500
    computer=Computer(rating=5),
    # Expected: 0 tons, Cr 30,000
    civilian_sensors=CivilianGradeSensors(),
    # Expected: 1.00 ton, Cr 3,000,000, 1 PP
    fixed_firmpoints=[
        FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True)),
        # Expected: 0 tons, Cr 1,600,000, 2 PP
    ],
)

# Cargo: 0.09 tons (reference); ~0.08 tons computed (rounding differences)

if __name__ == "__main__":
    s = ultralight_fighter
    a = s.hull.crystaliron_armour
    st = s.hull.basic_stealth

    print(f"Ultralight Fighter (Revised) - TL {s.tl}, {s.displacement} tons")
    print(f"Hull cost: {s.hull.configuration.cost(s.displacement):,.0f} CR")
    print(f"Armour: Crystaliron protection {a.protection}, "
          f"{float(a.tons):.2f} tons (exp 2.16), "
          f"{int(a.cost):,} CR (exp 432,000)")
    print(f"Stealth: {st.description}, "
          f"{float(st.tons):.2f} tons (exp 0.12), "
          f"{int(st.cost):,} CR (exp 240,000)")
    print()
    for label, part in [
        ("M-Drive", s.m_drive),
        ("Fusion Plant", s.fusion_plant),
        ("Fuel", s.operation_fuel),
        ("Cockpit", s.cockpit),
        ("Computer", s.computer),
        ("Sensors", s.civilian_sensors),
    ]:
        print(f"  {label}: {float(part.tons):.4f} tons, "
              f"{int(part.cost):,} CR, {float(part.power):.0f} PP")
    for fp in s.fixed_firmpoints:
        print(f"  Fixed Firmpoint: {float(fp.tons):.4f} tons, "
              f"{int(fp.cost):,} CR, {float(fp.power):.0f} PP")
    print()
    print(f"Cargo: {float(s.cargo):.4f} tons (ref: 0.09)")
    print()
    print("--- JSON ---")
    print(s.model_dump_json(indent=2))
