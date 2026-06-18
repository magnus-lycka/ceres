# Completed todo items

Moved from `docs/todo_maybe.md` once fully implemented.

## Psion career and talent-acquisition foundation

The Core Psion career, typed psionic talents, eligibility, career tables,
events and mishaps, Psionic Community auto-qualification, and RIC-006
homeworld offer are implemented.

Implemented:

- Psionic testing establishes PSI and typed `Psionics` state.
- Entering Psionic Community or the Psion career starts institute training
  when the character has not previously attempted talent acquisition.
- Talent-acquisition attempts track their cumulative DM penalty and acquired
  talents separately from ordinary skills.
- Psion skill-table results improve possessed talents or allow an acquisition
  attempt for an unpossessed talent.

Individual psionic powers remain tracked separately in `docs/todo_maybe.md`.

## Character creation: CareerTerm narrative fields

`CareerTerm` carries `event`, `mishap`, and `prison` narrative fields.
Career event, mishap, life-event prison, and Prisoner-transition handlers
populate them so consumers can describe a term without interpreting event IDs.

Covered by `tests/character/test_career_term_narrative.py`.

## Character creation: career re-entry restrictions

Immediate career re-entry restrictions are enforced:

- Mishap ejection blocks the same career in the following term, regardless of
  assignment.
- Voluntarily leaving an assignment-change career blocks every assignment in
  that career in the following term.
- Voluntarily leaving Agent, Citizen, Entertainer, or Merchant blocks the same
  assignment but permits a different assignment as a new career run.
- Draft entry uses its separate path and bypasses normal re-entry restrictions.
- `MusterOut.used` prevents a post-muster re-entry from continuing the prior
  career run.

`CharacterSummary.last_career_ejected` records whether the most recent
departure was an ejection. Covered by the re-entry tests in
`tests/character/test_muster_out.py`.

## Psionic Community pre-career: bring Ceres fully in line with Companion

Psionic Community entry, training, graduation checks, and graduation benefits
are represented.

References:

- `refs/companion/07_pre_career_options.md` (Psionic Community)
- `src/ceres/character/domain/precareer/psionic_community.py`
- `src/ceres/character/domain/precareer/loader.py`
- `tests/character/test_companion_precareers.py`

Implemented:

- Entry requires established PSI and resolves the `PSI 8+` check with
  `DM+1` for INT 8+.
- Entry starts psionic institute training for an untrained psion.
- Graduation resolves the `PSI 6+` check with `DM+1` for INT 8+.
- Graduation grants PSI +1, Science (psionicology) 1, one possessed talent at
  level 1, and permanent automatic Psion enlistment.
- Honours raises all possessed talents to level 1 and offers one at level 2.
- Graduation grants the required Rival, or Enemy with honours.

## Character creation: make career classes real rule-owning objects; unify with Career identity

All 14 career modules converted from the `CAREER_DATA = XCareerData(...)` singleton
pattern to `ClassVar`-based rule ownership. Each career module now declares one
`CareerData` subclass with a `type: Literal['X_CAREER']` discriminator; all
Traveller rules (qualification, assignments, skill tables, ranks, mishaps, events,
muster-out) live as `ClassVar` attributes on the class.

`CareerData._registry` and `__init_subclass__` registration replace the old
`CAREER_DATA` module-attribute scan. `model_validator(mode='before')` enables
round-trip deserialization of stored career references via the registry.

`CharacterSummary.current_career`, `CharacterSummary.last_career`,
`CareerTerm.career`, and `CharacterProjection.muster_out_career` /
`forced_next_career` all changed from `Career` to `CareerData`. Module-level
constants (`SCOUT`, `AGENT`, etc.) are now `CareerData` instances. All
`term.career == self.career` comparisons replaced with `type(term.career) is
type(self)` (or Pydantic equality for module-constant comparisons).

The tiny `Career` frozen dataclass is fully deleted. Each career module now
declares `name`, `source`, and `description` as direct `ClassVar[str]` attributes.
`CareerData` base class declares `name: ClassVar[str]`, `description: ClassVar[str]`,
and `source: ClassVar[str] = 'Core'` (default covers all 13 Core careers).

## Character creation: typed skill instances in pending events

`PendingCareerSkillRoll`, `PendingSkillChoice`, `PendingCareerSkillChoice`, and
`PendingBackgroundSkills` now hold `AnySkill` instances in their `options` fields
instead of strings. `_pick_skill_auto` in `state.py` handles typed instances
directly. All career event handlers and test assertions use typed skill objects.
`skill_instances()` in `skills.py` returns `list[AnySkill]`. `SkillTableEntry` in
`career_data.py` and `PrecareerSkillEntry.skill` in `precareer_data.py` both use
`AnySkill`. `scholar.py` and `prisoner.py` updated with typed options.

The remaining string-based paths were eliminated in the two follow-up work packages below.

## Character creation: remove `str` overload from `CharacterSummary.skill_level`

`skill_level(name: str | type[Skill])` simplified to `skill_level(skill_cls:
type[Skill])`. The `str` branch is gone; the implementation now uses `type(skill)
is skill_cls` instead of string name comparison. `diff_summaries` updated to key
on `type(s)` instead of `type(s).name()`. All callers in test files converted to
typed class references, with missing imports added to each file.

## Character creation: eliminate all string-based skill lookup

`PreCareerSkillChoiceEvent.skill` migrated from `str` to `AnySkill`. All
string-based skill functions (`skill_from_str`, `skill_class_by_name`,
`skill_names`, `expand_to_spec_options`, `parse_skill_spec_option`,
`skill_spec_option_names`) deleted from `skills.py`. `increment_skill` in
`state.py` now takes `AnySkill` directly. `precareer_skills` in
`CharacterSummary` changed from `list[str]` to `list[SerializeAsAny[AnySkill]]`.
`PendingPreCareerSkillChoice.options` is `list[AnySkill]`; `auto_event`,
`event_from_form`, and `input_specs` updated accordingly.
`PrecareerSkillEntry.option_names` renamed to `skill_options` and now returns
`list[AnySkill]`. All precareer files (`university.py`, `psionic_community.py`,
`colonial_upbringing.py`, `school_of_hard_knocks.py`, `spacer_community.py`,
`merchant_academy.py`) updated to work with typed instances throughout.

## Character creation: Prisoner advancement + parole simultaneity fix

`SkillTableEvent.apply` previously called `get_current_career()` unconditionally.
For a Prisoner who simultaneously advances (rank up) and earns parole, the
`queue_reenlist_or_aging` call triggered by the advancement clears `current_career`
via `muster_out_setup` before the queued `PendingSkillTable` is processed, causing
a `ReplayError: No active career`.

Fixed by falling back to `projection.muster_out_career` when `current_career is
None` — `muster_out_setup` sets `muster_out_career` before clearing the active
career, so the skill table can still be applied.

## Character creation: TermData base class

Introduced `TermData(BaseModel)` in `career_data.py` as the shared base for both
`CareerData` and `PreCareerData`. `TermData` owns the `events: dict[int, CareerEventEntry]`
field (previously duplicated in both). `CareerData(TermData)` and `PreCareerData(TermData)`
both inherit from it.

All career modules now define a named `CareerData` subclass (`ArmyCareerData`,
`MarinesCareerData`, `MerchantCareerData`, `NavyCareerData`, `ScholarCareerData`,
`ScoutCareerData`) rather than using `CareerData` directly — mirroring how precareers
are already structured as subclasses of `PreCareerData`.

The `_CAREER_MODULE_NAMES` lazy-load pattern in `careers/__init__.py` was kept as-is
because eager imports cause a circular import via the `events.py → state.py →
careers/__init__.py → common.py → events.py` chain.

