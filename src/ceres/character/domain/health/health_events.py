from collections.abc import Mapping
from typing import Literal

from pydantic import Field

from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.input_specs import InputSpec, NumberEntry, Select, form_int, form_str
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import PendingInputBase


class CharacteristicChoiceHandler(EventHandlerBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'
    characteristic: Chars
    amount: int = 1

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        char = self.characteristic
        current = projection.summary.characteristics.get(char, 0)
        projection.summary.characteristics[char] = max(0, current - self.amount)
        if isinstance(fulfilled_pending, PendingNearlyKilled):
            for other in (Chars.STR, Chars.DEX, Chars.END):
                if other != char:
                    projection.summary.characteristics[other] = max(
                        0, projection.summary.characteristics.get(other, 0) - 2
                    )
        elif isinstance(fulfilled_pending, (PendingAgingChoice, PendingAgingChoiceMental)) and not (
            check_aging_crisis(projection, event.id)
        ):
            remaining = [
                pending
                for pending in projection.pending_inputs
                if isinstance(pending, (PendingAgingChoice, PendingAgingChoiceMental))
            ]
            if not remaining:
                complete_aging(projection, event.id)


class AgingRollHandler(EventHandlerBase):
    kind: Literal['aging_roll'] = 'aging_roll'
    roll: int  # 2D result (2-12) before the term-count DM

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        if not (2 <= self.roll <= 12):
            raise ReplayError(f'Aging roll must be 2-12, got {self.roll}')

        effective = self.roll - projection.summary.terms_started_in_pre_and_careers
        pending_idx = 0
        if effective >= 1:
            complete_aging(projection, event.id)
        elif effective == 0:
            projection.pending_inputs.append(
                PendingAgingChoice(
                    pending_id=(event.id, pending_idx),
                    instruction='Aging: choose STR, DEX, or END to reduce by 1',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
        elif effective == -1:
            for _ in range(2):
                projection.pending_inputs.append(
                    PendingAgingChoice(
                        pending_id=(event.id, pending_idx),
                        instruction='Aging: choose STR, DEX, or END to reduce by 1',
                        options=[Chars.STR, Chars.DEX, Chars.END],
                    )
                )
                pending_idx += 1
        elif effective == -2:
            for char in (Chars.STR, Chars.DEX, Chars.END):
                projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 1)
            if not check_aging_crisis(projection, event.id):
                complete_aging(projection, event.id)
        elif effective == -3:
            projection.pending_inputs.append(
                PendingAgingChoice(
                    pending_id=(event.id, pending_idx),
                    instruction='Aging: choose STR, DEX, or END to reduce by 2',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
            pending_idx += 1
            for _ in range(2):
                projection.pending_inputs.append(
                    PendingAgingChoice(
                        pending_id=(event.id, pending_idx),
                        instruction='Aging: choose STR, DEX, or END to reduce by 1',
                        options=[Chars.STR, Chars.DEX, Chars.END],
                    )
                )
                pending_idx += 1
        elif effective == -4:
            for _ in range(2):
                projection.pending_inputs.append(
                    PendingAgingChoice(
                        pending_id=(event.id, pending_idx),
                        instruction='Aging: choose STR, DEX, or END to reduce by 2',
                        options=[Chars.STR, Chars.DEX, Chars.END],
                    )
                )
                pending_idx += 1
            projection.pending_inputs.append(
                PendingAgingChoice(
                    pending_id=(event.id, pending_idx),
                    instruction='Aging: choose STR, DEX, or END to reduce by 1',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
        elif effective == -5:
            for char in (Chars.STR, Chars.DEX, Chars.END):
                projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 2)
            if not check_aging_crisis(projection, event.id):
                complete_aging(projection, event.id)
        else:  # <= -6
            for char in (Chars.STR, Chars.DEX, Chars.END):
                projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 2)
            if not check_aging_crisis(projection, event.id):
                projection.pending_inputs.append(
                    PendingAgingChoiceMental(
                        pending_id=(event.id, 0),
                        instruction='Aging: choose INT or SOC to reduce by 1',
                        options=[Chars.INT, Chars.SOC],
                    )
                )


class InjuryTableHandler(EventHandlerBase):
    kind: Literal['injury_table'] = 'injury_table'
    roll: int  # 1D result (1-6) on the Injury table

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        if not (1 <= self.roll <= 6):
            raise ReplayError(f'Injury table roll must be 1-6, got {self.roll}')
        _apply_injury_table_result(projection, self.roll, event.id)


class DoubleInjuryTableHandler(EventHandlerBase):
    kind: Literal['double_injury_table'] = 'double_injury_table'
    roll1: int  # first 1D result (1-6)
    roll2: int  # second 1D result (1-6)

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        for roll in (self.roll1, self.roll2):
            if not (1 <= roll <= 6):
                raise ReplayError(f'Double injury roll must be 1-6, got {roll}')
        _apply_injury_table_result(projection, min(self.roll1, self.roll2), event.id)


class AgingCrisisHandler(EventHandlerBase):
    kind: Literal['aging_crisis'] = 'aging_crisis'
    paid: bool
    medical_roll: int = 0  # 1D result for medical cost; 0 if not paying

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        from ceres.character.domain.career.career_events import muster_out_setup

        career = projection.summary.current_career
        last_term = projection.summary.career_terms[-1] if projection.summary.career_terms else None
        deferred_mo = last_term.muster_out if last_term is not None else None
        if career is None and last_term is not None and deferred_mo is not None and deferred_mo.pending_setup:
            career = last_term.career
        if self.paid:
            for char in list(projection.summary.characteristics.keys()):
                if projection.summary.characteristics[char] == 0:
                    projection.summary.characteristics[char] = 1
            projection.pending_reenlist = None
            if career:
                muster_out_setup(projection, event.id, 0, clear_career=True)
            else:
                projection.clear_current_career()
        else:
            projection.summary.dead = True
            projection.clear_current_career()
            if deferred_mo is not None:
                deferred_mo.pending_setup = False
            projection.pending_reenlist = None


# ── Health helper functions ───────────────────────────────────────────────────


def _apply_injury_table_result(projection: CharacterProjection, roll: int, event_id: int) -> None:
    if roll == 6:
        return
    from ceres.character.domain.career.career_events import (
        PendingAdvancement,
        PendingAssignmentChangeChoice,
        PendingCareerChoice,
        PendingCommissionChoice,
        PendingMusterOut,
        PendingReenlist,
    )

    insert_at = next(
        (
            i
            for i, p in enumerate(projection.pending_inputs)
            if isinstance(
                p,
                (
                    PendingAdvancement,
                    PendingCareerChoice,
                    PendingCommissionChoice,
                    PendingMusterOut,
                    PendingReenlist,
                    PendingAssignmentChangeChoice,
                ),
            )
        ),
        len(projection.pending_inputs),
    )
    if roll == 5:
        pending: PendingCharacteristicChoice = PendingCharacteristicChoice(
            pending_id=(event_id, 0),
            instruction='Injured: choose STR, DEX, or END to reduce by 1',
            options=[Chars.STR, Chars.DEX, Chars.END],
            amount=1,
        )
    elif roll == 4:
        pending = PendingCharacteristicChoice(
            pending_id=(event_id, 0),
            instruction='Scarred: choose STR, DEX, or END to reduce by 2',
            options=[Chars.STR, Chars.DEX, Chars.END],
            amount=2,
        )
    elif roll == 3:
        pending = PendingCharacteristicChoice(
            pending_id=(event_id, 0),
            instruction='Missing Eye or Limb: choose STR or DEX to reduce by 2',
            options=[Chars.STR, Chars.DEX],
            amount=2,
        )
    elif roll == 2:
        pending = PendingSeverelyInjured(
            pending_id=(event_id, 0),
            instruction='Severely injured: roll 1D — choose STR, DEX, or END to reduce by that amount',
        )
    else:  # roll == 1
        pending = PendingNearlyKilled(
            pending_id=(event_id, 0),
            instruction=(
                'Nearly killed: roll 1D — choose STR, DEX, or END to reduce by that amount; '
                'the other two physical characteristics are each reduced by 2'
            ),
        )
    projection.pending_inputs.insert(insert_at, pending)


def complete_aging(projection: CharacterProjection, source_event_id: int) -> None:
    from ceres.character.domain.career.career_events import (
        PendingAssignmentChangeChoice,
        PendingReenlist,
        muster_out_setup,
    )

    last_term = projection.summary.career_terms[-1] if projection.summary.career_terms else None
    deferred_mo = last_term.muster_out if last_term is not None else None
    if deferred_mo is not None and deferred_mo.pending_setup:
        muster_out_setup(projection, source_event_id, 0, clear_career=False)
    else:
        career = projection.get_current_career() if projection.summary.current_career else None
        if career and career.allows_assignment_change and len(career.assignments) > 1:
            can_muster_out_ac = not projection.forced_stay
            projection.pending_inputs.append(
                PendingAssignmentChangeChoice(
                    pending_id=(source_event_id, 0),
                    muster_out=can_muster_out_ac,
                    instruction='Stay, switch assignment, or muster out?'
                    if can_muster_out_ac
                    else 'Stay or switch assignment?',
                )
            )
            projection.forced_stay = False
        else:
            can_muster_out = not projection.forced_stay
            projection.forced_stay = False
            projection.pending_inputs.append(
                PendingReenlist(
                    pending_id=(source_event_id, 0),
                    can_muster_out=can_muster_out,
                )
            )
    projection.pending_reenlist = None


def check_aging_crisis(projection: CharacterProjection, source_event_id: int) -> bool:
    if any(v == 0 for v in projection.summary.characteristics.values()):
        projection.pending_inputs = [
            p for p in projection.pending_inputs if not isinstance(p, (PendingAgingChoice, PendingAgingChoiceMental))
        ]
        projection.pending_inputs.append(
            PendingAgingCrisis(
                pending_id=(source_event_id, 0),
                instruction='Aging crisis: pay for medical care or die?',
            )
        )
        return True
    return False


# ── Health Pending Input Types ────────────────────────────────────────────────


class PendingCharacteristicChoice(PendingInputBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'
    options: list[Chars] = Field(default_factory=list)
    amount: int = 1

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=CharacteristicChoiceHandler(
                characteristic=Chars(form_str(form, 'characteristic', Chars.STR)),
                amount=self.amount,
            ),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options: list[tuple[str, str]] = [(opt, opt) for opt in self.options]
        return [Select(name='characteristic', label='Characteristic', options=options)]


class PendingSeverelyInjured(PendingInputBase):
    kind: Literal['severely_injured'] = 'severely_injured'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=CharacteristicChoiceHandler(
                characteristic=Chars(form_str(form, 'characteristic', Chars.STR)),
                amount=form_int(form, 'roll', 1),
            ),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        char_options: list[tuple[str, str]] = [(c, c) for c in (Chars.STR, Chars.DEX, Chars.END)]
        return [
            Select(name='characteristic', label='Characteristic to reduce', options=char_options),
            NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6),
        ]


class PendingNearlyKilled(PendingInputBase):
    kind: Literal['nearly_killed'] = 'nearly_killed'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=CharacteristicChoiceHandler(
                characteristic=Chars(form_str(form, 'characteristic', Chars.STR)),
                amount=form_int(form, 'roll', 1),
            ),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        char_options: list[tuple[str, str]] = [(c, c) for c in (Chars.STR, Chars.DEX, Chars.END)]
        return [
            Select(name='characteristic', label='Characteristic to reduce', options=char_options),
            NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6),
        ]


class PendingInjuryTable(PendingInputBase):
    kind: Literal['injury_table'] = 'injury_table'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=InjuryTableHandler(roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6)]


class PendingDoubleInjuryRoll(PendingInputBase):
    kind: Literal['double_injury_roll'] = 'double_injury_roll'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=DoubleInjuryTableHandler(roll1=form_int(form, 'roll1', 1), roll2=form_int(form, 'roll2', 1)),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            NumberEntry(name='roll1', label='First 1D roll (1–6)', min=1, max=6),
            NumberEntry(name='roll2', label='Second 1D roll (1–6)', min=1, max=6),
        ]


class PendingAgingRoll(PendingInputBase):
    kind: Literal['aging_roll'] = 'aging_roll'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=AgingRollHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]


