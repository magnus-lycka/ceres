# Plan: Self-Addressed Envelopes for Career Choices

## Problem

The current "choose A or B" pattern requires a separate `PendingXxxChoice` class for every
decision point. Each class encodes the logic for _all_ branches in its `on_choice()` method,
matching against raw string constants:

```python
class PendingCitizenEvent8(CareerChoicePendingBase):
    kind: Literal['citizen_event_8'] = 'citizen_event_8'

    def on_choice(self, projection, event) -> None:
        if event.choice == 'use_it':
            ...
        else:  # 'refuse'
            ...
```

Problems with this:
- The handler class has to know about all option strings and all branches.
- The mapping from string to logic is implicit. A typo in `'refuse'` silently does nothing.
- Adding an option requires editing the same class in two places (options list and on_choice).
- There is no discoverable relationship between an option and what it does.
- There are ~20 such classes across all career modules, each doing the same dispatch pattern.

The current code for Citizen Event 8 also contains a bug: the rule says the character gains
"DM+1 to a Benefit roll **and** gains Streetwise 1, Deception 1 **or** a criminal Contact."
The current implementation ignores the second part entirely. The complexity of the dispatch
machinery obscured this during implementation.

## Solution

Give each option its own class — a **self-addressed envelope**. The class knows what to do
when selected. The generic pending and dispatch mechanism ("mailman") only needs to present
options and deliver the selected one; it has no knowledge of what's inside.

## Core Design

### `ChoiceBase`

```python
class ChoiceBase(BaseModel):
    kind: str
    label: str  # shown to the user in the UI

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        raise NotImplementedError
```

Each option is a concrete subclass with `kind: Literal[...]` and its own `handle()`.

### `PendingChoices`

One generic pending class replaces all `PendingXxxChoice` classes:

```python
class PendingChoices(PendingInputBase):
    kind: Literal['choices'] = 'choices'
    choices: list[AnyChoice]  # discriminated union

    def event_from_form(self, form) -> AnyEvent:
        return CareerChoiceEvent(choice=form_str(form, 'choice', ''), fulfills=self.id)

    def input_specs(self, projection) -> list[InputSpec]:
        return [Select(name='choice', label=self.instruction,
                       options=[(c.label, c.kind) for c in self.choices])]
```

`AnyChoice` is a Pydantic discriminated union of all concrete choice classes (see below).

### Dispatch: `CareerChoiceEvent`