Added `RUF012` to the per-file-ignores for `src/ceres/character/**/*.py` in
`pyproject.toml` because ruff cannot trace cross-file Pydantic inheritance chains
(it recognises `PreCareerData(BaseModel)` but not `PreCareerData(TermData)` where
`TermData(BaseModel)` is defined in another file).

## Muster-out benefits are string-key encoded

Replaced `parse_benefit(...)` throughout career data with typed benefit objects.
Added `CombinedBenefit` to `benefits.py` for rows that grant multiple benefits
simultaneously (Noble roll 7: SOC+1 and Yacht; Entertainer roll 7: SOC+1 and
EDU+1; Prisoner roll 7: Deception, Persuade, and Stealth). Added named constants
for all item benefits (`SHIP_SHARE`, `SCOUT_SHIP`, `BLADE`, `CONTACT`, etc.).
Updated `_apply_muster_out_benefit` in `events.py` to apply `CombinedBenefit`
sub-benefits in sequence. Removed `parse_benefit` entirely.

## Crewmember Profession is wrong

Removed `CrewmemberProfession` class from `src/ceres/character/skills.py` and the `Professions` union.
Removed it from the `isinstance` check in `src/ceres/make/robot/skills.py`.
Removed "Crewmember Profession" from the RIC-001 broad-skill table in `docs/RULE_INTERPRETATIONS.md`.
"Crewmember" is a specialisation of `SpacerProfession`, not a separate broad skill.

## Naming

Renamed `self.owner` → `self.ship` and `_owner` → `_ship` throughout `parts.py` and all subclasses.

## Software Singleton

Note that Software Packages are Singletons

If user e.g. lists JumpContrl/2 and then JumpControl/3,
they have (and pay for) JumpControl/3, and a warning that
redundant JumpControl/2 was added. Note the included
JumpControl SW in Core models. I assume that if your main
is a Core, and your spare is a (non Core) computer, it
can still run the Core supplied SW within the capacity of
its rating.

## Quantities

If we have 10 staterooms, it should say Staterooms ✕ 10.
The same is probably true for many other items. If it's
just one, it can just say Stateroom.

Current status:

- done for Staterooms
- done for Low Berths
- done for Probe Drones
- done for grouped spec rows such as Airlocks
- done for crew table rows

## Decentralize build_spec

Move substantial parts of Ship.build_spec() out to the
sections that own the rows, such as storage, computer,
habitation and systems.

## Character creation: replace remaining `list[str]` options with typed option objects

All five remaining raw-string option contracts replaced with typed equivalents:

- `PendingSkillTable.options` → `list[SkillTableOption]`
- `PendingConnectionsRoll.options` → `list[int]`
- `PendingSwitchAssignment.options` → `list[AssignmentData]`
- `PendingBenefitChoice.options: list[str]` → dropped entirely; `benefit_options: list[AnyBenefit]` was already the typed field
- `DecreaseCharacteristicChoiceEffect.options` → `list[Chars]`

## Character creation: typed career and assignment fields in handlers and CareerTerm

Replaced all `career: str` and `assignment: str` fields in event handlers and summary
state with domain objects throughout:

- `CareerEntryHandler`, `DraftHandler`, `DraftAssignmentHandler`, `SwitchAssignmentHandler`
  — `career: CareerData`, `assignment: AssignmentData`. No string-to-domain lookups
  anywhere; callers must supply real objects.
- `CareerTerm.assignment: AssignmentData` — removed `assignment: str` and
  `assignment_index: int = 0`. Index is derivable via `career.assignment_index(assignment)`.
- `CharacterSummary.current_assignment` / `last_assignment` — changed from `str | None` to
  `AssignmentData | None`; `current_assignment_index` and `last_assignment_index` fields
  deleted entirely.
- `_from_registry` model validator changed from `mode='before'` to `mode='wrap'` so
  `CareerData` instances short-circuit cleanly without Pydantic re-validating the returned
  subclass instance.

Current status:

- done for hull
- done for drives / power
- done for storage (fuel + cargo)
- done for command
- done for computer
- done for sensors
- done for habitation
- done for systems
- done for weapons
- done for craft

Note:

- expense / crew summary now live in `expense.py` and `crew.py`
- a couple of generic row-grouping helpers still remain in `Ship`, but the section-level decentralization itself is complete

## Implement armoured bulkhead

Armoured bulkheads protect specific areas and
systems, such as the jump drive or fuel tanks, making
them much more resilient to damage.
Adding armoured bulkheads consumes an amount of
space equal to 10% of the tonnage of the protected
item. During space combat, the Severity of any critical
hit to the protected space is reduced by -1 (to a
minimum of Severity 1).

Option Cost
Armoured Bulkhead MCr0.2 per ton

Current status:

- `ArmouredBulkhead` implemented in `hull.py`
- cost and tonnage modeled
- protection target shown in spec notes
- treated as a ship-design/spec concern, not as combat simulation logic

## Limit TL

Make a note in ARCHITECTURE.md that support is limited to TL16 and lower, and
stick to that when writing code. For now we cap ship TL to 16 and don't bother
to implement TL17+ features.

Current status:

- `ARCHITECTURE.md` now states the TL16 cap explicitly
- `Ship` now rejects `tl > 16`
- TL17+ features are intentionally out of scope for now

## Expense module

Break out expense code to its own module expense.py

## Combine propulsion and jump sections

Maybe it's better to combine jump and propulsion to a drives section?

## x vs ×

Counted labels now go through shared helpers in `ceres.make.ship.text`, so the display form is consistently `×`
instead of `x`, and repeated labels are collapsed in one place instead of being reimplemented separately.

## Large ship crew reduction cap

For displacement-based roles the crew reduction for large ships should not
result in more crew than the next bracket above would require.

Implemented by restructuring the bracket data into `_LARGE_SHIP_BRACKETS` and
adding `_next_crew_reduction_multiplier`. `_apply_large_ship_reduction` now
applies `min(result, ceil(count × next_multiplier))` for any ship in the
reduction zone, preventing a ship just below a bracket boundary from needing
more crew than one just above it. The cap is not applied to ships ≤ 5,000 dTons
(outside the large-ship reduction zone).

## Medic passenger count

The commercial medic rule is "1 per 120 crew **and** passengers." Previously
only crew count was used.

## Hardened Systems

References: `refs/hg/10_step_6_install_computer.md`, `refs/hg/26_drones.md`,
`refs/hg/17_particle_beam.md`, `refs/hg/43_fleet_evaluation.md`

`Computer` already supports `/fib` (+50% cost, ion immunity). The broader rule
from HG is:

> Any system that draws power from the power plant can be Hardened to render it immune to Ion weapons. A Hardened system has its cost increased by +50%.

Current status:

- The construction rule is implemented per powered system, not as a hull-level
  option.
- `ShipPart` has `hardened: bool = False`.
- Ship spec rows and production cost apply +50% cost only when `hardened=True`
  and the part draws Power.
- Hardened powered parts add the note "Hardened against Ion weapons".
- Hardened zero-Power `ShipPart`s report an error and do not receive a cost
  increase.
- Computer `/fib` remains the computer-specific spelling used by the source
  material; it is not collapsed into generic hardening.
- Radiation shielding treats the bridge as Hardened, but this is part of the
  radiation-shielding rule and remains an operational note unless bridge
  hardening becomes explicitly modelled.
- The fleet combat trait "Hardened" from `43_fleet_evaluation.md` is derived
  from powered-system coverage and is not a separate ship input flag.

## Breakaway Hulls

A ship can be designed to separate into two or more independently operating
sections. Each section must have its own bridge and power plant; drives,
weapons, and screens are optional per section but combined while docked. The
separation mechanism consumes 2% of the combined hull tonnage at MCr2/ton. Hull
points of each section are proportional to the total.

Reference: `refs/hg/05_specialised_hull_types.md`

