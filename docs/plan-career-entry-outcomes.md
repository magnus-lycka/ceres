# Plan: Replace Career Effects with Typed Entry Outcomes

## Problem

The career tables used to carry a YAML-era shape:

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

The old mixed model was also internally inconsistent:

- Some effects applied themselves with `effect.apply(...)`.
- Other effects were interpreted with `isinstance(...)` branches inside
  `MishapHandler`, `TermEventHandler`, and `PreCareerEventHandler`.
- `CareerHandlerBase` subclasses were already closer to "custom table rows"
  than effects.

The result was neither a clean declarative data model nor clean polymorphism.

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
  `MishapEntry` are now thin aliases of the shared entry base.
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
- Phase 5 is complete for career and pre-career tables: legacy `*Effect`
  classes, `AnyEffect`, `effects` fields, and effect-dispatch branches have
  been removed from the character domain.

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

Status: **complete**.

#### Pre-career effect inventory

Inspection shows the remaining live pre-career event effect data is
concentrated in `PreCareerData.events`, the shared event table used by all
pre-careers. The loader no longer owns rule data.

The desired migration direction is to make pre-careers follow the same broad
pattern as careers: term data should be owned by `TermData`-derived classes,
not assembled as mostly-anonymous instances in a loader. `TermData` lives in
`src/ceres/character/domain/term_data.py`; anything genuinely shared by careers
and pre-careers belongs there rather than in `career_data.py`.

That does not mean one flat class per current row of data. Commonality should
inform the inheritance tree:

- a shared `PreCareerData` base owns mechanics common to all pre-careers
- intermediate subclasses such as military academy or merchant academy own
  genuinely shared entry/graduation behavior
- concrete pre-careers such as University, Army Academy, Navy Academy, and
  Colonial Upbringing own their named table data
- shared pre-career event row classes represent repeated event-table outcomes
  in the same spirit as shared career table entries

Avoid a separate mixin layer unless a real second inheritance axis appears.
Shared pre-career behavior should live on `PreCareerData` or an intermediate
pre-career superclass. Shared career/pre-career behavior should move to
`TermData`.

Pre-career event rows migrated to typed entries:

- roll 2: `NoEffectEntry`, with the existing manual psionics note still handled
  by `PreCareerEventHandler`
- roll 3: `NoEffectEntry`, with terminal "fail to graduate" flow still handled
  by `PreCareerEventHandler`
- roll 4: `NoEffectEntry`, with the existing manual SOC/Rival/Enemy note still
  handled by `PreCareerEventHandler`
- roll 5: `GainSkillEntry(Carouse())`
- roll 6: `RolledConnectionsEntry(ALLY, d3)`
- roll 7: `LifeEventEntry`
- roll 8: `GainConnectionsEntry([ALLY, ENEMY])`
- roll 9: `SkillChoiceEntry(level=0)` with empty options meaning "any skill"
- roll 10: `GainConnectionEntry(RIVAL)`
- roll 11: `NoEffectEntry`, with terminal draft/fail-to-graduate flow still
  handled by `PreCareerEventHandler`
- roll 12: `NoEffectEntry`, with the existing SOC increase still handled by
  `PreCareerEventHandler`

Rolls 2, 3, 4, and 11 are not simple effect replacements. They encode
pre-career-specific manual notes or terminal flow and should become explicit
pre-career event rows instead of being hidden in post-effect `if self.roll`
branches if we want to continue flattening `PreCareerEventHandler`.

Current test touchpoints:

- `tests/character/test_events_pending_inputs.py` covers the pending-input,
  manual-note, and terminal branches for `PreCareerEventHandler`.
- `tests/character/test_precareers.py` asserts that the shared pre-career event
  rows are typed entries and have no `effects` payloads.
- `tests/character/test_career_data.py` now covers table entries, not legacy
  effect internals.

Progress:

- `TermData` now lives in `src/ceres/character/domain/term_data.py`, so
  pre-careers no longer import the shared term base from `career_data.py`.
- All loaded named pre-careers now have distinct concrete `PreCareerData`
  subclasses. Military and merchant academies still share behavior through
  intermediate academy superclasses.
- Named pre-career configuration now lives on concrete classes; `loader.py`
  instantiates those classes instead of passing rule data through constructors.
- Pre-career event rows 5, 6, 7, and 10 now use typed entries instead of
  effect wrappers.
- Pre-career event rows 2, 3, 4, 8, 9, 11, and 12 are now typed entries as well.
- `AnyEffect`, the old `*Effect` classes, the `effects` fields, legacy handler
  dispatch, and tests guarding effect internals have been removed.

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
  interpretation. **Done.**
- `PreCareerEventHandler` no longer contains legacy effect interpretation.
  **Done.**
- Direct career-table state changes are named projection methods or typed entry
  outcomes, not tiny effect wrappers. **Done.**
- Custom career rows are direct `CareerHandlerBase` table entries with domain
  names. **Done.**
- Tests are at the right abstraction level for the career-entry migration.
  **Done for this refactor.**
