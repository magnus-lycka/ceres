from collections.abc import Mapping
from typing import Literal, cast

from ceres.character.domain.benefits import AnyBenefit
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.input_specs import InputSpec, NumberEntry, Select, form_int, form_str, literal
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase, PendingInputBase


class MusterOutHandler(EventHandlerBase):
    kind: Literal['muster_roll'] = 'muster_roll'
    table: Literal['cash', 'benefits']
    roll: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        if not projection.summary.career_terms:
            raise ReplayError('No muster out career set')
        career = projection.summary.career_terms[-1].career
        effective_roll = max(1, min(7, self.roll))
        row = career.muster_out.rows.get(effective_roll)
        if row is None:
            raise ReplayError(f'No muster out row for roll {effective_roll}')
        benefit_choice_count = sum(isinstance(pending, PendingBenefitChoice) for pending in projection.pending_inputs)
        if self.table == 'cash':
            if projection.summary.muster_out_cash_count >= 3:
                raise ReplayError('Cash may only be taken a maximum of 3 times')
            projection.summary.cash += row.cash
            projection.summary.record_muster_out_cash_roll()
        else:
            for _ in range(row.count):
                row.benefit.apply(projection, event.id)
        benefit_choice_added = (
            sum(isinstance(pending, PendingBenefitChoice) for pending in projection.pending_inputs)
            > benefit_choice_count
        )
        muster_out = projection.summary.career_terms[-1].require_muster_out()
        muster_out.rolls_remaining -= 1
        if muster_out.rolls_remaining == 0:
            if benefit_choice_added:
                projection.pending_inputs[-1] = projection.pending_inputs[-1].model_copy(
                    update={'is_muster_out': True, 'muster_out_remaining': 0}
                )
            else:
                finalize_muster_out(projection, event.id)
        elif benefit_choice_added:
            projection.pending_inputs[-1] = projection.pending_inputs[-1].model_copy(
                update={'is_muster_out': True, 'muster_out_remaining': muster_out.rolls_remaining}
            )
        else:
            projection.pending_inputs.append(PendingMusterOut(pending_id=(event.id, 0)))


class BenefitChoiceHandler(EventHandlerBase):
    kind: Literal['benefit_choice'] = 'benefit_choice'
    choice_index: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        if not isinstance(fulfilled_pending, PendingBenefitChoice):
            raise ReplayError('BenefitChoiceEvent must fulfill a PendingBenefitChoice')
        options = fulfilled_pending.benefit_options
        if not (0 <= self.choice_index < len(options)):
            raise ReplayError(f'choice_index {self.choice_index} out of range for {len(options)} options')
        options[self.choice_index].apply(projection, event.id)
        if fulfilled_pending.is_muster_out:
            if fulfilled_pending.muster_out_remaining > 0:
                projection.pending_inputs.append(PendingMusterOut(pending_id=(event.id, 0)))
            else:
                finalize_muster_out(projection, event.id)


class PendingMusterOut(PendingInputBase):
    kind: Literal['muster_roll_pending'] = 'muster_roll_pending'
    instruction: str = 'Muster out: choose cash or benefits table'
    options: tuple[Literal['cash'], Literal['benefits']] = ('cash', 'benefits')

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        table = cast(
            Literal['cash', 'benefits'],
            literal(form_str(form, 'table', 'benefits'), ('cash', 'benefits'), 'benefits'),
        )
        return Event(fulfills=self.pending_id, handler=MusterOutHandler(table=table, roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        total_dm = 0
        if projection.summary.career_terms:
            muster_out = projection.summary.career_terms[-1].muster_out
            if muster_out is not None:
                total_dm = sum(dm.amount for dm in muster_out.benefit_roll_dms)
        roll_label = (
            f'1D roll (1–6); DM+{total_dm} available on benefits table'
            if total_dm
            else '1D roll (1–6, apply DMs first)'
        )
        return [
            Select(name='table', label='Table', options=[(option.title(), option) for option in self.options]),
            NumberEntry(name='roll', label=roll_label, min=1, max=7),
        ]


class PendingBenefitChoice(PendingInputBase):
    kind: Literal['benefit_choice_pending'] = 'benefit_choice_pending'
    benefit_options: list[AnyBenefit]
    muster_out_remaining: int = 0
    is_muster_out: bool = False

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(
            fulfills=self.pending_id,
            handler=BenefitChoiceHandler(choice_index=form_int(form, 'choice_index', 0)),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(
                name='choice_index',
                label='Choose benefit',
                options=[(benefit.display_label, str(index)) for index, benefit in enumerate(self.benefit_options)],
            )
        ]


def finalize_muster_out(projection: CharacterProjection, event_id: int) -> None:
    from ceres.character.domain.career.career_events import queue_career_choice_indexed

    if projection.summary.career_terms:
        projection.summary.career_terms[-1].require_muster_out().used = True
    if not projection.summary.dead:
        queue_career_choice_indexed(projection, event_id, 0, 'Start a new career, or finish character creation')


def setup_muster_out(
    projection: CharacterProjection,
    source_event_id: int,
    pending_idx: int = 0,
    clear_career: bool = True,
    ejected: bool = False,
) -> int:
    from ceres.character.domain.career.career_events import queue_career_choice_indexed

    if clear_career:
        projection.clear_current_career(ejected=ejected)
    muster_out = projection.summary.career_terms[-1].muster_out if projection.summary.career_terms else None
    if muster_out is not None:
        muster_out.setup(projection.summary.rank or 0)
    if muster_out is not None and muster_out.rolls_remaining > 0:
        projection.pending_inputs.append(PendingMusterOut(pending_id=(source_event_id, pending_idx)))
    else:
        queue_career_choice_indexed(projection, source_event_id, pending_idx)
    return pending_idx + 1