Current status:

- `breakaway: bool` on `HullConfiguration` adds the 2% tonnage and MCr2/ton
  separation mechanism cost to the ship spec.
- the separation mechanism reduces residual cargo/usable tonnage.
- operational section separation and docked performance remain notes/out of
  scope until sections are explicitly modelled.

Future multi-section modelling is tracked separately in `docs/todo_maybe.md`.

## Non-Gravity Hull

Basic hulls include artificial gravity, using grav plates to ensure a normal
gravitational environment for the comfort and convenience of the crew. Hulls
can be built cheaper without artificial grav plating, using specific
configurations that allow the hull to spin in order to generate gravity if
desired. Non-gravity hulls reduce hull cost by 50% but are limited to a maximum
size of 500,000 tons due to structural limitations. Base Power Requirements for
non-gravity hulls are half that of other hull types.

Current status:

- hull cost reduction implemented
- basic hull power reduction implemented
- 500,000-ton maximum size reported as a ship error
- spin-capable layout, spin radius, comfort, and usefulness are layout/runtime
  concerns and are not modelled by `ceres.make.ship`; see RIS-021

## Solar Energy Systems

High Guard and Spinward Extents solar-energy ship-building products are now
kept as separate source-specific classes where their tables and constraints
differ.

References:

- `refs/hg/25_solar_energy_systems.md`
- `refs/spinext/59_arcturus.md`
- `docs/solar-energy-systems-comparison.md`

Implemented High Guard/default variants:

- `BasicSolarPanels`
- `ImprovedSolarPanels`
- `EnhancedSolarPanels`
- `AdvancedSolarPanels`
- `EnhancedSolarCoating`
- `AdvancedSolarCoating`
- `SolarSail`

Implemented Spinward Extents variants:

- `SpinExtSolarPanelsTL6`
- `SpinExtSolarPanelsTL8`
- `SpinExtSolarPanelsTL12`
- `SpinExtSolarCoatingTL6`
- `SpinExtSolarCoatingTL8`
- `SpinExtSolarCoatingTL12`
- `SpinExtSolarSailTL6`
- `SpinExtSolarSailTL8`
- `SpinExtSolarSailTL12`

Solar sails are modelled as drive accessories. Spinward Extents solar sails can
also act as solar panels with `solar_panel_mode=True`, doubling their cost and
contributing half the Power of same-tonnage Spinward Extents solar panels.

Distance from the star, deployment timing, manoeuvre restrictions, jump
restrictions, detection modifiers, repair/replacement behaviour, and similar
operational effects are represented as notes or errors in the construction
model rather than simulated as runtime state.

Added `_habitation_population` which sums stateroom `.occupancy`, low berth
count, and `cabin_space.passenger_capacity`. Both `_commercial_roles` and
`_military_roles` now use this as the population denominator when habitation is
present (covering crew and passengers sharing the same accommodation), falling
back to `len(roles)` for ships with no habitation such as small craft.

## Remove singular SystemsSection accessors

Removed `SystemsSection.first_internal_system_of_type` and singular convenience
properties such as `medical_bay`, `library`, `briefing_room`, `workshop`, and
`biosphere`. Repeated internal systems are now accessed through list-returning
properties such as `medical_bays`, `libraries`, `briefing_rooms`, `workshops`,
and `biospheres`, or through `internal_systems_of_type(...)`.

## Handle non-fusion power plants

Chemical and fission power plants are implemented in `power.py`, accepted by
`PowerSection`, covered by unit tests, and represented in operation-fuel tests.

Sterling fission plants are also implemented from the Spinward Extents rules,
including TL6/TL8/TL12 variants, lifespan, minimum size, no operation-fuel
tonnage, and warnings for direct jump-drive use.

## Reaction drives

R-drives are implemented alongside M-drives and J-drives, including high-burn
thruster notes and reference-ship coverage for the 90-ton non-gravity R-drive
case.

The remaining external-load performance policy has been kept in
`docs/todo_maybe.md` under "External-load drive performance".

## Initial hull modifications

Reinforced Hull and Light Hull are implemented as `HullConfiguration` options,
affecting hull cost and Hull points.

Armoured Bulkhead is implemented as a protected-part option plus explicit hull
component, with cost, tonnage, spec notes, and tests.

Pressure Hull is implemented with 25% tonnage usage, ×10 hull cost, intrinsic
Armour 4, spec output, and tests.

Any remaining validation rules for incompatible hull combinations remain in
`docs/todo_maybe.md`.

## Verify that we do not collapse non-identical rows

Spec row grouping and report-row collapse already require matching item labels
and display notes. Added a regression test covering two different triple
turrets:

- two identical pulse-laser turrets may collapse to `Triple Turret × 2`
- a pulse-laser turret and a missile/sandcaster turret remain separate rows

The test covers both raw `ShipSpec` weapon rows and `collapsed_main_rows(...)`
used by reports.

## Massive ship Hull points

Very large ships now use the High Guard Hull point scaling:

- 25,000-99,999 tons: 1 Hull point per 2 tons
- 100,000+ tons: 1 Hull point per 1.5 tons

Existing configuration modifiers such as Reinforced Hull and Light Hull still
apply before the divisor.

## Non-gravity hull maximum size

Non-gravity hulls now report a ship error above the 500,000-ton maximum size.

The remaining spin-layout modelling question stays in `docs/todo_maybe.md`.

## Command Bridge

Command bridges are implemented as a separate `CommandBridge` internal system,
not as a variant of the ship-control bridge.

They add 40 tons, add MCr30 to bridge cost, require ship displacement greater
than 5,000 tons, and add a spec note for DM+1 to Tactics (naval) checks made
within the command bridge.

## Cargo handling equipment

Cargo handling equipment from High Guard is implemented in `storage.py` and
rendered in the Cargo section of ship specs.

Implemented parts:

- `CargoCrane`: tonnage = 2.5 + 0.5 per 150 tons or part thereof of cargo
  space; MCr1 per ton of crane; reduces usable cargo hold capacity.
- `CargoScoop`: 2 tons, MCr0.5, with operational notes for scooping floating
  cargo and failed Pilot checks.
- `CargoNet`: 5 tons, MCr1, with operational notes for tow drones and jump
  restrictions while deployed.
- `LoadingBeltTL7`: 1 ton, Cr3,000, replaces 10 loading crew.
- `LoadingBeltTL12`: 1 ton, Cr10,000, 1 Power, replaces 25 loading crew.

## External Cargo Mount

External cargo mounts are implemented in `storage.py` as
`ExternalCargoMount(capacity=...)`.

They cost Cr1,000 per ton of external cargo capacity, add no internal tonnage
or power load, cannot be installed on streamlined or dispersed-structure hulls,
and add notes that the ship is effectively unstreamlined while external cargo
is mounted.

External cargo mount capacity contributes to ship `performance_displacement`,
so drive and fuel calculations using the combined tonnage are updated.

## Jump Net

Jump nets are implemented in `storage.py` and rendered in the Cargo section of
ship specs.

Implemented variants:

- `InterplanetaryJumpNet(capacity=...)`: TL8, 1 ton per 100 tons of external
  cargo capacity or part thereof, MCr0.1 per ton of net, cannot perform jump
  while deployed.
- `InterstellarJumpNet(capacity=...)`: TL10, 1 ton per 100 tons of external
  cargo capacity or part thereof, MCr0.3 per ton of net.

Both variants add notes that the ship is effectively unstreamlined while the
jump net is deployed. Jump net capacity contributes to
`performance_displacement`, so drive and fuel calculations include the external
cargo tonnage.

## Accommodation additions

Accommodation/support options from the High Guard Spacecraft Options chapter
are implemented in `systems.py` and render in the ship spec as internal system
rows.

