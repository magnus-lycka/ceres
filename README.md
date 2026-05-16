# ceres

**Ceres** builds Mongoose Traveller 2nd Edition assemblies in Python: starships,
robots, and reusable gear/catalogue items. A design is an ordinary Python
object: instantiate the relevant model, pass it part objects and parameters,
and get back a validated design.

A likely use for this is to hand it to an AI and build rules-compliant
Traveller designs for conversation, tooling, or export.

## Starship example

```python
from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import FuelProcessor, FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import Airlock, ProbeDrones, SystemsSection, Workshop
from ceres.make.ship.weapons import DoubleTurret, WeaponsSection
from ceres.report import render_ship_html

scout = ship.Ship(
    ship_class='Suleiman',
    ship_type='Scout/Courier',
    tl=12,
    displacement=100,
    design_type=ship.ShipDesignType.STANDARD,
    hull=hull.Hull(
        configuration=hull.streamlined_hull,
        armour=armour.CrystalironArmour(protection=4),
        airlocks=[Airlock()],
    ),
    drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
    power=PowerSection(plant=FusionPlantTL12(output=60)),
    fuel=FuelSection(
        jump_fuel=JumpFuel(parsecs=2),
        operation_fuel=OperationFuel(weeks=12),
        fuel_processor=FuelProcessor(tons=2),
    ),
    command=CommandSection(bridge=Bridge()),
    computer=ComputerSection(
        hardware=Computer5(bis=True),
        software=[JumpControl(rating=2)],
    ),
    sensors=SensorsSection(primary=MilitarySensors()),
    weapons=WeaponsSection(turrets=[DoubleTurret()]),
    craft=CraftSection(
        internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))],
    ),
    habitation=HabitationSection(staterooms=[Stateroom()] * 4),
    systems=SystemsSection(internal_systems=[Workshop()], drones=[ProbeDrones(count=10)]),
)

spec = scout.build_spec()
html = render_ship_html(scout)

print(spec.row('M-Drive 2').tons)
print(html[:120])
print(scout.model_dump_json(indent=2)[:240])
```

## Robot example

```python
from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion
from ceres.make.robot.options import DomesticCleaningEquipment, ReconSensor
from ceres.report import render_robot_typst

servant = Robot(
    name='Domestic Servant',
    tl=8,
    size=RobotSize.SIZE_3,
    locomotion=WheelsLocomotion(speed_reduction=1),
    brain=PrimitiveBrain(function='clean'),
    manipulators=[],
    options=[
        DomesticCleaningEquipment(size='small'),
        ReconSensor(quality='improved'),
    ],
)

spec = servant.build_spec()
typst = render_robot_typst(servant)

print(servant.skills_display)
print(typst[:120])
print(servant.model_dump_json(indent=2)[:240])
```

## What you get

- **Structured specs** — designs build sectioned specs with rows, costs, tons,
  power, notes, and domain-specific details such as crew or traits.
- **Renderers** — Ceres can render ships, robots, and gear catalogues from the
  same structured data.
- **Legality checks** — errors and warnings are embedded as notes on the parts
  that triggered them.
- **Reusable gear** — catalogue equipment such as computers and communications
  gear can be rendered on its own and reused by assembly builders.
- **Serialization** — full designs serialize to/from JSON via Pydantic.
  Derived values (cost, tons, power) are recalculated on load so the JSON is
  always a snapshot of the current model, not an authoritative source.

## AI-assisted design

Because Ceres models follow explicit Traveller rules, an AI assistant with
access to those rules can generate Python definitions from a plain-text
description and produce a fully costed, rule-checked stat sheet without manual
calculation.

The `refs/` directory is intentionally gitignored and is expected to exist in a
working copy. Use it for local source material converted to markdown, text,
screenshots, or PDF excerpts. Do not commit copyrighted source material.

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
