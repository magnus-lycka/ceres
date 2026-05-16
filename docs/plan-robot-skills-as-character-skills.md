# Plan: Robot Skills As Shared Character Skills

## Goal

Robot skills should use the same canonical skill model as Traveller characters
once character creation and character skill handling exist in Ceres.

The robot layer should not own a separate string-only skill universe. A robot
skill package such as `Electronics (remote ops) 1`, a primitive package grant
such as `Profession (domestic cleaner) 2`, and a future character skill such as
`Pilot (spacecraft) 1` should all refer to the same skill identity model.

The robot layer should still own robot-specific construction rules:

- skill package cost from Robot Handbook skill package tables
- bandwidth use
- installed package level
- robot brain skill DM
- primitive/basic brain bundled skill grants
- robot-specific restrictions on what brains may run skill packages

The shared character skill layer should own:

- canonical skill names
- specialities and broad-skill naming policy
- display formatting
- validation and aliases
- source/rules notes for skill identity

This mirrors the direction in `docs/plan-gear-backed-robot-options.md`: generic
facts live in the generic domain, and robot-specific installation/build rules
adapt them for robot construction.

## Current State

Robot skills are currently represented with plain strings.

`ceres.make.robot.skills` contains:

- `SkillGrant(name: str, level: int)`
- `SkillPackage(name: str, level: int, bandwidth: int)`
- `_SKILL_BASE_COSTS: dict[str, float]`
- primitive/basic package grants such as `SkillGrant('Recon', 0)`

This works for early robot examples, but it means robot construction currently
duplicates or guesses skill identity. It also means spelling, specialities, and
future character rules can drift between subsystems.

The same conceptual skill names already appear elsewhere, especially in
`ceres.gear.software.Expert`, where skill strings are validated against a known
skill table and unknown skills fall back with warnings.

`docs/RULE_INTERPRETATIONS.md` already includes skill interpretation policy for
broad skills and specialities. That policy should eventually be enforced by a
shared skill model rather than by scattered string handling.

## Proposed Shared Skill Model

When character support exists, add a shared skill module. Possible location:

```text
src/ceres/character/skills.py
```

or, if the model is deliberately not character-specific:

```text
src/ceres/rules/skills.py
```

The shared model should provide a canonical skill identity object. A possible
shape:

```python
class Skill(CeresModel):
    name: str
    speciality: str | None = None

    @property
    def display_name(self) -> str: ...
```

and a level-bearing value:

```python
class SkillLevel(CeresModel):
    skill: Skill
    level: int
```

The exact API can differ, but it should support:

- `Admin`
- `Recon`
- `Electronics (remote ops)`
- `Profession (domestic cleaner)`
- broad skills such as `Space Science (Planetology)` where applicable
- language skills according to the current Ceres interpretation

The key rule is that a skill package, a character sheet, an Expert package, and
a robot option should all point at the same canonical skill identity.

## Robot Adaptation

Robot package classes should keep robot-specific semantics while replacing raw
skill strings with shared skill objects.

Current style:

```python
SkillPackage(name="Electronics (remote ops)", level=1, bandwidth=1)
SkillGrant("Recon", 0)
```

Target style:

```python
RobotSkillPackage(skill=Skill.parse("Electronics (remote ops)"), level=1, bandwidth=1)
SkillGrant(skill=Skill.parse("Recon"), level=0)
```

or, if `SkillLevel` exists:

```python
SkillGrant(skill_level=SkillLevel(skill=Skill.parse("Recon"), level=0))
```

Compatibility constructors may accept strings during migration, but internal
storage should be typed.

## Important Distinction

A robot skill package is not the same thing as a character personally knowing a
skill.

The shared skill model should define *what skill is being referred to*. The
robot package should define *how that skill is installed into a robot brain*.

Examples:

- A character has `Electronics (remote ops) 1`.
- A robot has a `RobotSkillPackage` for `Electronics (remote ops)` at package
  level 1, consuming bandwidth and costing according to Robot Handbook.
- An Expert software package may support the same skill identity but has CSC
  software TL/cost/rating rules.

These are different rule objects using the same underlying skill identity.

## Source Mapping

The first implementation pass should map the robot skill package table to the
future canonical skill table.

Robot skill package base costs currently include broad entries such as:

- `Admin`
- `Athletics`
- `Electronics`
- `Profession`
- `Science`
- `Tactics`

Installed packages and example robots may include specialities, such as:

- `Electronics (remote ops)`
- `Profession (domestic cleaner)`
- `Profession (labourer)`
- `Athletics (dexterity)`
- `Flyer (grav)`
- `Science (robotics)`

