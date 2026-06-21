"""Career-phase event handlers for the new Event(handler=...) architecture.

All handlers here correspond to EventBase subclasses from events.py and implement
the EventHandlerBase interface.
"""

from collections.abc import Sequence
from typing import Annotated, Any, ClassVar, Literal, cast

from pydantic import Field, TypeAdapter

from ceres.character.domain.career.advancement import (
    AdvancementDmChoiceHandler,
    AdvancementHandler,
    CommissionHandler,
    PendingAdvancement,
    PendingCommissionChoice,
    PendingRankBonusChoice,
    advancement_pending,
    apply_auto_advance,
    apply_forced_commission,
    rank_bonus_skill,
)
from ceres.character.domain.career.career_data import (
    AdvancementDmOption,
    AssignmentData,
    CareerData,
    CareerSkillOption,
    SkillTableOption,
)
from ceres.character.domain.career.entry import (
    CareerEntryHandler,
    DraftAssignmentHandler,
    DraftHandler,
    PendingCareerChoice,
    PendingDraftAssignmentChoice,
    PendingDraftChoice,
    queue_career_choice,
    queue_career_choice_indexed,
)
from ceres.character.domain.career.muster_out import (
    BenefitChoiceHandler,
    MusterOutHandler,
    PendingBenefitChoice,
    PendingMusterOut,
    setup_muster_out,
)
from ceres.character.domain.career.prisoner_events import (
    ParoleRollHandler,
    PendingParoleRoll,
    apply_prisoner_advancement,
    set_forced_prison_career,
)
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, characteristic_dm
from ceres.character.domain.choice_events import ChoiceHandler, PendingChoices
from ceres.character.domain.connection_events import ConnectionsRollHandler, PendingConnectionsRoll
from ceres.character.domain.health.health_events import CharacteristicChoiceHandler
from ceres.character.domain.life_events import (
    BetrayalConvertHandler,
    ConnectionKindChoiceHandler,
    LifeEventCrimeLoseBenefitRoll,
    LifeEventCrimeTakePrisoner,
    LifeEventHandler,
    LifeEventUnusualHandler,
    PendingLifeEvent,
    PendingLifeEventAlienScience,
    PendingLifeEventBetrayalConvert,
    PendingLifeEventChoice,
    PendingLifeEventUnusual,
)
from ceres.character.domain.psionics import (
    PendingLifeEventPsionicsRoll,
    Psi,
    PsionicTalentTrainingHandler,
    talent_acquisition_roll_required,
)
from ceres.character.domain.skill_events import (
    PendingSkillChoice,
    SkillChoiceHandler,
    build_skill_select_options,
    skill_option_label,
)
from ceres.character.domain.skills import (
    AnySkill,
    level_fields,
)
from ceres.character.input_specs import (
    InputSpec,
    NumberEntry,
    Select,
    form_int,
    form_str,
    literal,
)
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import PendingInputBase

__all__ = [
    'AdvancementDmChoiceHandler',
    'AdvancementHandler',
    'BenefitChoiceHandler',
    'BetrayalConvertHandler',
    'CareerChoiceHandler',
    'CareerEntryHandler',
    'CharacteristicChoiceHandler',
    'CommissionHandler',
    'ConnectionKindChoiceHandler',
    'ConnectionsRollHandler',
    'DraftAssignmentHandler',
    'DraftHandler',
    'LifeEventCrimeLoseBenefitRoll',
    'LifeEventCrimeTakePrisoner',
    'LifeEventHandler',
    'LifeEventUnusualHandler',
    'MusterOutHandler',
    'ParoleRollHandler',
    'PendingAdvancement',
    'PendingBenefitChoice',
    'PendingCareerChoice',
    'PendingChoices',
    'PendingCommissionChoice',
    'PendingConnectionsRoll',
    'PendingDraftAssignmentChoice',
    'PendingDraftChoice',
    'PendingLifeEvent',
    'PendingLifeEventAlienScience',
    'PendingLifeEventBetrayalConvert',
    'PendingLifeEventChoice',
    'PendingLifeEventPsionicsRoll',
    'PendingLifeEventUnusual',
    'PendingMusterOut',
    'PendingParoleRoll',
    'PendingRankBonusChoice',
    'queue_career_choice',
    'queue_career_choice_indexed',
]

# ── Shared helpers ─────────────────────────────────────────────────────────────


