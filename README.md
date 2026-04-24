# ceres

**Ceres** builds Mongoose Traveller 2nd Edition starships in Python, using the
[High Guard 2022](https://www.mongoosepublishing.com/products/high-guard-update-2022)
rules. A ship is an ordinary Python object: instantiate `Ship`, pass it part
objects and parameters, and get back a validated design.

A likely use for this is to handd it to an AI and build rules complient Traveller
ships for conversing with the AI.

```python
from tycho import armour, hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer5, ComputerSection, JumpControl2
from tycho.crafts import AirRaft, CraftSection, InternalDockingSpace
from tycho.drives import DriveSection, FusionPlantTL12, JumpDrive2, MDrive2, PowerSection
from tycho.habitation import HabitationSection, Staterooms
from tycho.sensors import MilitarySensors, SensorsSection
from tycho.storage import FuelProcessor, FuelSection, JumpFuel, OperationFuel
from tycho.systems import Airlock, ProbeDrones, SystemsSection, Workshop
from tycho.weapons import MountWeapon, Turret, WeaponsSection

scout = ship.Ship(
    ship_class='Suleiman',
    ship_type='Scout/Courier',
    tl=12,
    displacement=100,
    design_type=ship.ShipDesignType.STANDARD,
    hull=hull.Hull(
        configuration=hull.streamlined_hull,
        armour=armour.CrystalironArmour(tl=12, protection=4),
        airlocks=[Airlock()],
    ),
    drives=DriveSection(m_drive=MDrive2(), jump_drive=JumpDrive2()),
    power=PowerSection(fusion_plant=FusionPlantTL12(output=60)),
    fuel=FuelSection(
        jump_fuel=JumpFuel(parsecs=2),
        operation_fuel=OperationFuel(weeks=12),
        fuel_processor=FuelProcessor(tons=2),
    ),
    command=CommandSection(bridge=Bridge()),
    computer=ComputerSection(hardware=Computer5(bis=True), software=[JumpControl2()]),
    sensors=SensorsSection(primary=MilitarySensors()),
    weapons=WeaponsSection(
        turrets=[
            Turret(
                size='double',
                weapons=[
                    MountWeapon(weapon='beam_laser'),
                    MountWeapon(weapon='beam_laser'),
                ],
            )
        ],
    ),
    craft=CraftSection(docking_space=InternalDockingSpace(craft=AirRaft())),
    habitation=HabitationSection(staterooms=Staterooms(count=4)),
    systems=SystemsSection(probe_drones=ProbeDrones(count=10), workshop=Workshop()),
)

print(scout.markdown_table())
```

## What you get

- **Stat sheet** — `ship.markdown_table()` produces a Markdown table matching
  official High Guard stat-block layout (tonnage, power budget, cost in kCr,
  operating expenses, crew salaries).
- **Legality checks** — errors and warnings are embedded as notes on the parts
  that triggered them (negative cargo, missing airlock, TL mismatches, jump
  control/drive mismatches, undersized common area, etc.).
- **Serialization** — the full ship serializes to/from JSON via Pydantic.
  Derived values (cost, tons, power) are recalculated on load so the JSON is
  always a snapshot of the current model, not an authoritative source.

## AI-assisted ship design

Because ship construction follows explicit rules from the High Guard rulebook,
an AI assistant with access to those rules can generate correct `Ship`
definitions from a plain-text description and produce a fully costed,
rule-checked stat sheet without manual calculation. The `refs/` directory
holds your copies of the relevant PDFs for this purpose.

## Development

```bash
uv run pytest --cov=tycho --cov-report=term-missing   # tests + coverage
uvx ruff check --fix                                   # lint + auto-fix
uvx ruff format                                        # format
uvx ty check                                           # type check
```

All four must pass before a change is considered complete.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for patterns and technical decisions,
and [AI_README.md](AI_README.md) for contributor guidance (including AI
assistants).