The cost table may apply to the broad/base skill while the installed package
uses a speciality. That mapping should be explicit:

```python
RobotSkillPackage(skill=Skill.parse("Electronics (remote ops)")).base_cost_key
```

should resolve to the Robot Handbook `Electronics` row, not to an unrelated
fallback.

Do not use robot test examples as rules sources. If a skill spelling or
speciality appears in an example but is not present in source rules, treat it as
an input gap or alias question.

## Relationship To Expert Software

`ceres.gear.software.Expert` already has skill-name validation and fallback
behaviour. Once shared skills exist, Expert should also move toward that shared
skill model.

Preferred direction:

- `Expert(skill=Skill.parse("Admin"), rating=1)`
- `RobotSkillPackage(skill=Skill.parse("Admin"), level=1, bandwidth=1)`
- character sheets use the same `Skill` identity

Expert should continue to own CSC software TL/cost/rating rules. Robot skill
packages should continue to own Robot Handbook bandwidth and package cost.

## Migration Plan

### Phase 1: Define Shared Skill Identity

- Implement or identify the canonical skill model used by character support.
- Include parsing from current display strings.
- Include display formatting back to the current strings.
- Include aliases only when backed by source rules or documented Ceres
  interpretations.
- Add tests for known skill names, specialities, and broad-skill policy.

### Phase 2: Add Robot Compatibility Layer

- Let `SkillGrant` accept either `Skill` or the existing string input.
- Let `SkillPackage` accept either `Skill` or the existing `name` string.
- Store a typed skill internally.
- Preserve current `skills_display` output exactly.
- Preserve current serialization long enough for existing examples to migrate.

### Phase 3: Move Robot Cost Lookup To Skill Identity

- Replace `_SKILL_BASE_COSTS` string lookup with a table keyed by canonical skill
  or broad-skill key.
- Add explicit broad-key resolution for specialities:
  - `Electronics (remote ops)` -> `Electronics`
  - `Profession (domestic cleaner)` -> `Profession`
  - `Science (robotics)` -> `Science`
- Keep Robot Handbook cost math: base cost multiplied by `10**level`.

### Phase 4: Convert Primitive And Basic Grants

- Replace primitive/basic package `SkillGrant` strings with typed skill grants.
- Keep function packages such as `clean`, `servant`, and `locomotion` in the
  robot brain layer; those are robot programming concepts, not generic skills.
- Add unit tests that primitive/basic package skill output remains unchanged.

### Phase 5: Convert Advanced Brain Installed Packages

- Migrate `AdvancedBrain.installed_skills` and similar fields to typed
  `RobotSkillPackage` objects.
- Keep a compatibility alias for existing tests and examples until all call
  sites are migrated.
- Verify brain skill DM still adjusts the displayed granted skill level without
  altering the installed package's own level.

### Phase 6: Align Expert And Character Skills

- Update `ceres.gear.software.Expert` to use the shared skill identity.
- Ensure Expert fallback warnings still exist for unsupported or unfamiliar
  skills.
- Ensure character skills, Expert software, and robot skill packages all render
  the same canonical display strings.

## Test Expectations

Shared skill tests should validate:

- parsing and formatting for plain skills
- parsing and formatting for specialities
- broad-skill policy from `docs/RULE_INTERPRETATIONS.md`
- aliases and rejected unknowns

Robot unit tests should validate:

- package cost still follows Robot Handbook base cost by broad skill
- package bandwidth remains robot-specific
- primitive/basic grants produce the same visible skill rows
- brain skill DM still adjusts grants correctly
- old string inputs still work during migration

Robot validation examples should continue to compare produced builds to
`_expected` values. Detailed skill identity and cost rules should live in unit
tests.

## Open Questions

- Should the shared module live under `ceres.character`, `ceres.rules`, or
  another neutral location?
- Should `Skill` and `SkillLevel` be frozen Pydantic models, dataclasses, or
  simple value objects?
- Should unknown skills be rejected immediately, or allowed with warning notes
  like current Expert software?
- How should Robot Handbook broad skill rows interact with Traveller Companion
  broad-skill changes?
- Should robot skill packages be a subtype of shared software package once
  `docs/plan-robot-brains-as-computers.md` is implemented?
- How should localized/source spelling differences be represented without
  leaking aliases into display output?

## Non-Goals For The First Pass

- Do not implement character creation just to migrate robot skills.
- Do not remove robot-specific bandwidth, package cost, or brain DM rules.
- Do not infer new skill names from examples without a source.
- Do not force all robot programming functions to become generic skills.
