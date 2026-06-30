from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast

from pydantic import Field

from ceres.character.domain.career.career_data import (
    AdvancementDmOption,
    AssignmentData,
    CareerData,
    CareerSkillOption,
    RankBonus,
)
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, characteristic_dm
from ceres.character.domain.psionics import PsionicTalentTrainingHandler
from ceres.character.domain.psionics_data import Psi
from ceres.character.domain.skills import AnySkill, level_fields
from ceres.character.input_specs import InputSpec, NumberEntry, Select, form_int, form_str
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase, PendingInputBase


class AdvancementHandler(EventHandlerBase):
    kind: Literal['advancement_event'] = 'advancement_event'
    roll: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        from ceres.character.domain.career.career_events import queue_reenlist_or_aging
        from ceres.character.domain.career.prisoner_events import apply_prisoner_advancement

        career = projection.get_current_career()
        if career.advancement_is_special():
            apply_prisoner_advancement(projection, event, career)
            return
        assignment = projection.summary.current_assignment
        if assignment is None:
            raise ReplayError('No current assignment')
        dm = characteristic_dm(projection.summary.characteristics.get(assignment.advancement.characteristic, 0))
        dm += projection.pending_advancement_dm
        projection.pending_advancement_dm = 0
        success = (self.roll + dm) >= assignment.advancement.target
        terms_in_career = len(career.prior_terms(projection.summary.career_terms, assignment))
        if self.roll == 12:
            projection.summary.career_terms[-1].forced_stay = True
        elif self.roll <= terms_in_career:
            projection.summary.career_terms[-1].forced_leave = True
        if not success:
            queue_reenlist_or_aging(projection, event.id, 0)
            return
        _apply_promotion(projection, career, event.id)


class CommissionHandler(EventHandlerBase):
    kind: Literal['commission'] = 'commission'
    attempt: bool
    roll: int = 0

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        career = projection.get_current_career()
        if not self.attempt:
            projection.pending_inputs.append(
                advancement_pending(career, projection.summary.current_assignment, event.id)
            )
            return
        if career.commission is None:
            raise ReplayError(f'{career.name} does not support commission')
        dm = career.commission_dm(projection) + projection.pending_advancement_dm
        projection.pending_advancement_dm = 0
        if self.roll + dm < career.commission.target:
            projection.pending_inputs.append(
                advancement_pending(career, projection.summary.current_assignment, event.id)
            )
            return
        apply_forced_commission(projection, career, event.id)


class AdvancementDmChoiceHandler(EventHandlerBase):
    kind: Literal['advancement_dm_choice'] = 'advancement_dm_choice'

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        projection.pending_advancement_dm += 4
        if projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                advancement_pending(career, projection.summary.current_assignment, event.id)
            )


class PendingAdvancement(PendingInputBase):
    kind: Literal['advancement_pending'] = 'advancement_pending'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(fulfills=self.pending_id, handler=AdvancementHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]


class PendingCommissionChoice(PendingInputBase):
    kind: Literal['commission_choice'] = 'commission_choice'
    options: tuple[Literal['attempt'], Literal['skip']] = ('attempt', 'skip')

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        if form_str(form, 'choice', 'skip') == 'attempt':
            return Event(
                fulfills=self.pending_id,
                handler=CommissionHandler(attempt=True, roll=form_int(form, 'roll', 7)),
            )
        return Event(fulfills=self.pending_id, handler=CommissionHandler(attempt=False))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(
                name='choice',
                label='Commission',
                options=[('Attempt commission', 'attempt'), ('Skip (roll advancement)', 'skip')],
            ),
            NumberEntry(name='roll', label='Commission roll (2D, if attempting)', min=2, max=12),
        ]


class PendingRankBonusChoice(PendingInputBase):
    kind: Literal['rank_bonus_choice'] = 'rank_bonus_choice'
    level: int
    options: Sequence[CareerSkillOption | AdvancementDmOption] = Field(default_factory=list)
    continue_career_progress: bool = True

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        from ceres.character.domain.career.career_events import (
            AdvancementDmChoiceHandler,
            SkillChoiceHandler,
            _adv_dm_or_skill_adapter,
        )

        parsed = _adv_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return Event(fulfills=self.pending_id, handler=AdvancementDmChoiceHandler())
        if isinstance(parsed, Psi):
            return Event(
                fulfills=self.pending_id,
                handler=PsionicTalentTrainingHandler(talent=parsed.talent, roll=form_int(form, 'roll', 2)),
            )
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=cast(AnySkill, parsed)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        from ceres.character.domain.skill_events import build_skill_select_options

        specs: list[InputSpec] = [
            Select(
                name='skill',
                label='Choose a skill',
                options=build_skill_select_options(projection, self.options, self.level),
            )
        ]
        from ceres.character.domain.psionics import talent_acquisition_roll_required

        if talent_acquisition_roll_required(projection, self.options):
            specs.append(
                NumberEntry(
                    name='roll',
                    label='Psionic talent acquisition roll (2D, only for an untrained talent)',
                    min=2,
                    max=12,
                )
            )
        return specs

    def on_skill_chosen(self, projection: CharacterProjection, event: Event) -> None:
        projection.grant_skill(event.skill)
        self._continue(projection, event)

    def on_psi_chosen(self, projection: CharacterProjection, event: Event) -> None:
        self._continue(projection, event)

    def _continue(self, projection: CharacterProjection, event: Event) -> None:
        from ceres.character.domain.career.career_events import PendingSkillTable, queue_reenlist_or_aging

        if not self.continue_career_progress:
            return
        career = projection.get_current_career()
        tables = career.available_tables(
            projection.summary.characteristics.get(Chars.EDU, 0),
            projection.summary.current_assignment,
        )
        projection.pending_inputs.append(
            PendingSkillTable(pending_id=(event.id, 0), instruction='Choose a skill table and roll 1D', options=tables)
        )
        queue_reenlist_or_aging(projection, event.id, 1)