Implemented parts:

- `AccelerationBench`: 4 seats, 1 ton, Cr10,000, a lower-cost bench variant of
  `AccelerationSeat`.
- `MultiEnvironmentSpace(covered_tons=...)`: support equipment for unusual
  environmental conditions, adding 5% of the designated area's tonnage,
  MCr0.5 per equipment ton, and 1 Power per equipment ton.

## Vault

Vaults are implemented in `systems.py` as `Vault(tons=...)`.

They support the High Guard 4-40 ton size range, cost MCr0.5 per ton, add no
power load, and expose content-only protection values:

- `content_armour = min(10, tons)`
- `content_hull_points = tons // 5`

Spec notes state that vault armour and Hull points protect contents only, not
the ship, and that contents can survive in vacuum for a limited time if the
ship is destroyed.

## Re-entry Capsule and Re-entry Pod

Re-entry capsules and pods are implemented in `systems.py` and render in ship
specs as internal system rows.

Implemented variants:

- `BasicReEntryCapsule`: TL8, 0.5 tons, Cr20,000, capacity 1.
- `AssaultReEntryCapsule`: TL10, 0.5 tons, Cr50,000, capacity 1,
  Protection +20, DM-2 to detect.
- `HighSurvivabilityReEntryCapsule`: TL14, 0.5 tons, MCr0.1, capacity 1,
  Protection +30, DM-4 to detect, DM-2 against attacks.
- `ReEntryPod`: TL9, 1 ton, MCr0.15, capacity 2, with notes for its gliding
  surface, computer guidance, and manual Flyer (wing) control.

## Stable

Stables are implemented in `habitation.py` as `Stable(tons=...)` and render in
the Habitation section of ship specs.

They cost Cr2,500 per ton, add no power load, require a minimum size of 10
tons, and add Cr250 per ton to life support facility costs. Capacity scales
from the High Guard baseline of 10 tons housing 20 human-sized or 10
cattle-sized creatures.

## Concealed Compartment

Concealed compartments are implemented in `storage.py` as
`ConcealedCompartment(tons=...)` and render in the Cargo section of ship specs.

They cost Cr20,000 per ton, add no power load, and validate the High Guard
limit of at most 5% of ship tonnage. Spec notes include DM-2 to Electronics
(sensors) checks and DM-4 to Investigate checks made to find the compartment.

## Booby-Trapped Airlock

Booby-trapped airlocks are implemented as an optional `booby_trap` sub-part on
`Airlock`.

Implemented variants:

- `BoobyTrapTL6`: MCr0.1, 3D damage/round.
- `BoobyTrapTL8`: MCr0.3, 5D damage/round.
- `BoobyTrapTL10`: MCr0.5, 6D damage/round.
- `BoobyTrapTL12`: MCr1, 8D damage/round.

The trap adds no tonnage, adds its cost even when the airlock itself is part of
the ship's free airlock allowance, validates its TL, and renders a damage note
in the ship spec. The actual combat effect is out of scope for ship building.

## Construction Deck

Construction decks are implemented in `systems.py` as `ConstructionDeck(tons=...)`
and render in ship specs as internal system rows.

They cost MCr0.5 per ton, require 1 Power per ton, and report that they can
build or repair ships up to half the construction deck tonnage at the carrying
ship's TL. Construction simulation is out of scope.

## Optional Label On Parts

Generic display labels are implemented on `CeresModel` through
`display_label: str | None`.

The base `build_item()` renders labelled instances as
`"<display label> (<description>)"`, so generic parts can represent published
design names such as `Trophy Lounge (Common Area)` without changing tonnage,
cost, power, validation, or grouping semantics.

## Common Area Extras

Additional High Guard common-area extras are implemented in `systems.py`:

- `Brewery(litres_per_week=...)`: TL10, 0.5 tons per 10 litres/week, MCr0.1 per
  ton.
- `GourmetKitchen(diners=...)`: 1 ton per diner, MCr0.2 per ton, with notes for
  Steward 2 and DM+1 when seeking high passengers.
- `ZeroGRoom(tons=...)`: any specified room size, Cr50,000 fixed cost for
  controls and safe-access portal.

## Companion Weapon Additions

Traveller Companion starship weapon additions are implemented in the
`weapons/` package.

Implemented parts:

- `PlasmaCarronade`: TL10, 4 hardpoints, 4 tons, MCr10, 35 Power, 12D, Weak.
- `FusionCarronade`: TL12, 4 hardpoints, 4 tons, MCr12, 45 Power, 16D,
  Radiation and Weak.
- `GeneralPurposeMassDriverBay(extra_launch_capacity=...)`: TL8, base 50 tons,
  MCr4, 10 Power, 1 hardpoint, with optional extra launch capacity.
- `TorpedoInterceptorCluster`: TL10, 1 hardpoint, 1 ton, MCr1, 1 Power,
  one-shot system with four interceptors.
- `LargeHullcutterBay`: TL16, 5 hardpoints, 500 tons, MCr110, 100 Power, with
  Reductor noted as an operational combat effect.

Operational combat mechanics such as Weak, Reductor, and interceptor kill rolls
are represented as notes only.

## Pop-Up Mounting

Pop-up mounting is implemented on `FixedMount` and turrets through
`pop_up: bool = False`.

When enabled, it requires TL10, adds 1 ton and MCr1 to the mount, and renders a
note that the weapon system is concealed until deployed. Hardpoint/firmpoint
allocation remains the same as the underlying fixed mount or turret.

## Weapon Customisation Modifiers

Additional High Guard weapon customisation modifiers are implemented in the
`weapons/` package:

- `Accurate`: 2 Advantages, note for DM+1 to attack rolls.
- `EasyToRepair`: 1 Advantage, note for DM+1 to repair attempts.
- `IntenseFocus`: 2 Advantages, note for AP+2, restricted to laser and
  particle weapons.
- `Resilient`: 1 Advantage, note for reducing weapon critical hit Severity by
  -1.
- `Inaccurate`: 1 Disadvantage, note for DM-1 to attack rolls.

They are wired into the existing customisation framework and allowed on weapon
parts that already support weapon customisation.

## Jump Drive Customisation Modifiers

Additional High Guard jump drive customisation modifiers are implemented in
`drives.py`:

- `EarlyJump`: 1 Advantage, note for jumping at the 90-diameter limit.
- `StealthJump`: 2 Advantages, note for reduced jump emergence radiation
  signature.
- `JumpEnergyInefficient`: 1 Disadvantage, +30% Power for jump drives.
- `LateJump`: 1 Disadvantage, note for requiring the 150-diameter limit before
  jumping.

## Weapon Model Refactor

The broad weapon model refactor is complete enough to close the original
`Sort out weapons` doing item.

Implemented structure:

- hardpoint/firmpoint capacity checks
- small craft restriction to single turrets
- concrete turret classes such as `SingleTurret`, `DoubleTurret`, and
  `TripleTurret`
- shared concrete mount weapon classes for fixed mounts and turrets
- concrete barbettes, bays, point-defence batteries, spinal mounts, and
  ammunition/storage parts
- size-reduction weapon modifiers for barbettes, bays, and point-defence
  batteries
- fixed mounts with multiple weapons and small-craft restrictions

Remaining coverage and policy questions were moved back to `todo_maybe.md` as
follow-up todo items rather than keeping the broad refactor open.

## Crew Calculation Structure

The broad crew-calculation structure is complete enough to close the original
`DETERMINE CREW` doing item.

Implemented structure:

- `crew.py` is the single source of truth for ship crew calculations
- `Ship` delegates crew analysis to `crew.py`
- commercial crew rules
- military crew rules
- large ship crew reduction, including bracket-boundary cap
- medic count uses habitation capacity as a population proxy

