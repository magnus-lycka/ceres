# ceres

**Ceres** builds Mongoose Traveller 2nd Edition starships in Python, using the
[High Guard 2022](https://www.mongoosepublishing.com/products/high-guard-update-2022)
rules. A ship is an ordinary Python object: instantiate `Ship`, pass it part
objects and parameters, and get back a validated design.

A likely use for this is to hand it to an AI and build rules-compliant
Traveller ships for conversation, tooling, or export.

```python
from stuart import render_ship_html
from tycho import armour, hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection, JumpControl
from tycho.crafts import AirRaft, CraftSection, InternalDockingSpace
from tycho.drives import DriveSection, FusionPlantTL12, JDrive, MDrive, PowerSection
from tycho.habitation import HabitationSection, Staterooms
from tycho.sensors import MilitarySensors, SensorsSection
from tycho.storage import FuelProcessor, FuelSection, JumpFuel, OperationFuel
from tycho.systems import Airlock, ProbeDrones, SystemsSection, Workshop
from tycho.weapons import Turret, WeaponsSection

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
    drives=DriveSection(m_drive=MDrive(2), j_drive=JDrive(2)),
    power=PowerSection(fusion_plant=FusionPlantTL12(output=60)),
    fuel=FuelSection(
        jump_fuel=JumpFuel(parsecs=2),
        operation_fuel=OperationFuel(weeks=12),
        fuel_processor=FuelProcessor(tons=2),
    ),
    command=CommandSection(bridge=Bridge()),
    computer=ComputerSection(hardware=Computer(5, bis=True), software=[JumpControl(2)]),
    sensors=SensorsSection(primary=MilitarySensors()),
    weapons=WeaponsSection(turrets=[Turret(size='double')]),
    craft=CraftSection(docking_space=InternalDockingSpace(craft=AirRaft())),
    habitation=HabitationSection(staterooms=Staterooms(count=4)),
    systems=SystemsSection(probe_drones=ProbeDrones(count=10), workshop=Workshop()),
)

spec = scout.build_spec()
html = render_ship_html(scout)

print(spec.row('M-Drive 2').tons)
print(html[:120])
print(scout.model_dump_json(indent=2)[:240])
```

## What you get

- **Structured spec** — `ship.build_spec()` produces a `ShipSpec` with sectioned
  rows, crew, passengers, expenses, and notes.
- **Renderers** — Stuart can render ships to HTML, Typst, and PDF from the same
  `ShipSpec`/`Ship` data.
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
uv run pytest                                          # quick suite
uv run pytest --all-tests                             # include slow + generated-output tests
uv run pytest --cov --cov-report=term-missing         # tests + coverage
uvx ruff check --fix                                   # lint + auto-fix
uvx ruff format                                        # format
uvx ty check                                           # type check
```

Default `pytest` skips slow tests and generated-output artifact tests. Use
`--with-slow`, `--with-generated-output`, or `--all-tests` when you want the
full suite.

The usual full gate for local work is `./pre-commit.sh`.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for patterns and technical decisions,
and [AI_README.md](AI_README.md) for contributor guidance (including AI
assistants).

# Fair Use

The Traveller, 2300AD, Twilight: 2000 and Dark
Conspiracy games in all forms are owned by Mongoose
Publishing. Copyright 1977 - 2025 Mongoose
Publishing. Traveller is a registered trademark of
Mongoose Publishing. Mongoose Publishing permits
web sites and fanzines for this game, provided it
contains this notice, that Mongoose Publishing is
notified, and subject to a withdrawal of permission on 90
days notice. The contents of this site are for personal,
non-commercial use only. Any use of Mongoose
Publishing’s copyrighted material or trademarks
anywhere on this web site and its files should not be
viewed as a challenge to those copyrights or
trademarks. In addition, any program/articles/file on this
site cannot be republished or distributed without the
consent of the author who contributed it.