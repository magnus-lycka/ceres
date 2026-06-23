from collections.abc import Mapping
from typing import Literal

from ceres.character.domain.career.career_data import CareerData
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, characteristic_dm
from ceres.character.input_specs import InputSpec, NumberEntry, form_int
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import PendingInputBase


class ParoleRollHandler(EventHandlerBase):
    kind: Literal['parole_roll'] = 'parole_roll'
    roll: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        threshold = self.roll + 2
        projection.summary.parole_threshold = threshold
        projection.summary.narrative.append(f'Prisoner: Parole Threshold set to {threshold} (rolled {self.roll}+2)')


class PendingParoleRoll(PendingInputBase):
    kind: Literal['parole_roll'] = 'parole_roll'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(fulfills=self.pending_id, handler=ParoleRollHandler(roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6)]


def set_forced_prison_career(projection: CharacterProjection, description: str) -> None:
    from ceres.character.domain.career.prisoner import PRISONER

    projection.forced_next_career = PRISONER
    if projection.summary.career_terms:
        projection.summary.career_terms[-1].prison = description


def apply_prisoner_advancement(projection: CharacterProjection, event: Event, career: CareerData) -> None:
    from ceres.character.domain.career.advancement import rank_bonus_skill
    from ceres.character.domain.career.career_events import (
        PendingRankBonusChoice,
        PendingSkillTable,
        queue_reenlist_or_aging,
    )

    assignment = projection.summary.current_assignment
    if assignment is None:
        raise ReplayError('No current assignment')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
    dm += projection.pending_advancement_dm
    projection.pending_advancement_dm = 0
    effective = event.roll + dm
    parole_threshold = projection.summary.parole_threshold or 0
    freed = effective > parole_threshold
    rank_bonus_pending = None
    success = effective >= target
    if success:
        new_rank = (projection.summary.rank or 0) + 1
        projection.summary.rank = new_rank
        career.update_current_term_rank(projection)
        rank_entry = career.current_ranks(projection).get(new_rank)
        if rank_entry and rank_entry.bonus:
            bonus = rank_entry.bonus
            choices = bonus.resolve_choices()
            if choices:
                rank_bonus_pending = PendingRankBonusChoice(
                    pending_id=(event.id, 0),
                    level=bonus.level,
                    instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                    options=choices,
                )
            elif bonus.skill:
                projection.grant_skill(rank_bonus_skill(bonus))
            elif bonus.characteristic:
                char = bonus.characteristic
                projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
    if freed:
        projection.prisoner_freed = True
        projection.summary.narrative.append(
            f'Parole granted! (rolled {effective}, Parole Threshold was {parole_threshold})'
        )
    if rank_bonus_pending:
        projection.pending_inputs.append(rank_bonus_pending)
        return
    if success:
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = career.available_tables(edu, projection.summary.current_assignment)
        projection.pending_inputs.append(
            PendingSkillTable(pending_id=(event.id, 0), instruction='Choose a skill table and roll 1D', options=tables)
        )
        queue_reenlist_or_aging(projection, event.id, 1)
    else:
        queue_reenlist_or_aging(projection, event.id, 0)