def _skill_option_label(opt: Any) -> str:
    return skill_option_label(opt)


# ── Survive ────────────────────────────────────────────────────────────────────


class SurviveHandler(EventHandlerBase):
    kind: Literal['survive'] = 'survive'
    roll: int  # sum of 2D, before characteristic DM

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        if fulfilled_pending is not None:
            fulfilled_pending.resolve(projection, event)


# ── Mishap ─────────────────────────────────────────────────────────────────────


class MishapHandler(EventHandlerBase):
    kind: Literal['mishap'] = 'mishap'
    roll: int  # 1D result
    stay_in_career: bool = False

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.career_data import (
            DecreaseCharacteristicChoiceEffect,
            GainConnectionsRolledEffect,
            InjuryEffect,
            SkillChoiceEffect,
        )
        from ceres.character.domain.health.health_events import (
            PendingAgingRoll,
            PendingCharacteristicChoice,
            PendingInjuryTable,
        )

        career = projection.get_current_career()
        mishap = career.mishaps.get(self.roll)
        pending_idx = 0
        if mishap:
            projection.summary.problems.append(mishap.text)
            projection.summary.narrative.append(f'Mishap ({career.name}): {mishap.text}')
            for effect in mishap.effects:
                if isinstance(effect, DecreaseCharacteristicChoiceEffect):
                    characteristic = ', '.join(c.value for c in effect.options)
                    projection.pending_inputs.append(
                        PendingCharacteristicChoice(
                            pending_id=(event.id, pending_idx),
                            instruction=(f'Choose characteristic to decrease by {effect.amount}: {characteristic}'),
                            options=effect.options,
                            amount=effect.amount,
                        )
                    )
                    pending_idx += 1
                elif isinstance(effect, GainConnectionsRolledEffect):
                    projection.pending_inputs.append(
                        PendingConnectionsRoll(
                            pending_id=(event.id, pending_idx),
                            connection_type=effect.connection_type,
                            instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s',
                            options=effect.roll_options(),
                        )
                    )
                    pending_idx += 1
                elif isinstance(effect, SkillChoiceEffect):
                    projection.pending_inputs.append(
                        PendingSkillChoice(
                            pending_id=(event.id, pending_idx),
                            instruction=f'Choose one skill at level {effect.level}',
                            options=effect.options,
                            level=effect.level,
                        )
                    )
                    pending_idx += 1
                elif isinstance(effect, InjuryEffect):
                    if effect.severity == 'normal':
                        projection.pending_inputs.append(
                            PendingCharacteristicChoice(
                                pending_id=(event.id, pending_idx),
                                instruction='Injured: choose STR, DEX, or END to reduce by 1',
                                options=[Chars.STR, Chars.DEX, Chars.END],
                                amount=1,
                            )
                        )
                        pending_idx += 1
                    elif effect.severity == 'severe':
                        projection.pending_inputs.append(
                            PendingCharacteristicChoice(
                                pending_id=(event.id, pending_idx),
                                instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                                options=[Chars.STR, Chars.DEX, Chars.END],
                                amount=2,
                            )
                        )
                        pending_idx += 1
                    elif effect.severity == 'from_table':
                        projection.pending_inputs.append(
                            PendingInjuryTable(
                                pending_id=(event.id, pending_idx),
                                instruction='Roll 1D on Injury table',
                            )
                        )
                        pending_idx += 1
                else:
                    from ceres.character.domain.career.career_data import CareerHandlerBase

                    if isinstance(effect, CareerHandlerBase):
                        pending_idx = effect.handle(projection, event.id, pending_idx)
                    else:
                        effect.apply(projection, source=mishap.text, source_event_id=event.id)
        defer = mishap is not None and mishap.defer_ejection
        if defer:
            pass
        elif self.stay_in_career or (mishap is not None and mishap.stay_in_career):
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment, event.id, pending_idx)
            )
        else:
            if mishap and projection.summary.career_terms:
                projection.summary.career_terms[-1].mishap = mishap.text
            purge_career_pendings(projection)
            if projection.summary.career_terms:
                projection.summary.career_terms[-1].require_muster_out().lost_rolls += 1
            projection.summary.age += 4
            if projection.summary.age >= 34:
                projection.clear_current_career(ejected=True)
                projection.summary.career_terms[-1].require_muster_out().pending_setup = True
                projection.pending_inputs.append(
                    PendingAgingRoll(pending_id=(event.id, pending_idx), instruction='Roll 2D on Aging table')
                )
            else:
                muster_out_setup(projection, event.id, pending_idx, ejected=True)