def rank_bonus_skill(bonus: RankBonus) -> AnySkill:
    from ceres.character.domain.skills import Level

    skill = bonus.skill
    if skill is None:
        raise ReplayError('rank_bonus_skill: bonus has no skill')
    skill_cls: Any = type(skill)  # dynamic dispatch; field name resolved at runtime
    fields = level_fields(skill_cls)
    if len(fields) == 1:
        return skill_cls(**{fields[0]: Level(value=bonus.level)})
    active_fields = [field for field in fields if getattr(skill, field).value > 0]
    if len(active_fields) != 1:
        raise ReplayError(f'Specialised rank bonus {skill_cls.name()} requires one chosen specialisation')
    return skill_cls(**{active_fields[0]: Level(value=bonus.level)})


def _apply_promotion(projection: CharacterProjection, career: CareerData, event_id: int) -> None:
    from ceres.character.domain.career.career_events import PendingSkillTable, queue_reenlist_or_aging

    new_rank = (projection.summary.rank or 0) + 1
    projection.summary.rank = new_rank
    career.update_current_term_rank(projection)
    if _apply_rank_bonus(projection, career, new_rank, event_id):
        return
    tables = career.available_tables(
        projection.summary.characteristics.get(Chars.EDU, 0),
        projection.summary.current_assignment,
    )
    projection.pending_inputs.append(
        PendingSkillTable(pending_id=(event_id, 0), instruction='Choose a skill table and roll 1D', options=tables)
    )
    queue_reenlist_or_aging(projection, event_id, 1)


def _apply_rank_bonus(projection: CharacterProjection, career: CareerData, rank: int, event_id: int) -> bool:
    entry = career.current_ranks(projection).get(rank)
    if not entry or not entry.bonus:
        return False
    bonus = entry.bonus
    if choices := bonus.resolve_choices():
        projection.pending_inputs.append(
            PendingRankBonusChoice(
                pending_id=(event_id, 0),
                level=bonus.level,
                instruction=f'Rank {rank} bonus: choose skill at level {bonus.level}',
                options=choices,
            )
        )
        return True
    if bonus.skill:
        projection.grant_skill(rank_bonus_skill(bonus))
    elif bonus.characteristic:
        projection.summary.characteristics[bonus.characteristic] = (
            projection.summary.characteristics.get(bonus.characteristic, 0) + bonus.level
        )
    return False


def apply_auto_advance(projection: CharacterProjection, career: CareerData, event_id: int) -> None:
    _apply_promotion(projection, career, event_id)


def apply_forced_commission(projection: CharacterProjection, career: CareerData, event_id: int) -> None:
    projection.summary.rank = 1
    if projection.summary.career_terms:
        projection.summary.career_terms[-1].commission = True
        projection.summary.career_terms[-1].rank = 1
    _apply_promotion_after_existing_rank(projection, career, event_id)


def _apply_promotion_after_existing_rank(projection: CharacterProjection, career: CareerData, event_id: int) -> None:
    from ceres.character.domain.career.career_events import PendingSkillTable, queue_reenlist_or_aging

    if _apply_rank_bonus(projection, career, 1, event_id):
        return
    tables = career.available_tables(
        projection.summary.characteristics.get(Chars.EDU, 0),
        projection.summary.current_assignment,
    )
    projection.pending_inputs.append(
        PendingSkillTable(pending_id=(event_id, 0), instruction='Choose a skill table and roll 1D', options=tables)
    )
    queue_reenlist_or_aging(projection, event_id, 1)


def advancement_pending(
    career: CareerData, assignment: AssignmentData | None, event_id: int, pending_idx: int = 0
) -> PendingAdvancement:
    if assignment is None:
        raise ReplayError('No current assignment')
    return PendingAdvancement(
        pending_id=(event_id, pending_idx),
        instruction=f'Advancement: {assignment.advancement.characteristic} {assignment.advancement.target}+',
    )


def career_progress_pending(
    projection: CharacterProjection,
    career: CareerData,
    event_id: int,
    pending_idx: int = 0,
) -> PendingAdvancement | PendingCommissionChoice:
    if career.can_attempt_commission(projection):
        if career.commission is None:
            raise ReplayError(f'{career.name} can attempt commission without commission rules')
        return PendingCommissionChoice(
            pending_id=(event_id, pending_idx),
            instruction=(
                f'Attempt commission ({career.commission.characteristic} {career.commission.target}+) '
                'or roll advancement?'
            ),
        )
    return advancement_pending(career, projection.summary.current_assignment, event_id, pending_idx)