`CareerChoiceEvent` carries `choice: str` (the selected choice's `kind`). Its `apply()` is
updated to dispatch via the choice object rather than via `fulfilled_pending.on_choice()`:

```python
class CareerChoiceEvent(EventBase):
    kind: Literal['career_decision'] = 'career_decision'
    choice: str

    def apply(self, projection, fulfilled_pending=None) -> None:
        if fulfilled_pending is None:
            raise ReplayError('CareerChoiceEvent has no matching pending input')
        selected = next((c for c in fulfilled_pending.choices if c.kind == self.choice), None)
        if selected is None:
            raise ReplayError(f'Unknown choice {self.choice!r}')
        selected.handle(projection, self)
```

The event log format is unchanged: `career_decision` with a `choice` string. The string is
now the choice's `kind` rather than an arbitrary label, which makes it self-documenting.

## Citizen Event 8 — Worked Example

```python
# citizen.py

class CitizenEvent8DoSo(ChoiceBase):
    kind: Literal['citizen_event_8_do_so'] = 'citizen_event_8_do_so'
    label: str = 'Choose to do so'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        # DM+1 to benefit roll
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger=EffectTrigger.MUSTER_OUT_ADD,
                source_event_id=event.id,
                effect={'type': EffectType.ADD, 'value': 1},
            )
        )
        # Now choose Streetwise 1, Deception 1, or a criminal Contact
        choices: list[AnyChoice] = []
        if projection.summary.skill_level(Streetwise) is None:
            choices.append(CitizenEvent8GainStreetwise())
        if projection.summary.skill_level(Deception) is None:
            choices.append(CitizenEvent8GainDeception())
        choices.append(CitizenEvent8GainContact())
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event.id}.0',
                instruction='Choose your reward',
                choices=choices,
            )
        )
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id, 1))


class CitizenEvent8Refuse(ChoiceBase):
    kind: Literal['citizen_event_8_refuse'] = 'citizen_event_8_refuse'
    label: str = 'Refuse'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        pass


class CitizenEvent8GainStreetwise(ChoiceBase):
    kind: Literal['citizen_event_8_gain_streetwise'] = 'citizen_event_8_gain_streetwise'
    label: str = 'Streetwise 1'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        projection.grant_skill(Streetwise(level=Level(value=1)))


class CitizenEvent8GainDeception(ChoiceBase):
    kind: Literal['citizen_event_8_gain_deception'] = 'citizen_event_8_gain_deception'
    label: str = 'Deception 1'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        projection.grant_skill(Deception(level=Level(value=1)))


class CitizenEvent8GainContact(ChoiceBase):
    kind: Literal['citizen_event_8_gain_contact'] = 'citizen_event_8_gain_contact'
    label: str = 'Criminal Contact'

    def handle(self, projection: CharacterProjection, event: Any) -> None:
        projection.summary.connections.append(
            Contact(source='Criminal contact (Citizen event 8)')
        )


class CitizenEvent8Handler(CareerHandlerBase):
    type: Literal['citizen_event_8'] = 'citizen_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'You learn something you should not have – a corporate secret, a political '
                    'scandal – which you can profit from illegally. If you choose to do so, then '
                    'you gain DM+1 to a Benefit roll from this career and gain Streetwise 1, '
                    'Deception 1 or a criminal Contact. If you refuse, you gain nothing.'
                ),
                choices=[CitizenEvent8DoSo(), CitizenEvent8Refuse()],
            )
        )
        return pending_idx + 1
```

This is the full rule, correctly implemented. Compare with the current 60-line version that
also misses the second benefit.

## The `AnyChoice` Registry

Each concrete choice class needs a `kind: Literal[...]` discriminator. Pydantic requires
a discriminated union of all possible choice classes to serialize/deserialize `PendingChoices`.

This union lives in a new module, `src/ceres/character/choices.py`, that imports all concrete
choice classes from career modules and assembles `AnyChoice`:

```python
# choices.py
from ceres.character.careers.citizen import (
    CitizenEvent8DoSo,
    CitizenEvent8GainContact,
    CitizenEvent8GainDeception,
    CitizenEvent8GainStreetwise,
    CitizenEvent8Refuse,
    ...
)
# ... all other career choice imports

type AnyChoice = Annotated[
    CitizenEvent8DoSo
    | CitizenEvent8Refuse
    | CitizenEvent8GainStreetwise
    | ...
    Field(discriminator='kind'),
]
```

`ChoiceBase` and `PendingChoices` live in `events.py` or `state.py`; `choices.py` depends on
them but they do not depend on `choices.py`. Career modules depend on `ChoiceBase` only.
`PendingChoices` uses `TYPE_CHECKING` to reference `AnyChoice` for the type annotation while
the actual validator is set after the union is assembled — the same pattern used elsewhere in
the codebase for forward references.

## What Changes

- `CareerChoicePendingBase` and its `on_choice()` mechanism are removed.
- All `PendingXxxChoice` subclasses across career modules are removed.
- Their logic moves into per-option `ChoiceBase` subclasses.
- `CareerChoiceEvent.apply()` dispatches through the choice object rather than the pending.
- `PendingChoices` is added to `AnyPending`.
- `AnyChoice` union is maintained in `choices.py`.

Generic life event choices (`PendingLifeEventChoice`) also convert; they live in `events.py`
and the corresponding choice classes belong there too.

## What Does Not Change

- **`CareerSkillRollPendingBase` and subclasses** — dice-roll outcomes are a separate mechanism.
  The same "self-addressed envelope" idea could apply here eventually: a `SkillRollPending`
  could hold a success handler and a failure handler. That is a separate plan.
- **Numeric entry pendings** (`PendingUcp`, `PendingSurvive`, `PendingAdvancement`, etc.) — no
  branch dispatch involved.
- **`PendingHomeworldChangeRequired/Offered`** — world selection, not a choice between options.
- **`PendingSkillTable`, `PendingMusterOut`, `PendingSkillChoice`, etc.** — domain-specific, not
  the choice-dispatch pattern.
- **`CareerChoiceEvent` kind and `choice: str` field** — the serialized event log format is
  unchanged.

## Migration Strategy

Incremental by career. Each career can be migrated independently:

1. Add `ChoiceBase`, `PendingChoices`, `choices.py` skeleton; update `CareerChoiceEvent.apply()`.
2. Migrate one career at a time: replace `PendingXxxChoice` classes with choice classes +
   `PendingChoices` usage; add new choices to `AnyChoice`.
3. Remove `CareerChoicePendingBase` once all subclasses are gone.

The test suite gates each step. Existing tests for choice behaviour can be updated to use
the new pending/choice types as each career is migrated.