Role inference policy is now decided: ship role stays explicit. Ceres does not
infer military construction/crew mode automatically; callers opt into military
crew analysis with the existing `military=True` switch.

## Screens Follow-Up

The broad screens follow-up is complete enough to close the doing item.

Implemented screen support:

- `MesonScreen`
- `NuclearDamper`
- `DeflectorScreen`
- `EnergyShield`
- screen gunner counts in commercial and military crew analysis

Remaining Black Globe and source-coverage work was moved back to `todo_maybe.md`
as a focused todo item.

## Spinal Mount Follow-Up

The broad spinal mount follow-up is complete enough to close the doing item.

Implemented support:

- High Guard mass driver, meson, particle accelerator, and railgun spinal mounts
- TL improvement rows (`+1`, `+2`, `+3`)
- military gunner count for spinal weaponry
- mass driver spinal mount ammunition cargo helper
- railgun spinal mount extra rounds cargo helper

Remaining source-coverage work was moved back to `todo_maybe.md` as a focused
todo item.

## Military Hull Armour Cap

Military hull armour-cap handling is implemented.

Implemented support:

- `HullConfiguration.effective_hull_cost_modifier` applies the +25% military
  hull cost modifier.
- ships with `military=True` on hull configuration emit an error at
  displacement <= 5,000 tons.
- armour validation doubles the normal TL-derived armour cap for military
  hulls and reports a military-hull-specific error when exceeded.

## Cockpit Options

Dual cockpit and ejector seat options are implemented on `Cockpit`.

Implemented support:

- `dual: bool = False` adds space for a second crew member, +2.5 tons, and
  Cr15,000.
- `ejector_seat: bool = False` adds Cr5,000 per cockpit seat.
- cockpit display labels describe dual and ejector-seat variants.
- unit tests cover standard, holographic, dual, ejector-seat, and combined
  cockpit values.

## Emergency Low Berth

Emergency low berths are implemented in `habitation.py`.

Implemented support:

- `EmergencyLowBerth` consumes 1 ton, costs MCr1, requires 1 Power, and holds
  four occupants.
- emergency low berths are included in `HabitationSection`.
- occupant capacity is included in habitation capacity calculations.
- unit tests cover cost, tonnage, power, capacity, and section integration.

## Grav Screen

Grav screens are implemented in `systems.py`.

Implemented support:

- `GravScreen` is TL12.
- tonnage is one ton per 200 tons of hull displacement, rounded up.
- cost is MCr1 per ton.
- power requirement is 2 Power per ton.
- notes record the operational densitometer-blocking effect.
- unit tests cover scaling by ship displacement.

## Detachable Bridge

Detachable bridges are implemented on `Bridge`.

Implemented support:

- `detachable: bool = False` adds 20% to bridge tonnage.
- detachable bridges add 50% to bridge cost, combining with small and
  holographic bridge modifiers.
- bridge labels identify detachable standard, small, and holographic variants.
- minimum detachable bridge sizes are validated by displacement band:
  15 tons up to 200 tons displacement, 30 tons up to 1,000 tons, 50 tons up to
  2,000 tons, and 80 tons above 2,000 tons.
- unit tests cover tonnage, cost, item labels, and minimum-size validation.

## Gravity Well Generator

Gravity well generators are implemented in `systems.py`.

Implemented support:

- `GravityWellGenerator` is TL16.
- tonnage is 100 tons.
- cost is MCr120.
- power requirement is 500 Power.
- notes record that the artificial-gravity-well effect is tactical and out of
  scope for ship construction.
- the part is included in `AnyInternalSystem` for serialization and system
  section use.
- unit tests cover values, notes, stale numeric input handling, and computed
  property serialization.

## Launch Tube And Recovery Deck

Launch tubes and recovery decks are implemented in `crafts.py`.

Implemented support:

- `LaunchTube(largest_craft_tons=...)` is TL9.
- `RecoveryDeck(largest_craft_tons=...)` models the recovery counterpart.
- both consume tonnage equal to 10 times the largest craft they support.
- both cost MCr0.5 per ton and require 1 Power per ton.
- notes record the construction-relevant operational limits: launch tubes do
  not replace docking space/full hangars, and recovery decks are open to vacuum
  and not full hangars.
- both parts are included in `InternalCraftHousing` for serialization and craft
  section use.
- unit tests cover values, notes, TL validation, power, stale numeric input
  handling, and computed property serialization.

## Jump Filter

Jump filters are implemented in `systems.py`.

Implemented support:

- `JumpFilter` is TL14.
- tonnage is 0 tons.
- cost is MCr5.
- power requirement is 1 Power.
- bandwidth is exposed as a property with value 5; ship spec rows do not yet
  have a bandwidth column.
- notes record the construction-relevant operational effect while keeping
  detailed jump-disruption mechanics out of scope.
- the part is included in `AnyInternalSystem` for serialization and system
  section use.
- unit tests cover values, notes, TL validation, spec row output, stale numeric
  input handling, and computed property serialization.

## Psion Stateroom

Psion staterooms are implemented in `habitation.py`.

Implemented support:

- `PsionStateroom` is TL12.
- tonnage is 4 tons, matching a normal stateroom.
- cost is MCr2.
- the room is otherwise modelled as a normal stateroom, including occupancy,
  residence provision, and life-support facility cost.
- notes record the +50% PSI-regeneration effect for a psion occupant.
- the part is included in the stateroom union for serialization and habitation
  section use.
- unit tests cover values, notes, TL validation, residence/life-support
  integration, and JSON round-trip.

## Psionic Shielding

Psionic shielding is implemented in `systems.py`.

Implemented support:

- `PsionicShielding` is TL12.
- standard shielding consumes 1% of ship displacement.
- standard shielding costs MCr0.5 per ton.
- standard shielding consumes no Power.
- standard shielding notes report the size-dependent Clairvoyance and Telepathy
  effect: impenetrable below 100 tons, DM-4 up to 300 tons, DM-2 up to 500 tons,
  and no DM above 500 tons.
- `AdvancedPsionicShielding` is TL16.
- advanced shielding consumes no tonnage or Power.
- advanced shielding costs MCr1 per 100 tons, or part thereof, of ship
  displacement.
- both parts are included in `AnyInternalSystem` for serialization and system
  section use.
- unit tests cover values, notes, TL validation, stale numeric input handling,
  and computed property serialization.

Psionic Capacitor remains intentionally out of scope because Ceres currently
supports TL16 and lower.

## Power Plant Increased Power Customisation

The High Guard `Increased Power` customisation modifier is implemented for
power plants.

Implemented support:

- `IncreasedPower` is a 2-Advantage modification.
- power plants store the requested base output as the serialized `output`
  field and expose effective `.output` after customisation.
- `IncreasedPower` multiplies effective output by 1.10.
- plant tonnage remains based on base output, while customisation grade cost
  modifiers continue to apply normally.
- `PowerSection.output`, available ship power, and Power spec rows use the
  effective output.
- unit tests cover output, cost, tonnage, spec rows, notes, available power, and
  JSON/model round-trip.

## Reaction Drive Fuel Customisation

Reaction-drive fuel customisation modifiers are implemented.

Implemented support:

- `FuelEfficient` is a 1-Advantage modification and reduces reaction-fuel
  requirement by 20%.
- `FuelInefficient` is a 1-Disadvantage modification and increases
  reaction-fuel requirement by 25%.
- R-drives are now `CustomisableShipPart` instances and allow those
  reaction-drive fuel modifiers.
- `ReactionFuel` reads the installed R-drive customisation fuel multiplier.
- R-drive customisation notes are displayed alongside high-burn thruster notes
  where applicable.
- unit tests cover efficient and inefficient fuel calculations, notes, allowed
  modification handling, and JSON/model round-trip.

## Reflec Hull Option

