# Decision record: `ceres.make.robot`

> Ursprunglig plan genomförd. Filen arkiverades 2026-05-16.
> Öppna utvidgningar lever i egna plandokument, se nedan.

## Vad som byggdes

`ceres.make.robot` är ett paket för att deklarativt modellera Mongoose Traveller-robotar
enligt samma mönster som `ceres.make.ship`. En robot instansieras med del-objekt och
returnerar ett validerat design-objekt med beräknade egenskaper.

### Paketstruktur (fas 1–4 — klart)

```text
src/ceres/make/robot/
  __init__.py
  base.py        # RobotBase: tl, size, locomotion, parts_of_type()
  robot.py       # Robot aggregate, build_notes(), build_spec(), _build_detail_sections()
  spec.py        # RobotSpec, RobotSpecRow, RobotSpecSection, RobotDetailSection
  chassis.py     # RobotSize(IntEnum) tabell, base_slots/hits/cost, armour, endurance
  locomotion.py  # discriminated union: None/Wheels/Tracks/Grav/Walker/m.fl.
  parts.py       # RobotPartMixin + RobotPart, slot/cost/TL-helpers
  options.py     # zero-slot och slottade options, default suite, default_suite_item_cost
  brain.py       # Primitive/Basic/Advanced/VeryAdvanced; INT-upgrade; BW-upgrade (validerat fält)
  skills.py      # SkillPackage, SkillGrant, primitive_package_skills
  text.py        # format_traits, format_credits
```

### Teststruktur (fas 4–5 — klart)

```text
tests/make/robot/
  test_chassis.py, test_locomotion.py, test_options.py
  test_brain.py, test_skills.py, test_robot.py, test_serialization.py

tests/robots/
  test_domestic_servant.py
  test_lab_control_robot_basic.py
  test_lab_control_robot_advanced.py
  test_utility_droid.py
  test_basic_courier.py
  test_ag300.py
  test_gallery.py           # JSON + Typst + PDF (slow) per robot
  test_gallery_coverage.py  # säkerställer att alla test_*.py-filer ingår i galleriet
```

### Genomförda fas 1–5

- **Fas 1**: `RobotSize`, `RobotBase`, locomotion-union, `RobotPartMixin`/`RobotPart`,
  `Robot`, `available_slots`, `used_slots`, `base_hits`, `base_armour`, `base_endurance`.
- **Fas 2**: Primitive, Basic, Advanced och Very Advanced brains; INT-upgrade;
  Brain Bandwidth Upgrade (validerat `bandwidth`-fält med BW-upgrade-tabell och kostnad);
  skill packages; bandwidth accounting; `+N Bandwidth available` i skills-raden.
- **Fas 3**: Default Suite, zero-slot och slottade options för Domestic Servant och
  Lab Control; slot- och zero-slot-kapacitetskoll; skill grants från options.
- **Fas 4**: `build_spec()` med alla standardrader; Finalisation-sektion i detail;
  `build_notes()` med error/info för slots, bandwidth och Basic Cost-golv;
  robot-galleri med JSON/Typst/PDF-artefakter.
- **Fas 5**: Utility Droid (walker, manipulatorer), Basic Courier (grav, flyer-traits),
  AG300 (extra manipulatorer, storage, sensorer).

### Completion definition (uppfylld)

- ✅ Domestic Servant och Basic Lab Control byggs med Python-objekt.
- ✅ Stat blocks matchar källans rader för hits, locomotion, speed, TL, cost,
  skills, attacks, manipulators, endurance, traits, programming, options.
- ✅ Slot-, TL- och bandwidth-overloads ger notes.
- ✅ JSON round-trip bevarar design-input och konkreta typer.
- ✅ Deriverade värden räknas om efter laddning — inga cached input-fält.
- ✅ Mikro-/nano-/stora robotar är medvetet exkluderade utan halvfärdiga specialfall.

## Öppna avvikelser mot källdata

Fyra robot-exempel har okänd kostnadsrabatt (~10–15%) i källan jämfört med
Ceres-beräkning. Dokumenterat som RIR-002 i `docs/RULE_INTERPRETATIONS.md`.

## Uppskjutna utvidgningar

Dessa ingick aldrig i planen och har egna plandokument:

- **Vapensystem**: `docs/plan-gear-backed-robot-options.md` — WeaponMount,
  FireControlSystem, attacks-rad; kräver `ceres.gear.weapons` som förutsättning.
- **Komplett manipulatorregel**: `docs/plan-robot-manipulators.md` — STR/DEX,
  ombyggnad, tillägg, walkerben; nuläget är naiv `list[str]`.
- **Gear-backed robot options**: `docs/plan-gear-backed-robot-options.md` —
  transkeivers, sensorer, m.fl. som generiskt gear i stället för robot-strängar.
- **Slot-reduktion vid design**: todo_maybe — permanent borttagning av oanvända slots
  (−Cr100/slot), förklarar Domestic Servant Cr800 vs Ceres Cr900.

## Medvetet uteslutna robottyper

Microbots, nanorobots, vehicle brains, ship's brains, androider, biologiska robotar,
avatarer, kloner och mycket stora fordonsliknande robotar är uteslutna och har inga
halvfärdiga specialfall i modellen.
