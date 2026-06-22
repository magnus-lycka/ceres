# Plan: Replace Career Effects with Typed Entry Outcomes

## Problem

The career tables still carry a YAML-era shape:

```python
CareerEventEntry(text='...', effects=[AdvancementDmEffect(amount=2)])
MishapEntry(text='...', effects=[GainSkillEffect(skill=Diplomat(level=Level(value=1)))])
```

This is no longer a good fit now that careers are Python modules. The `Effect`
classes are often middlemen between a career table row and
`CharacterProjection`.

`GainSkillEffect` is the clearest example:

```python
class GainSkillEffect(BaseModel):
    skill: AnySkill

    def apply(self, projection, source='', source_event_id=0):
        projection.grant_skill(self.skill)
```

It adds a class, discriminator, import, and `apply()` method around one direct
projection operation. Several other effects have the same smell.

The current model is also internally inconsistent:

- Some effects apply themselves with `effect.apply(...)`.
- Other effects are interpreted with `isinstance(...)` branches inside
  `MishapHandler`, `TermEventHandler`, and `PreCareerEventHandler`.
- `CareerHandlerBase` subclasses are already closer to "custom table rows" than
  effects.

The result is neither a clean declarative data model nor clean polymorphism.

## Goal

Replace generic `CareerEventEntry` / `MishapEntry` instances containing
`effects=[...]` with typed entry classes that represent the actual rule row.

The career modules should read like the Traveller tables:

```python
events = {
    7: LifeEventEntry(text='Life Event. Roll on the Life Events table.'),
    9: AdvancementDmEntry(text='You impress your superiors.', amount=2),
    12: AutoAdvanceEntry(text='Your efforts are rewarded with promotion.'),
}

mishaps = {
    4: GainSkillAndConnectionMishap(
        text='Gain a Rival and Diplomat 1.',
        skill=Diplomat(level=Level(value=1)),
        connection=ConnectionKind.RIVAL,
    ),
}
```

Handlers should dispatch to the entry object, not interpret a list of effect
objects.

## Design Direction

### Shared base

Introduce a shared base for event and mishap table rows:

```python
class CareerTableEntry(BaseModel):
    text: str

    def apply(self, projection: CharacterProjection, event: Event, pending_idx: int) -> int:
        return pending_idx

    def continues_career_progress(self) -> bool:
        return True
```

Then specialize:

```python
class CareerEventEntry(CareerTableEntry):
    pass


class MishapEntry(CareerTableEntry):
    stay_in_career: bool = False
    defer_ejection: bool = False
```

`MishapHandler` remains responsible for common mishap framing:

- append problem/narrative
- clear or retain career based on mishap flags
- start muster-out/ejection flow

The entry object owns the row's concrete outcome.

### Projection verbs

Before removing effects, add intention-revealing methods to
`CharacterProjection`. These methods make entry classes small and keep state
rules in one place:

- `grant_skill(skill)`
- `decrease_characteristic(characteristic, amount)`
- `queue_characteristic_choice(event_id, pending_idx, options, amount, instruction)`
- `add_connection(kind, origin=...)`
- `queue_connection_roll(event_id, pending_idx, kind, dice, instruction=None)`
- `queue_skill_choice(event_id, pending_idx, options, level, instruction=None)`
- `queue_injury(event_id, pending_idx, severity)`
- `queue_life_event(event_id, pending_idx)`
- `queue_mishap(event_id, pending_idx, leave=True)`
- `add_advancement_dm(amount)`
- `add_qualification_dm(amount)`
- `add_benefit_dm(amount)`
- `adjust_parole_threshold(amount)`
- `auto_qualify(career)`
- `forfeit_current_career_benefits()`

Some of these may live as helper functions rather than methods if they are
event-layer concepts, but the key is to remove duplicated pending-input
construction from handlers.

### Shared entry classes

Start with reusable common entries:

- `NoEffectEntry`
- `GainSkillEntry`
- `GainConnectionEntry`
- `GainSkillAndConnectionEntry`
- `RolledConnectionsEntry`
- `SkillChoiceEntry`
- `CharacteristicLossEntry`
- `CharacteristicLossChoiceEntry`
- `InjuryEntry`
- `RollMishapEntry`
- `LifeEventEntry`
- `AutoAdvanceEntry`
- `AdvancementDmEntry`
- `QualificationDmEntry`
- `BenefitDmEntry`
- `ParoleThresholdChangeEntry`
- `AutoQualifyCareerEntry`
- `LoseAllCareerBenefitsEntry`

Do not create a subclass for every single table row. Create shared classes for
repeated Traveller rule shapes, and use custom subclasses only where the row has
bespoke branching.

### Career-specific custom entries

Existing `CareerHandlerBase` subclasses should become custom entry classes, for
example:

- `ScoutEvent3Entry`
- `ScholarMishap5Entry`
- `ArmyEvent12Entry`
- `PrisonerEvent9Entry`

These classes should inherit from the event or mishap entry base and implement
the same `apply(...)` interface as shared entries.

This makes the naming honest: they are table rows with custom behavior, not
anonymous effects inside a generic table row.

## Migration Strategy

### Current Status

- Phase 1 is complete for this refactor: projection verbs exist for the direct
  state changes that used to sit behind small effect middlemen.
- Phase 2 is complete: `CareerTableEntry` is the shared table-row base,
  handlers dispatch typed entries directly, and `CareerEventEntry` /
  `MishapEntry` retain compatibility fields only for non-career consumers and
  any future deserialization cleanup.
- Phase 3 is complete at the career table surface: career modules no longer use
  `effects=[...]` rows. Direct outcomes, pending-input outcomes, no-op rows,
  mixed common outcomes, and bespoke career rows are represented as
  table entries.
