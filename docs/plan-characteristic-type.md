# Plan: Characteristic Type

## STATUS: NOT STARTED — low priority, do not block other plans on this

## Background

Characteristics (STR, DEX, END, INT, EDU, SOC, PSI, …) are currently
represented by the `Chars` enum in `src/ceres/character/domain/character_state.py`.
The enum acts as a typed key that identifies which characteristic to read or
modify. Characteristic values are stored in `CharacterSummary` as a dict
keyed by `Chars`.

This works for basic access but creates friction in several areas:

- **Display names and abbreviations** are attached to the enum by convention,
  not by structure.
- **Modification logic** (apply a `+1`, respect a floor/ceiling, track aging
  damage) lives in `CharacterSummary` rather than in the characteristic itself.
- **Type narrowing** for subsets of characteristics (physical vs. mental vs.
  social vs. psionic) requires explicit lists or sets rather than subclass
  membership.
- **Skill-table rendering** currently emits `Chars` as an option value with a
  string like `"STR +1"`, but the form submit path cannot parse `Chars` back
  from that string — a gap that would be solved by a class that knows its own
  form value.

The user question from the findings review: "Should we have a proper
Characteristic class which we subclass instead of the simple enum?"

---

## Proposed Direction

Replace `Chars` with a class hierarchy:

```text
Characteristic (base class)
├── PhysicalCharacteristic
│   ├── Strength
│   ├── Dexterity
│   └── Endurance
├── MentalCharacteristic
│   ├── Intellect
│   └── Education
├── SocialCharacteristic
│   └── SocialStanding
└── PsionicCharacteristic
    └── Psionic
```

Each class:

- Is a singleton or small-value type (like `Skill` subclasses).
- Knows its own abbreviation (e.g., `Strength.abbreviation = "STR"`).
- Knows its display name (e.g., `Strength.name = "Strength"`).
- Can render its own form value and parse itself from form data.

`CharacterSummary` would store characteristic values keyed by `type[Characteristic]`
(or by instance if characteristics carry their value, like skills do).

---

## Design Questions to Resolve Before Implementing

### Should a Characteristic instance carry its value?

**Option A — Typed key only (like the current `Chars`):**
`Strength` is a class; `summary.characteristics[Strength]` returns the integer
value. Modification is `summary.apply_characteristic_change(Strength, +1)`.

**Option B — Value-bearing (like `Skill` instances):**
`Strength(value=7)` is an instance. `summary.characteristics` is a list or set
of `Characteristic` instances. Modification creates a new instance.

Option A is a smaller change from the current model. Option B is more consistent
with how skills work, but characteristics have stronger "you always have all of
them" semantics than skills.

### What replaces `Chars` as a dict key?

If using Option A, the dict key changes from `Chars` (enum member) to
`type[Characteristic]` (class). Serialisation: Pydantic can serialise
`type[Characteristic]` via a custom validator that maps to/from the abbreviation
string.

### How does this interact with aging and injuries?

Aging and injuries modify specific characteristics by specific amounts (sometimes
negative). The current `apply_characteristic_change(Chars, int)` signature would
become `apply_characteristic_change(type[Characteristic], int)` or similar.
That is a mechanical find-and-replace; no semantic change needed.

---

## Implementation Steps

This section will be filled in once the design questions above are answered.
Start by answering the two questions above and recording the decision here before
writing any code.

**Suggested pre-work:**

1. Read `src/ceres/character/domain/character_state.py` and list all the places
   `Chars` is used as a key, a type annotation, a dict key, and a rendered label.
2. Read `src/ceres/character/domain/career/career_data.py` for characteristic
   modification sites.
3. Check how `Chars` is used in skill table entries (`Chars` in
   `SkillTableItem`).
4. Check `src/ceres/character/domain/skill_events.py` for form rendering.
5. Decide on Option A or Option B and record here.

---

## Relationship to Other Plans

- The form-value parseable gap in `build_skill_select_options()` is tracked in
  [plan-not-gained-api.md](archive/plan-not-gained-api.md). If a `Characteristic` class
  knows how to parse itself from form data, that gap closes automatically.
- `Chars` appears in `SkillTableItem` type aliases. After this plan, the type
  alias and all its consumers (`_apply_skill_table_entry()`, etc.) will need
  updating — coordinate with [plan-not-gained-api.md](archive/plan-not-gained-api.md).