# ── Term Event ─────────────────────────────────────────────────────────────────


class TermEventHandler(EventHandlerBase):
    kind: Literal['term_event'] = 'term_event'
    roll: int  # sum of 2D

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.career_data import (
            AutoAdvanceEffect,
            GainConnectionsRolledEffect,
            LifeEventEffect,
            RollMishapEffect,
            SkillChoiceEffect,
        )

        career = projection.get_current_career()
        term_event = career.events.get(self.roll)
        skill_choice_effect = None
        roll_mishap_effect = None
        auto_advance = False
        life_event_pending = False
        pending_idx = 0
        career_handler_invoked = False
        if term_event:
            projection.summary.narrative.append(
                f'Term {projection.summary.terms_started_in_current_career} event ({career.name}): {term_event.text}'
            )
            if projection.summary.career_terms:
                projection.summary.career_terms[-1].event = term_event.text
            for effect in term_event.effects:
                if isinstance(effect, SkillChoiceEffect):
                    skill_choice_effect = effect
                elif isinstance(effect, RollMishapEffect):
                    roll_mishap_effect = effect
                elif isinstance(effect, AutoAdvanceEffect):
                    auto_advance = True
                elif isinstance(effect, LifeEventEffect):
                    life_event_pending = True
                elif isinstance(effect, GainConnectionsRolledEffect):
                    projection.pending_inputs.append(
                        PendingConnectionsRoll(
                            pending_id=(event.id, pending_idx),
                            connection_type=effect.connection_type,
                            instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s',
                            options=effect.roll_options(),
                        )
                    )
                    pending_idx += 1
                else:
                    from ceres.character.domain.career.career_data import CareerHandlerBase

                    if isinstance(effect, CareerHandlerBase):
                        pending_idx = effect.handle(projection, event.id, pending_idx)
                        career_handler_invoked = True
                    else:
                        effect.apply(projection, source=term_event.text, source_event_id=event.id)
        if roll_mishap_effect is not None:
            instruction = (
                'Roll 1D on Mishap table (you are not ejected from this career)'
                if not roll_mishap_effect.leave
                else 'Roll 1D on Mishap table'
            )
            projection.pending_inputs.append(
                PendingMishap(
                    pending_id=(event.id, pending_idx),
                    instruction=instruction,
                    stay_in_career=not roll_mishap_effect.leave,
                )
            )
        elif auto_advance:
            _apply_auto_advance(projection, career, event.id)
        elif life_event_pending:
            projection.pending_inputs.append(
                PendingLifeEvent(pending_id=(event.id, pending_idx), instruction='Roll 2D on Life Events table')
            )
        elif skill_choice_effect is not None:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, pending_idx),
                    instruction=f'Choose one skill at level {skill_choice_effect.level}',
                    options=skill_choice_effect.options,
                    level=skill_choice_effect.level,
                )
            )
        elif not career_handler_invoked:
            projection.pending_inputs.append(career_progress_pending(projection, career, event.id, pending_idx))


# Compatibility name retained while consumers migrate to ChoiceHandler.
CareerChoiceHandler = ChoiceHandler


# ── Reenlist ───────────────────────────────────────────────────────────────────


class ReenlistHandler(EventHandlerBase):
    kind: Literal['reenlist_event'] = 'reenlist_event'
    reenlist: bool

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        if self.reenlist:
            career = projection.get_current_career()
            _start_new_career_term(projection, career, event.id)
        else:
            purge_career_pendings(projection)
            muster_out_setup(projection, event.id, 0)


# ── Skill Table ────────────────────────────────────────────────────────────────