The High Guard reflec hull option is implemented on `Hull`.

Implemented support:

- `Hull.reflec` adds a Hull spec row named `Reflec`.
- cost is MCr0.1 per ton of ship displacement.
- notes record +3 armour protection against lasers.
- reflec cost is included in production cost.
- ships with both reflec and stealth emit an error.
- unit tests cover cost, spec row output, production cost, and stealth
  incompatibility.

## Automation

Traveller Companion ship automation levels are implemented.

Implemented support:

- `Ship.automation` defaults to `StandardAutomation`.
- all six automation tiers are modelled: crew-intensive, low, standard,
  enhanced, advanced, and high.
- automation cost modifiers use the configured hull basis plus drives and power
  plant costs.
- the non-gravity hull discount is excluded from the automation cost basis.
- crew multipliers are applied to reducible crew roles.
- standard automation emits no spec row; non-standard automation emits a Hull
  spec row with any task DM notes.
- unit tests cover tier values, cost basis, spec row output, serialization, and
  non-gravity automation basis handling.

## Concealed Manoeuvre Drive

High Guard concealed manoeuvre drives are implemented on M-drive parts.

Implemented support:

- `MDrive*` parts accept `concealed=True`.
- concealed drives add +25% to M-drive tonnage and cost.
- effective Thrust is halved, rounding down, through `.effective_thrust`.
- power remains based on the installed drive rating because the option only
  changes tonnage, cost, and effective Thrust.
- notes record the effective Thrust, the 3-metre accelerating-surface placement
  rule, and that removing the outer bulkhead does not improve performance.
- unit tests cover values, notes, and JSON/model round-trip through the M-drive
  union.

## Collectors

High Guard collector arrays are implemented as Fuel section parts.

Implemented support:

- `Collector(parsecs=...)` models a TL14 collector sized for a jump rating.
- tonnage is `(1% of hull tonnage * jump rating) + 5`.
- cost is MCr0.5 per ton.
- collectors draw no ship power.
- collector rows render in the Fuel section and note that they collect and
  store interstellar hydrogen for jump fuel.
- unit tests cover values, computed-field serialization, and spec output.

## Fuel Refinery

High Guard fuel refineries are implemented as Fuel section parts.

Implemented support:

- `FuelRefinery(tons=..., tl=7|10|13)` models the three High Guard tiers.
- output per day, power, crew requirement, and cost follow the TL-specific
  table.
- refinery rows render in the Fuel section with the output rate in tons/day.
- fuel power load includes both fuel processors and fuel refineries.
- notes record the table's crew requirement.
- unit tests cover all TL tiers, computed-field serialization, spec output,
  and fuel power load.

## Adjustable Hull

High Guard adjustable hulls are implemented as Hull section parts.

Implemented support:

- `AdjustableHull(tl=12|15)` models the two High Guard tiers.
- TL12 consumes 5% of ship tonnage and costs +10% of base hull cost.
- TL15 consumes 1% of ship tonnage and costs +100% of base hull cost.
- spec rows render in the Hull section.
- notes record the same-tonnage/configuration/options/external-systems mimicry
  rule and that all weapons receive pop-up mountings at no additional cost.
- TL validation is covered by normal ship-part validation.
- unit tests cover both tiers, production cost, spec rows, notes, and TL errors.

## Ramscoops

High Guard ramscoops are implemented as Fuel section parts.

Implemented support:

- `Ramscoop(extra_tons=0)` models the passive hydrogen collector.
- tonnage is `max(1% of hull tonnage + 5, 10) + extra_tons`.
- collection rate is 5 tons of hydrogen per week per ton of ramscoop.
- cost is MCr0.25 per ton.
- ramscoop rows render in the Fuel section.
- notes record the collection rate and that ramscoops do not require fuel
  scoops or fuel processors.
- streamlined hulls report an error because ramscoops prevent atmospheric
  re-entry.
- unit tests cover minimum sizing, extra tonnage, computed-field
  serialization, spec output, and streamlined-hull validation.

## Fuel Tank Compartments

High Guard fuel tank compartments are implemented as Cargo section parts.

Implemented support:

- `FuelTankCompartment(tons=...)` models hidden compartments that officially
  count as fuel tankage.
- Ceres treats them as real cargo volume per RIS-018, without increasing real
  jump or operation fuel capacity.
- cost is Cr4000 per ton.
- notes record the access restriction, DM-4 Electronics (sensors), DM-6
  Investigate, and the official-operation-endurance overstatement where a power
  plant fuel rate is available.
- unit tests cover values, notes, spec output, and the RIS-018 behaviour.

## Metal Hydride Storage

High Guard metal hydride storage is implemented as a Fuel section option.

Implemented support:

- `FuelSection(metal_hydride_storage=MetalHydrideStorage())` replaces normal
  liquid hydrogen fuel tankage.
- stored fuel still comes from the normal fuel parts (`JumpFuel`,
  `OperationFuel`, and `ReactionFuel`), while metal hydride storage adds an
  equal amount of extra tankage so the fuel row consumes twice the stored fuel
  volume.
- cost is MCr0.2 per ton of metal hydride tankage.
- notes record the doubled-volume rule and the 25%/minimum-1-ton fuel leak
  loss rule.
- TL9 validation, spec output, production-cost accounting, and ship-gallery
  sanity tests are covered.

## Fuel System Variants Decisions

The remaining High Guard fuel tank variants in this group are intentionally not
static ship construction components:

- Collapsible Fuel Tank, Mountable Tank, and Drop Tank are treated as loose
  equipment or operational state; see RIS-017.
- Fuel Tank Compartment is modelled as real cargo volume with official fuel
  tankage notes; see RIS-018.

## Black Globe Generator Construction

High Guard black globe generators are implemented as Screen section parts.

Implemented support:

- `BlackGlobeGenerator` models the TL15 screen generator.
- `BlackGlobeCapacitorBank(tons=...)` models additional black globe capacitors.
- construction values are 50 tons, MCr100, and 30 Power.
- additional capacitors cost MCr3 per ton and absorb 50 points of damage per
  ton.
- spec rows render in the Screens section.
- notes record that black globe generators are not commercially available, block
  manoeuvre/dodge/jump/weapons/sensors while active, and use capacitor/overload
  operational rules outside build-spec modelling.
- unit tests cover table values, capacitor values, spec output, notes, and
  discriminated-union deserialization.

## Holographic Hull

High Guard holographic hulls are implemented as Systems section parts.

Implemented support:

- `HolographicHull` models the TL10 projector system.
- tonnage is zero.
- cost is Cr100000 per ton of hull.
- power draw is 1 Power per 2 tons of hull.
- notes record that the system changes hull colours, graphics, and visual
  appearance without changing the ship's shape.
- unit tests cover values and spec output.

## Breaching Tube

High Guard breaching tubes are implemented as Systems section parts.

Implemented support:

- `BreachingTube` models the military boarding tube.
- tonnage is 3 tons.
- cost is MCr3.
- notes record the DM +1 Boarding Actions modifier and operational attachment
  limits.
- unit tests cover values and spec output.

## External Attachment Systems

High Guard external attachment systems from `refs/hg/26_drones.md` are now
covered as construction/spec parts where they belong in the current ship model.

Implemented support:

- `DockingClamp` in `crafts.py`.
- `TowCable`, `GrapplingArm`, `HolographicHull`, `BreachingTube`, and
  `ForcedLinkageApparatus` in `systems.py`.
- forced linkage apparatus tiers model the Basic, Improved, Enhanced, and
  Advanced table rows, including TL, pilot-check DM, tonnage, cost, notes, and
  the 5000-ton target-use limit.

External-load drive-performance effects remain covered by the separate
effective-displacement todo.

## Split Big Ship Files

The large ship implementation files have been split into focused modules.