- `CareerTableEntry` carries `stay_in_career` and `defer_ejection` framing flags
  so shared entries can be used directly in mishap tables.
- Snapshot/approval experiments are intentionally deferred; use ordinary
  focused assertions unless a complex row genuinely needs full state-delta
  characterization.
- Career table effect rows are migrated:
  `rg "effects=\[" src/ceres/character/domain/career`
  returns no matches.
- Bespoke career rows are direct `CareerHandlerBase` table entries. They no
  longer sit behind `handler=...` payloads on `CareerEventEntry` /
  `MishapEntry`.

### Phase 1: Add projection verbs

Status: **complete for career tables**.

Add small projection methods or event helper functions for repeated operations.
Move behavior without changing career data yet.

Good first targets:

- `decrease_characteristic()` including PSI cleanup
- `add_advancement_dm()`
- `add_qualification_dm()`
- `add_benefit_dm()`
- `adjust_parole_threshold()`
- `auto_qualify()`
- `forfeit_current_career_benefits()`
- `queue_skill_choice()`
- `queue_connection_roll()`

Add focused tests around these operations where coverage is currently only
indirect.

### Phase 2: Introduce entry classes beside effects

Status: **complete for career tables**.

Add `CareerTableEntry` and a few shared subclasses while keeping the existing
`effects` field working.

Allow `CareerEventEntry` and `MishapEntry` to either:

- continue accepting `effects=[...]` temporarily, or
- be replaced one table row at a time with subclasses.

The handlers can support both during migration:

```python
if isinstance(entry, CareerTableEntrySubclass):
    pending_idx = entry.apply(projection, event, pending_idx)
else:
    apply_legacy_effects(entry.effects)
```

Career modules no longer need this compatibility. The compatibility remains in
the shared data/events layer only because pre-career event tables still use
legacy effects.

### Phase 3: Migrate direct-mutation effects

Status: **complete for career tables**.

Remove the obvious middlemen first:

- `GainSkillEffect`
- `GainContactEffect`
- `GainAllyEffect`
- `GainRivalEffect`
- `GainEnemyEffect`
- `AdvancementDmEffect`
- `QualificationDmEffect`
- `BenefitDmEffect`
- `ParoleThresholdChangeEffect`
- `AutoQualifyCareerEffect`
- `LoseAllCareerBenefitsEffect`
- `DecreaseCharacteristicEffect`

These should become either entry subclasses or direct projection calls inside a
custom entry.

This phase should produce visible simplification in career modules like:

```python
effects=[GainEnemyEffect(), GainSkillEffect(skill=Deception(level=Level(value=1)))]
```

becoming:

```python
GainSkillAndConnectionMishap(
    text='Gain an Enemy and Deception 1.',
    skill=Deception(level=Level(value=1)),
    connection=ConnectionKind.ENEMY,
)
```

### Phase 4: Migrate pending/control-flow effects

Status: **complete for career tables**.

Then migrate the remaining effect-like records:

- `SkillChoiceEffect`
- `GainConnectionsRolledEffect`
- `DecreaseCharacteristicChoiceEffect`
- `InjuryEffect`
- `RollMishapEffect`
- `AutoAdvanceEffect`
- `LifeEventEffect`

These are more defensible than direct-mutation effects because they describe
pending-input or career-flow behavior. Still, they should become explicit entry
classes so the handlers no longer need large `isinstance(effect, ...)` loops.

### Phase 5: Remove legacy effect support

Status: **not complete globally**. Career tables no longer use legacy effects,
but pre-career events still do.

When all career and pre-career tables are migrated:

- delete `AnyEffect`
- delete old `*Effect` classes that no longer have callers
- remove legacy `effects` handling from handlers
- simplify tests that were only guarding effect internals
- update docs and architecture notes

## Testing Strategy

Follow `AI_README.md`:

- Add focused tests before each behavior move.
- Career rule tests use `CharacterDriver` and assert observable outcomes.
- Entry/projection tests live near the implementation and may inspect pending
  types or projection internals.

Suggested test homes:

- `tests/character/test_career_data.py` for shared entry classes.
- `tests/character/test_connection_events.py` for connection pending ordering.
- career-specific files for observable career table behavior.
- `tests/character/test_events_pending_inputs.py` only for event/pending
  mechanics and form boundaries.

Use approval/snapshot testing only for complex multi-effect deltas where "and
nothing else changed" is an important invariant.

## Risks and Open Questions

- **Entry class explosion:** avoid one class per table row unless the row has
  real custom branching.
- **Handler/projection boundary:** queueing pending inputs may belong in
  event-layer helpers rather than `CharacterProjection`; decide case by case.
- **Pre-career reuse:** pre-career events still reuse several career effect
  classes. Removing the remaining legacy effect infrastructure requires a
  separate pre-career table migration.
- **Serialization:** if table entries are ever persisted or serialized, keep
  Pydantic discriminators. If they remain static Python data, prefer simple
  Python classes and clear methods.
- **Migration churn:** change one effect family at a time and keep pre-commit
  green after each family.

## Success Criteria

- Career modules read as typed rule tables, not generic entries with effect
  lists. **Done.**
- `MishapHandler` and `TermEventHandler` no longer need legacy effect
  interpretation for career tables. **Done for career table data.**
- `PreCareerEventHandler` still contains legacy effect interpretation because
  pre-career event tables still use effects. **Separate follow-up.**
- Direct career-table state changes are named projection methods or typed entry
  outcomes, not tiny effect wrappers. **Done.**
- Custom career rows are direct `CareerHandlerBase` table entries with domain
  names. **Done.**
- Tests are at the right abstraction level for the career-entry migration.
  **Done for this refactor.**