class SkillTableHandler(EventHandlerBase):
    kind: Literal['skill_table'] = 'skill_table'
    table: str
    roll: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.career_data import AdvancementDmOption
        from ceres.character.domain.characteristics import Chars as _Chars
        from ceres.character.domain.health.health_events import PendingAgingRoll

        if projection.summary.current_career is not None:
            career = projection.get_current_career()
        elif projection.summary.career_terms and projection.summary.career_terms[-1].muster_out is not None:
            career = projection.summary.career_terms[-1].career
        else:
            raise ReplayError('No active career')
        table = career.skill_table(self.table)
        if table is None:
            raise ReplayError(f'Unknown skill table: {self.table!r}')
        if table.min_edu is not None:
            edu = projection.summary.characteristics.get(Chars.EDU, 0)
            if edu < table.min_edu:
                raise ReplayError(f'Table {self.table!r} requires EDU {table.min_edu}+, character has {edu}')
        if not (1 <= self.roll <= 6):
            raise ReplayError(f'Skill table roll must be 1-6, got {self.roll}')
        entry = table.entries[self.roll - 1]
        assignment_index = projection.summary.current_assignment
        choices: list[CareerSkillOption] | None = None
        if isinstance(entry, list):
            choices = [
                option
                for option in cast(list[CareerSkillOption], list(entry))
                if career.skill_table_option_is_available(projection, self.table, option)
            ]
        elif isinstance(entry, Psi):
            choices = [entry] if career.skill_table_option_is_available(projection, self.table, entry) else []
        elif not isinstance(entry, _Chars):
            skill_cls = type(entry)
            fields = level_fields(skill_cls)
            spec_field = next((f for f in fields if getattr(entry, f).value > 0), None)
            if spec_field is None and len(fields) > 1:
                choices = [skill_cls()]
        reenlist_queued = any(
            isinstance(p, (PendingReenlist, PendingAssignmentChangeChoice, PendingAgingRoll, PendingMusterOut))
            for p in projection.pending_inputs
        )
        if choices:
            new_pending = PendingSkillTableChoice(
                pending_id=(event.id, 0),
                instruction=f'Choose one skill: {", ".join(_skill_option_label(s) for s in choices)}',
                options=cast(list[CareerSkillOption | AdvancementDmOption], choices),
                reenlist_queued=reenlist_queued,
            )
            if reenlist_queued:
                idx = next(
                    (
                        i
                        for i, p in enumerate(projection.pending_inputs)
                        if isinstance(
                            p,
                            (PendingReenlist, PendingAssignmentChangeChoice, PendingAgingRoll, PendingMusterOut),
                        )
                    ),
                    len(projection.pending_inputs),
                )
                projection.pending_inputs.insert(idx, new_pending)
            else:
                projection.pending_inputs.append(new_pending)
        elif not isinstance(entry, (list, Psi)):
            _apply_skill_table_entry(projection, entry)
            if not reenlist_queued:
                projection.pending_inputs.append(_survive_pending(career, assignment_index, event.id))
        elif not reenlist_queued:
            projection.pending_inputs.append(_survive_pending(career, assignment_index, event.id))


# ── Skill Roll ─────────────────────────────────────────────────────────────────


class SkillRollHandler(EventHandlerBase):
    kind: Literal['skill_roll'] = 'skill_roll'
    skill: AnySkill | Chars
    modified_roll: int

    model_config = {'arbitrary_types_allowed': True}

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        blocking_count_before = sum(1 for p in projection.pending_inputs if p.blocking)
        if fulfilled_pending is not None:
            fulfilled_pending.resolve(projection, event)
        if (
            sum(1 for p in projection.pending_inputs if p.blocking) == blocking_count_before
            and projection.summary.current_career is not None
            and not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        ):
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment, event.id)
            )


# ── Assignment Change Choice ───────────────────────────────────────────────────


class AssignmentChangeChoiceHandler(EventHandlerBase):
    kind: Literal['assignment_change_choice'] = 'assignment_change_choice'
    choice: Literal['same', 'switch', 'muster_out']

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        if self.choice == 'same':
            _start_new_career_term(projection, career, event.id)
        elif self.choice == 'muster_out':
            purge_career_pendings(projection)
            muster_out_setup(projection, event.id, 0)
        else:
            current_assignment = projection.summary.current_assignment
            others = [a for a in career.assignments if a != current_assignment]
            projection.pending_inputs.append(
                PendingSwitchAssignment(
                    pending_id=(event.id, 0),
                    instruction=f'Switch assignment in {career.name}',
                    options=others,
                )
            )


# ── Switch Assignment ──────────────────────────────────────────────────────────