Completed splits:

- drives and power plants/systems are separate: `drives.py` and `power.py`
- the former monolithic `weapons.py` is now the `weapons/` package, with
  `weapons/__init__.py` as a small backwards-compatible facade over focused
  weapon modules:
  - `weapons/common.py`
  - `weapons/mounts.py`
  - `weapons/magazines.py`
  - `weapons/barbettes.py`
  - `weapons/bays.py`
  - `weapons/spinal.py`
  - `weapons/point_defense.py`
  - `weapons/section.py`
- the former monolithic `systems.py` is now the `systems/` package, with
  `systems/__init__.py` as a small backwards-compatible facade over focused
  system modules:
  - `systems/common.py`
  - `systems/facilities.py`
  - `systems/command.py`
  - `systems/security.py`
  - `systems/common_areas.py`
  - `systems/medical.py`
  - `systems/access.py`
  - `systems/external.py`
  - `systems/drones.py`
  - `systems/logistics.py`
  - `systems/acceleration.py`
  - `systems/reentry.py`
  - `systems/advanced.py`
  - `systems/section.py`

Existing imports from `ceres.make.ship.weapons` continue to work.
Existing imports from `ceres.make.ship.systems` continue to work.

## Hull Modifications

Specialised High Guard hull modification support is complete for the currently
modelled hull modifiers.

References: `refs/hg/05_specialised_hull_types.md` and
`refs/hg/23_spacecraft_options.md`.

Implemented:

- **Reinforced Hull** — +50% hull cost, +10% hull points.
- **Light Hull** — -25% hull cost, -10% hull points.
- **Armoured Bulkhead** — 10% of protected item's tonnage, MCr0.2/ton, with
  protected-area notes.
- **Pressure Hull** — 25% of total tonnage, x10 hull cost, intrinsic Armour +4.
- **Reflec** — MCr0.1 per ton of hull, +3 armour protection against lasers,
  incompatible with stealth.
- Reinforced and light hull construction are validated as mutually exclusive
  alternatives.

Military Hull remains covered by its own model and validation.

## Screens Source Coverage

High Guard screen construction coverage is complete for the currently modelled
ship-building scope.

References: `refs/hg/22_screens.md` and
`refs/hg/34_space_folding_potential.md`.

Implemented:

- `MesonScreen`: TL13, 30 Power, 10 tons, MCr20, 2D x 10 damage reduction.
- `NuclearDamper`: TL12, 20 Power, 10 tons, MCr10, 2D damage reduction.
- `DeflectorScreen`: TL10, 10 Power, 5 tons, MCr5, 1D damage reduction.
- `EnergyShield`: TL14, 50 Power, 20 tons, MCr25, 10-point energy buffer.
- `ImprovedEnergyShield`: TL16, 75 Power, 15 tons, MCr35, 20-point energy
  buffer.
- `AdvancedEnergyShield`: TL18, 100 Power, 10 tons, MCr60, 50-point energy
  buffer.
- `BlackGlobeGenerator`: TL15, 30 Power, 50 tons, at least MCr100.
- `BlackGlobeCapacitorBank`: MCr3 per ton, no Power requirement, 50 absorbed
  damage points per ton.

Operational rules such as angling screens, energy-shield buffer depletion and
regeneration, black-globe flicker, capacitor discharge, and overload remain
represented as notes or are out of scope for `ceres.make.ship`.

## Spinal Mount Source Coverage

High Guard spinal mount construction coverage is complete for the currently
modelled ship-building scope.

Reference: `refs/hg/18_railgun_ammunition.md`.

Implemented and covered:

- `MassDriverSpinalMount`
- `MesonSpinalMount`
- `ParticleAcceleratorSpinalMount`
- `RailgunSpinalMount`
- base TL, base size, base Power, base cost, damage dice, max size, traits, and
  hardpoint / military crew requirements
- TL improvement rows for +1, +2, and +3 across all four spinal mount families
- mass driver spinal mount ammunition cargo helper: 50 tons and Cr500000 per
  attack
- railgun spinal mount extra-rounds cargo helper: 20 tons and MCr0.2 per round

Operational targeting, range adjustment, and combat resolution remain out of
scope for `ceres.make.ship`.

## Weapon Coverage Follow-Up

The High Guard weapon construction model is complete for the currently modelled
ship-building scope.

References:

- `refs/hg/16_turrets_and_fixed_mounts.md`
- `refs/hg/17_particle_beam.md`
- `refs/hg/18_railgun_ammunition.md`
- `refs/hg/29_customising_ships.md`

Implemented and covered:

- concrete fixed mounts and turrets
- turret/fixed-mount weapons from the High Guard Turret Weapons table: beam
  laser, fusion gun, laser drill, missile rack, particle beam, plasma gun,
  pulse laser, railgun, and sandcaster
- barbettes, bays, spinal mounts, point-defence batteries, carronades, and
  ammunition/storage parts
- hardpoint/firmpoint capacity checks
- small-craft firmpoint restrictions
- High Guard weapon customisation modifiers

Deliberate policies:

- firmpoint range limitations are combat/operations scope, not construction
  calculations; see RIS-019.
- Ceres uses the High Guard Turret Weapons table as the compatibility boundary
  for fixed mounts and turrets and does not add extra construction-time
  restrictions; see RIS-020.

Possible future weapon families from non-HG sources should be opened as
source-specific todos when those sources are being implemented.

## Additional Sensor Suites

High Guard sensor option coverage from `refs/hg/26_drones.md` is complete for
the currently modelled ship-building scope.

Implemented and covered:

- `CountermeasuresSuite` and `MilitaryCountermeasuresSuite`
- `DeepPenetrationScanners`
- `DistributedArray`, `ExtendedArrays`, `RapidDeploymentExtendedArrays`, and
  `ExtensionNet`
- `LifeScanner` and `LifeScannerAnalysisSuite`
- `MailDistributionArray`
- `MineralDetectionSuite`
- `ShallowPenetrationSuite`
- `ImprovedSignalProcessing` and `EnhancedSignalProcessing`

Operational scanner procedures, range detail adjudication, jamming resolution,
and scan timing are represented as notes or remain out of scope for
`ceres.make.ship`.

## Replace string identity checks on career/assignment in CharacterSummary

Added `advancement_is_special() -> bool` to `CareerData` (returns `False`) and
overridden in `PrisonerCareerData` (returns `True`), replacing the
`career.name == 'Prisoner'` string check in `AdvancementEvent` and
`queue_reenlist_or_aging`. Added `assignment_by_index(index: int)` and
`assignment_index(assignment)` methods to `CareerData` for 1-based int-indexed
assignment lookup. Changed `ranks_by_assignment` from `dict[str, ...]` to
`dict[int, ...]` in all eight career files that use it (`agent.py`, `citizen.py`,
`drifter.py`, `entertainer.py`, `merchant.py`, `noble.py`, `rogue.py`, and
`scholar.py`). Changed `assignment_ranks` and `available_tables` signatures from
`str` to `int`. Added `current_assignment_index: int | None` and
`last_assignment_index: int | None` to `CharacterSummary`, and `assignment_index:
int` to `CareerTerm`. Updated all call sites in `events.py` and `career_data.py`
to pass and read assignment indexes instead of name strings, including
`_survive_pending`, `_advancement_pending`, `_start_new_career_term`, all five
`available_tables` call sites, and `AssignmentChangeChoiceEvent`. Updated
`AgentCareerData.prior_terms` to compare `term.assignment_index` instead of the
assignment name string. The circular-import constraint between `prisoner.py` and
`events.py` was solved by the `advancement_is_special()` polymorphism pattern —
no direct import of `PrisonerCareerData` is needed in `events.py`. Display code
continues to use `current_assignment: str | None` unchanged.

## Plasma Drives