class PendingAgingChoice(PendingInputBase):
    kind: Literal['aging_choice'] = 'aging_choice'
    options: list[Chars] = Field(default_factory=list)

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=CharacteristicChoiceHandler(characteristic=Chars(form_str(form, 'characteristic', Chars.STR))),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options: list[tuple[str, str]] = [(opt, opt) for opt in self.options]
        return [Select(name='characteristic', label='Characteristic', options=options)]


class PendingAgingChoiceMental(PendingInputBase):
    kind: Literal['aging_choice_mental'] = 'aging_choice_mental'
    options: list[Chars] = Field(default_factory=list)

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=CharacteristicChoiceHandler(characteristic=Chars(form_str(form, 'characteristic', Chars.STR))),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options: list[tuple[str, str]] = [(opt, opt) for opt in self.options]
        return [Select(name='characteristic', label='Characteristic', options=options)]


class PendingAgingCrisis(PendingInputBase):
    kind: Literal['aging_crisis'] = 'aging_crisis'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.mechanism.event_base import Event

        paid = form_str(form, 'paid', 'false').lower() in ('true', '1', 'yes')
        medical_roll = form_int(form, 'medical_roll', 0)
        return Event(fulfills=self.pending_id, handler=AgingCrisisHandler(paid=paid, medical_roll=medical_roll))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(
                name='paid',
                label='Medical care',
                options=[('Pay for medical care', 'true'), ('Cannot afford / decline', 'false')],
            ),
            NumberEntry(name='medical_roll', label='Medical roll (1D, if paying)', min=0, max=6),
        ]