class SwitchAssignmentHandler(EventHandlerBase):
    kind: Literal['switch_assignment'] = 'switch_assignment'
    assignment: AssignmentData
    qualification_roll: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        char = career.qualification.characteristic
        target = career.qualification.target
        dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
        if self.qualification_roll + dm >= target:
            purge_career_pendings(projection)
            career.start_new_term(projection, self.assignment, event.id, is_continuation=True)
        else:
            projection.pending_inputs.append(
                PendingReenlist(
                    pending_id=(event.id, 0),
                    instruction=(
                        f'Assignment change to {self.assignment.name!r} failed — reenlist with '
                        f'{projection.summary.current_assignment.name!r} or muster out?'
                    ),
                )
            )


# ── Injury/Nearly Killed ───────────────────────────────────────────────────────

# ── Choices Pending ────────────────────────────────────────────────────────────

# ── Skill Table Choice / Rank Bonus / Initial Training ────────────────────────

# ── InjuryTableHandler import from health for re-use ──────────────────────────

# Import InjuryTableHandler from health module to register it and make it available

# ── TypeAdapters for skill serialization ──────────────────────────────────────

_skill_adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)
_adv_dm_or_skill_adapter: TypeAdapter[AdvancementDmOption | Psi | AnySkill] = TypeAdapter(
    Annotated[AdvancementDmOption | Psi | AnySkill, Field(union_mode='left_to_right')]
)

# ── Skill-choice option builder ───────────────────────────────────────────────


def _build_skill_select_options(
    projection: CharacterProjection,
    options: Sequence[CareerSkillOption | AdvancementDmOption],
    level: int | None,
) -> list[tuple[str, str]]:
    return build_skill_select_options(projection, options, level)


# ── Career helper functions ───────────────────────────────────────────────────


def _rank_bonus_skill(bonus: Any) -> AnySkill:
    return rank_bonus_skill(bonus)


def _apply_auto_advance(projection: Any, career: Any, event_id: int) -> None:
    apply_auto_advance(projection, career, event_id)


def _apply_forced_commission(projection: Any, career: Any, event_id: int) -> None:
    apply_forced_commission(projection, career, event_id)


def _start_new_career_term(projection: Any, career: Any, event_id: int) -> None:
    purge_career_pendings(projection)
    assignment = projection.summary.current_assignment
    if assignment is None:
        raise ReplayError(f'No current assignment in career {career.name!r}')
    career.start_new_term(projection, assignment, event_id, is_continuation=True)


def _survive_pending(career: Any, assignment: Any, event_id: int) -> Any:
    if assignment is None:
        raise ReplayError(f'No current assignment in career {career.name!r}')
    return career.survival_pending(assignment, event_id)


def _advancement_pending(career: Any, assignment: Any, event_id: int, pending_idx: int = 0) -> Any:
    return advancement_pending(career, assignment, event_id, pending_idx)


def _apply_skill_table_entry(projection: Any, entry: Any) -> None:
    from ceres.character.domain.characteristics import Chars as _Chars

    if isinstance(entry, _Chars):
        projection.summary.characteristics[entry] = projection.summary.characteristics.get(entry, 0) + 1
    elif isinstance(entry, Psi):
        raise ReplayError('Psionic talent table entries require a training check')
    else:
        projection.increment_skill(entry)


def _set_forced_prison_career(projection: Any, description: str) -> None:
    set_forced_prison_career(projection, description)


def _apply_prisoner_advancement(projection: Any, event: Any, career: Any) -> None:
    apply_prisoner_advancement(projection, event, career)


def _apply_mishap_ejection(
    projection: Any,
    source_event_id: int,
    pending_idx: int,
    lose_current_term: bool = True,
) -> int:
    from ceres.character.domain.health.health_events import PendingAgingRoll

    if lose_current_term and projection.summary.career_terms:
        projection.summary.career_terms[-1].require_muster_out().lost_rolls += 1
    projection.summary.age += 4
    if projection.summary.age >= 34:
        projection.clear_current_career(ejected=True)
        projection.summary.career_terms[-1].require_muster_out().pending_setup = True
        projection.pending_inputs.append(
            PendingAgingRoll(pending_id=(source_event_id, pending_idx), instruction='Roll 2D on Aging table')
        )
        return pending_idx + 1
    return muster_out_setup(projection, source_event_id, pending_idx, ejected=True)


def purge_career_pendings(projection: CharacterProjection) -> None:
    projection.pending_inputs[:] = [
        p for p in projection.pending_inputs if not isinstance(p, _CAREER_PHASE_PENDING_TYPES)
    ]