Spinward Extents plasma drive construction coverage is complete for the
currently modelled ship-building scope.

Reference: `refs/spinext/59_arcturus.md`.

Implemented and covered:

- `SpinExtPlasmaDrive` in `src/ceres/make/ship/drives/spinext.py`
- available at TL8
- uses standard liquid hydrogen fuel
- tonnage is 20% of hull tonnage per Thrust
- cost is MCr0.4 per ton
- each ton of plasma drive requires 1 Power
- fuel use is 1% per Thrust per hour
- does not require or benefit from a gravity field, so it works in deep space
- plasma-drive-specific modifiers from the source: Energy Efficient, Fuel
  Efficient, Size Reduction, Energy Inefficient, Increased Size, and Fuel
  Inefficient

Operational planetary-use details remain out of scope for `ceres.make.ship`.

## Replace `ScheduledEffect` with domain-owned term state

`CharacterProjection.scheduled_effects` was a generic queue for unrelated
Traveller concepts. All uses have been migrated to explicit domain fields and
the mechanism deleted.

Implemented across `docs/plan-career-term-and-muster-out.md` (now archived):

- `MusterOut` model on `CareerTerm` owns extra/lost rolls, benefit-roll DMs,
  cash-roll count, and benefits. `CharacterSummary.benefits` and
  `muster_out_cash_count` became read-only aggregate properties.
- `allows_assignment_change: ClassVar[bool]` on `CareerData` replaced the
  CAREER_CATEGORY scheduled effect and drives `CareerTerm.continue_career_run_from()`.
- `CharacterProjection.pending_advancement_dm: int` replaced all
  `EffectTrigger.ADVANCEMENT` scheduled effects (career events, precareer
  graduation, AdvancementDmChoiceEvent). Consumed and reset to 0 in
  `AdvancementEvent`, `CommissionEvent`, and `_apply_prisoner_advancement`.
- `CharacterProjection.pending_qualification_dm: int` replaced all
  `EffectTrigger.QUALIFICATION` scheduled effects (University/Spacer Community
  graduation, Drifter event 3, Life Event roll 9).
- `CharacterProjection.auto_qualify_careers: list[str]` replaced all
  `EffectTrigger.AUTO_QUALIFY` scheduled effects (Military Academy graduation
  and failed graduation above natural 2).
- `ScheduledEffect`, `EffectTrigger`, `EffectType`, and
  `src/ceres/character/effect_enums.py` deleted.

## Character creation: eliminate remaining semantic strings — multi-phase handler context strings

Sub-section "Replace remaining `CareerDispatchEffect` registry dispatch with effect subclasses"
from the "eliminate remaining semantic strings" todo.

The `context='secondary_key'` string pattern that linked multi-phase handlers
(`PendingCareerChoice(context='prisoner_mishap_3_fight')`,
`PendingCareerSkillRoll(context='scholar_event_8_roll')`, etc.) has been fully
replaced with typed `ChoiceBase` subclasses and `PendingChoices`. Every previously
named affected pair (prisoner, drifter, scholar, merchant, rogue, noble, citizen,
entertainer, marines, scout) now expresses its multi-phase logic via:

- A typed `ChoiceBase` subclass whose `handle()` creates the follow-on pending input
- A typed `PendingXxxSkillRoll(CareerSkillRollPendingBase)` subclass for the
  second-phase roll, with its own `Literal` kind and `resolve()` logic

`PendingCareerChoice(context=...)` and `PendingCareerSkillRoll(context=...)` with
bare string cross-references no longer exist. `get_career_handler(context: str)`
registry lookup is gone. All test assertions use the typed pending/choice classes.

`PendingChoices.choices: list[SerializeAsAny[ChoiceBase]]` uses the registry pattern
(each `ChoiceBase` subclass registers its `kind: Literal[...]`) so no discriminated
union needs to be maintained.

## Character creation: eliminate remaining semantic strings — events.py, state.py, pending.py decomposition

Sub-sections "Make replay a dumb mailman — migration slice 2 (move pending-input
classes out of events.py)" and related structural decomposition from the "eliminate
remaining semantic strings" todo.

`src/ceres/character/events.py` deleted. All 70+ event handler classes and pending
input classes moved to their owning domain modules:

- Career events and pending types → `domain/career/career_events.py`
- Career shared pending bases → `domain/career/common_pending.py`
- Health/injury events and pendings → `domain/health/health_events.py`
- Homeworld events and pendings → `domain/homeworld/homeworld_events.py`
- Pre-career events and pendings → `domain/precareer/precareer_events.py`
- Character-start events and pendings → `domain/character_start.py`

`src/ceres/character/mechanism/pending.py` (the `AnyPending` discriminated union)
deleted. `PendingInputBase` gained a `_registry: ClassVar[dict[str, type]]` and
`__init_subclass__` auto-registration (same pattern as `EventHandlerBase`). The
`CharacterProjection.pending_inputs` field uses `BeforeValidator(_deserialise_pending_input)`
for round-trip deserialization without a maintained discriminated union.

`src/ceres/character/state.py` decomposed into:

- `mechanism/errors.py` — `ReplayError`
- `mechanism/pending_input.py` — `ChoiceBase`, `PendingInputBase`, `_deserialise_pending_input`
- `mechanism/character_state.py` — `CharacterSummary`, `CharacterProjection`, `diff_summaries`
- `domain/career/career_data.py` — `BenefitRollDm`, `MusterOut`, `CareerTerm` appended

All ~55 files importing from `state.py` or `events.py` migrated to the new locations.
`state.py` deleted after migration.

Dedicated unit tests for `mechanism/event_base.py` and the `PendingInputBase` registry
added to `tests/character/test_event_base.py`.

## Character creation: make replay a dumb mailman

Sub-section "Make replay a dumb mailman; move lifecycle rules out of `Event.apply()`"
from "Character creation: eliminate remaining semantic strings".

**Root-event routing via `init_replay()`:**

`EventHandlerBase` gained `init_replay(self, character_id: int, event_id: int) -> Any`
returning `None` by default. `CharacterStartedHandler` overrides it to build and return
the initial `CharacterProjection` with `CharacterSummary` populated from its own fields
and `PendingUcp` appended. `replay.py` now calls `events[0].handler.init_replay(...)` and
raises `ReplayError` if `None` is returned — no more `isinstance(events[0].handler,
CharacterStartedHandler)` checks and no domain imports in `replay.py`.

Migration slice 1 (domain-owned root handler) and slices 2 and 4 (from the previous
session) are all complete. All four slices done.

**DB schema change:**

`character_events` table renamed to `events`. Two new integer columns added alongside
the JSON payload: `fulfills_event_id INTEGER` and `fulfills_seq INTEGER`, storing the
`(event_id, seq)` identity of the pending input fulfilled by each event. The
`pending_inputs` table described in the original plan was omitted — pending inputs
remain fully derived state rebuilt by replay, so no authoritative storage is needed.
All SQL in `store.py` updated accordingly.

## Mishap 1 choice (all careers)

Core gives a choice between the severe-injury result and rolling twice on the
Injury table and taking the lower result. Implemented via `CommonMishap1Handler`
in `common.py`, used by all careers (Agent, Army, Citizen, Drifter, Entertainer,
Marines, Merchant, Navy, Noble, Prisoner, Rogue, Scholar, Scout).

## Scout Event 12: automatic promotion

Core automatically promotes the Traveller. Implemented with `AutoAdvanceEffect()`.

## Drifter Event 10: increase any existing skill by one level

Core says "increase any skill you already have by one level." Previous implementation used
`SkillChoiceEffect(options=[], level=1)` which produced an empty select with no choices.
Fixed with `DrifterEvent10Handler` that builds `PendingSkillChoice` from the character's
current skills with `level=None` (increment mode).