def queue_reenlist_or_aging(projection: CharacterProjection, event_id: int, idx: int) -> None:
    from ceres.character.domain.health.health_events import PendingAgingRoll

    if projection.prisoner_freed:
        projection.prisoner_freed = False
        projection.summary.age += 4
        career = projection.summary.current_career
        if projection.summary.age >= 34:
            projection.clear_current_career()
            if projection.summary.career_terms:
                projection.summary.career_terms[-1].require_muster_out().pending_setup = True
            projection.pending_reenlist = False
            projection.pending_inputs.append(
                PendingAgingRoll(pending_id=(event_id, idx), instruction='Roll 2D on Aging table')
            )
        elif career:
            muster_out_setup(projection, event_id, idx)
        return

    projection.summary.age += 4
    if projection.forced_leave:
        projection.forced_leave = False
        career = projection.get_current_career() if projection.summary.current_career else None
        if career:
            if projection.summary.age >= 34:
                projection.clear_current_career()
                projection.summary.career_terms[-1].require_muster_out().pending_setup = True
                projection.pending_reenlist = False
                projection.pending_inputs.append(
                    PendingAgingRoll(pending_id=(event_id, idx), instruction='Roll 2D on Aging table')
                )
            else:
                muster_out_setup(projection, event_id, idx)
        return
    if projection.summary.age >= 34:
        projection.pending_inputs.append(
            PendingAgingRoll(pending_id=(event_id, idx), instruction='Roll 2D on Aging table')
        )
    else:
        career = projection.get_current_career() if projection.summary.current_career else None
        if career and career.allows_assignment_change and len(career.assignments) > 1:
            can_muster_out = not career.advancement_is_special() and not projection.forced_stay
            projection.forced_stay = False
            projection.pending_inputs.append(
                PendingAssignmentChangeChoice(
                    pending_id=(event_id, idx),
                    muster_out=can_muster_out,
                    instruction='Stay, switch assignment, or muster out?'
                    if can_muster_out
                    else 'Stay or switch assignment?',
                )
            )
        else:
            can_muster_out = not projection.forced_stay
            projection.forced_stay = False
            projection.pending_inputs.append(
                PendingReenlist(
                    pending_id=(event_id, idx),
                    can_muster_out=can_muster_out,
                )
            )


def muster_out_setup(
    projection: Any,
    source_event_id: int,
    pending_idx: int = 0,
    clear_career: bool = True,
    ejected: bool = False,
) -> int:
    return setup_muster_out(projection, source_event_id, pending_idx, clear_career=clear_career, ejected=ejected)


def career_progress_pending(
    projection: Any, career: CareerData, event_id: int, pending_idx: int = 0
) -> PendingAdvancement | PendingCommissionChoice:
    from ceres.character.domain.career.advancement import career_progress_pending as build_pending

    return build_pending(projection, career, event_id, pending_idx)


# ── Career Pending Input Types ────────────────────────────────────────────────


class PendingSurvive(PendingInputBase):
    kind: Literal['survive'] = 'survive'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=SurviveHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]

    def resolve(self, projection: Any, event: Any) -> None:
        assignment = projection.summary.current_assignment
        if assignment is None:
            raise ReplayError('No current assignment')
        char = assignment.survival.characteristic
        target = assignment.survival.target
        dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
        success = event.roll != 2 and (event.roll + dm) >= target
        if success:
            projection.pending_inputs.append(
                PendingTermEvent(pending_id=(event.id, 0), instruction='Roll 2D on Events table')
            )
        else:
            if event.roll == 2:
                projection.summary.narrative.append(
                    f'Automatic mishap (rolled natural 2) in term {projection.summary.terms_started_in_current_career}'
                )
            projection.pending_inputs.append(
                PendingMishap(pending_id=(event.id, 0), instruction='Roll 1D on Mishap table')
            )


class PendingTermEvent(PendingInputBase):
    kind: Literal['term_event'] = 'term_event'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=TermEventHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]


class PendingMishap(PendingInputBase):
    kind: Literal['mishap'] = 'mishap'
    stay_in_career: bool = False

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=MishapHandler(roll=form_int(form, 'roll', 1), stay_in_career=self.stay_in_career),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6)]


class PendingSkillTable(PendingInputBase):
    kind: Literal['skill_table'] = 'skill_table'
    options: list[SkillTableOption] = Field(default_factory=list)

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=SkillTableHandler(table=form_str(form, 'table'), roll=form_int(form, 'roll', 1)),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        table_options = [(opt.label, opt.key) for opt in self.options]
        return [
            Select(name='table', label='Table', options=table_options),
            NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6),
        ]


class PendingReenlist(PendingInputBase):
    kind: Literal['reenlist_pending'] = 'reenlist_pending'
    instruction: str = 'Reenlist or muster out?'
    can_muster_out: bool = True

    @property
    def template_fragment(self) -> str:
        return 'reenlist'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        reenlist = form_str(form, 'reenlist', 'false').lower() in ('true', '1', 'yes')
        return Event(fulfills=self.pending_id, handler=ReenlistHandler(reenlist=reenlist))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return []


class PendingAssignmentChangeChoice(PendingInputBase):
    kind: Literal['assignment_change_choice'] = 'assignment_change_choice'
    muster_out: bool

    _LABELS: ClassVar[dict[str, str]] = {
        'same': 'Stay in current assignment',
        'switch': 'Switch assignment',
        'muster_out': 'Muster out',
    }

    def _choices(self) -> list[str]:
        return ['same', 'switch', 'muster_out'] if self.muster_out else ['same', 'switch']

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        raw = literal(form_str(form, 'choice', 'same'), tuple(self._choices()), 'same')
        choice = cast(Literal['same', 'switch', 'muster_out'], raw)
        return Event(
            fulfills=self.pending_id,
            handler=AssignmentChangeChoiceHandler(choice=choice),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(self._LABELS[c], c) for c in self._choices()]
        return [Select(name='choice', label='Assignment choice', options=options)]


class PendingSwitchAssignment(PendingInputBase):
    kind: Literal['switch_assignment'] = 'switch_assignment'
    options: list[AssignmentData] = Field(default_factory=list)

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        name = form_str(form, 'assignment', self.options[0].name if self.options else '')
        assignment = next((a for a in self.options if a.name == name), None)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {name!r}')
        roll = form_int(form, 'roll', 2)
        return Event(
            fulfills=self.pending_id,
            handler=SwitchAssignmentHandler(assignment=assignment, qualification_roll=roll),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(name='assignment', label='New assignment', options=[(a.name, a.name) for a in self.options]),
            NumberEntry(name='roll', label='Qualification roll (2D)', min=2, max=12),
        ]


class PendingInitialTrainingChoice(PendingInputBase):
    kind: Literal['initial_training_choice'] = 'initial_training_choice'
    options: Sequence[CareerSkillOption | AdvancementDmOption] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

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
        options = _build_skill_select_options(projection, self.options, 0)
        specs: list[InputSpec] = [Select(name='skill', label='Choose a skill', options=options)]
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

    def on_skill_chosen(self, projection: Any, event: Any) -> None:
        projection.grant_skill(event.skill)
        remaining = [p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice)]
        if not remaining and projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(_survive_pending(career, projection.summary.current_assignment, event.id))

    def on_psi_chosen(self, projection: Any, event: Any) -> None:
        self._complete_training(projection, event)

    def _complete_training(self, projection: Any, event: Any) -> None:
        remaining = [p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice)]
        if not remaining and projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(_survive_pending(career, projection.summary.current_assignment, event.id))


class PendingSkillTableChoice(PendingInputBase):
    kind: Literal['skill_table_choice'] = 'skill_table_choice'
    reenlist_queued: bool = False
    options: Sequence[CareerSkillOption | AdvancementDmOption] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

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
        options = _build_skill_select_options(projection, self.options, None)
        specs: list[InputSpec] = [Select(name='skill', label='Choose a skill', options=options)]
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

    def on_skill_chosen(self, projection: Any, event: Any) -> None:
        projection.grant_skill(event.skill)
        if projection.summary.current_career is not None and not self.reenlist_queued:
            career = projection.get_current_career()
            projection.pending_inputs.append(_survive_pending(career, projection.summary.current_assignment, event.id))

    def on_psi_chosen(self, projection: Any, event: Any) -> None:
        if projection.summary.current_career is not None and not self.reenlist_queued:
            career = projection.get_current_career()
            projection.pending_inputs.append(_survive_pending(career, projection.summary.current_assignment, event.id))


_CAREER_PHASE_PENDING_TYPES = (
    PendingSurvive,
    PendingTermEvent,
    PendingMishap,
    PendingAdvancement,
    PendingCommissionChoice,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingAssignmentChangeChoice,
    PendingSwitchAssignment,
)
