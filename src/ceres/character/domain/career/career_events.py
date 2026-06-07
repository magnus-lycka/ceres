"""Career-phase event handlers for the new Event(handler=...) architecture.

All handlers here correspond to EventBase subclasses from events.py and implement
the EventHandlerBase interface.
"""

from collections.abc import Sequence
from typing import Annotated, Any, ClassVar, Literal, cast

from pydantic import Field, SerializeAsAny, TypeAdapter

from ceres.character.domain.benefits import AnyBenefit
from ceres.character.domain.career.career_data import AdvancementDmOption, AssignmentData, CareerData, SkillTableOption
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind, characteristic_dm
from ceres.character.domain.skills import (
    AnySkill,
    Level,
    SpaceScience,
    _level_fields,
)
from ceres.character.input_specs import InputSpec, NumberEntry, Reference, Select, form_int, form_str, literal
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import ChoiceBase, PendingInputBase

# ── Shared helpers ─────────────────────────────────────────────────────────────


def _skill_option_label(opt: Any) -> str:
    from ceres.character.domain.career.career_data import AdvancementDmOption

    if isinstance(opt, AdvancementDmOption):
        return opt.label()
    skill_cls = type(opt)
    fields = _level_fields(skill_cls)
    if len(fields) > 1:
        active = next((f for f in fields if getattr(opt, f).value > 0), None)
        if active is not None:
            extra = skill_cls.model_fields[active].json_schema_extra or {}
            spec_label = str(extra.get('name') or active.replace('_', ' ').title())
            return f'{skill_cls.name()} ({spec_label})'
    return skill_cls.name()


# ── Career Entry ───────────────────────────────────────────────────────────────


class CareerEntryHandler(EventHandlerBase):
    kind: Literal['career_event'] = 'career_event'
    career: str
    assignment: str
    qualification_roll: int  # 2D result before characteristic DM

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.loader import load_careers

        careers = load_careers()
        career = careers.get(self.career)
        if career is None:
            raise ReplayError(f'Unknown career: {self.career!r}')
        assignment = career.assignment(self.assignment)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {self.assignment!r} for career {self.career!r}')
        career.start_career(projection, assignment, event.id, self.qualification_roll)


class DraftHandler(EventHandlerBase):
    kind: Literal['draft_event'] = 'draft_event'
    career: str
    assignment: str | None = None

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.loader import load_careers

        if projection.summary.drafted:
            raise ReplayError('A character may only enter the draft once')
        career = load_careers().get(self.career)
        if career is None:
            raise ReplayError(f'Unknown career: {self.career!r}')
        career.start_draft(projection, event.id, self.assignment)


class DraftAssignmentHandler(EventHandlerBase):
    kind: Literal['draft_assignment'] = 'draft_assignment'
    career: str
    assignment: str

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.loader import load_careers

        career = load_careers().get(self.career)
        if career is None:
            raise ReplayError(f'Unknown career: {self.career!r}')
        career.start_draft(projection, event.id, self.assignment)


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
                    projection.pending_inputs.append(
                        PendingCharacteristicChoice(
                            pending_id=(event.id, pending_idx),
                            instruction=(
                                f'Choose characteristic to decrease by {effect.amount}: {", ".join(c.value for c in effect.options)}'
                            ),
                            options=effect.options,
                        )
                    )
                    pending_idx += 1
                elif isinstance(effect, GainConnectionsRolledEffect):
                    projection.pending_inputs.append(
                        PendingConnectionsRoll(
                            pending_id=(event.id, pending_idx),
                            connection_type=effect.connection_type,
                            instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s',
                            options=list(range(1, 7)),
                        )
                    )
                    pending_idx += 1
                elif isinstance(effect, SkillChoiceEffect):
                    projection.pending_inputs.append(
                        PendingSkillChoice(
                            pending_id=(event.id, pending_idx),
                            instruction=f'Choose one skill: {", ".join(_skill_option_label(o) for o in effect.options)}',
                            options=effect.options,
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
                            )
                        )
                        pending_idx += 1
                    elif effect.severity == 'severe':
                        projection.pending_inputs.append(
                            PendingCharacteristicChoice(
                                pending_id=(event.id, pending_idx),
                                instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                                options=[Chars.STR, Chars.DEX, Chars.END],
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
            projection.summary.age += 4
            if projection.summary.age >= 34:
                projection.muster_out_career = career
                projection.clear_current_career(ejected=True)
                projection.pending_inputs.append(
                    PendingAgingRoll(pending_id=(event.id, pending_idx), instruction='Roll 2D on Aging table')
                )
            else:
                muster_out_setup(projection, career, event.id, pending_idx, lose_current_term=True, ejected=True)


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
                    max_count = {'d3': 3, '1d3': 3, 'd6': 6, '1d6': 6}.get(effect.dice.lower(), 6)
                    projection.pending_inputs.append(
                        PendingConnectionsRoll(
                            pending_id=(event.id, pending_idx),
                            connection_type=effect.connection_type,
                            instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s',
                            options=list(range(1, max_count + 1)),
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
            projection.pending_inputs.append(PendingMishap(pending_id=(event.id, pending_idx), instruction=instruction))
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
                    instruction=f'Choose one skill: {", ".join(_skill_option_label(o) for o in skill_choice_effect.options)}',
                    options=skill_choice_effect.options,
                )
            )
        elif not career_handler_invoked:
            projection.pending_inputs.append(career_progress_pending(projection, career, event.id, pending_idx))


# ── Skill Choice ───────────────────────────────────────────────────────────────


class SkillChoiceHandler(EventHandlerBase):
    kind: Literal['skill_choice'] = 'skill_choice'
    skill: AnySkill

    model_config = {'arbitrary_types_allowed': True}

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        if fulfilled_pending is not None and hasattr(fulfilled_pending, 'on_skill_chosen'):
            fulfilled_pending.on_skill_chosen(projection, event)
        else:
            projection.grant_skill(self.skill)
            if projection.summary.current_career is not None:
                career = projection.get_current_career()
                projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


# ── Advancement DM Choice ──────────────────────────────────────────────────────


class AdvancementDmChoiceHandler(EventHandlerBase):
    kind: Literal['advancement_dm_choice'] = 'advancement_dm_choice'

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        projection.pending_advancement_dm += 4
        if projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment, event.id)
            )


# ── Connection Kind Choice ─────────────────────────────────────────────────────


class ConnectionKindChoiceHandler(EventHandlerBase):
    kind: Literal['connection_kind_choice'] = 'connection_kind_choice'
    connection_kind: ConnectionKind

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.connection import make_connection

        source = (
            f'Life event roll {fulfilled_pending.roll}'
            if isinstance(fulfilled_pending, PendingLifeEventChoice)
            else 'unknown'
        )
        projection.summary.connections.append(make_connection(self.connection_kind, source=f'Life event: {source}'))
        _CHOICE_NARRATIVE = {
            4: {
                ConnectionKind.RIVAL: 'Life event: relationship ended, gained a rival',
                ConnectionKind.ENEMY: 'Life event: relationship ended, gained an enemy',
            },
            8: {
                ConnectionKind.RIVAL: 'Life event: betrayal, gained a rival',
                ConnectionKind.ENEMY: 'Life event: betrayal, gained an enemy',
            },
        }
        if isinstance(fulfilled_pending, PendingLifeEventChoice):
            kind_map = _CHOICE_NARRATIVE.get(fulfilled_pending.roll)
            if kind_map:
                entry = kind_map.get(self.connection_kind)
                if entry:
                    projection.summary.narrative.append(entry)


# ── Career Choice (ChoiceBase dispatch) ────────────────────────────────────────


class CareerChoiceHandler(EventHandlerBase):
    """Career-specific choice; dispatches to the selected ChoiceBase.handle()."""

    kind: Literal['career_decision'] = 'career_decision'
    choice: str

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        if fulfilled_pending is None:
            raise ReplayError('CareerChoiceEvent has no matching pending input')
        if not isinstance(fulfilled_pending, PendingChoices):
            raise ReplayError(
                f'CareerChoiceEvent fulfilled by unexpected pending type {type(fulfilled_pending).__name__!r}'
            )
        selected = next((c for c in fulfilled_pending.choices if c.kind == self.choice), None)
        if selected is None:
            raise ReplayError(f'Unknown choice {self.choice!r}')
        selected.handle(projection, event)


# ── Advancement ────────────────────────────────────────────────────────────────


class AdvancementHandler(EventHandlerBase):
    kind: Literal['advancement_event'] = 'advancement_event'
    roll: int  # sum of 2D, before characteristic DM

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        if career.advancement_is_special():
            _apply_prisoner_advancement(projection, event, career)
            return
        assignment = projection.summary.current_assignment
        if assignment is None:
            raise ReplayError('No current assignment')
        char = assignment.advancement.characteristic
        target = assignment.advancement.target
        dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
        dm += projection.pending_advancement_dm
        projection.pending_advancement_dm = 0
        success = (self.roll + dm) >= target
        terms_in_career = len(career.prior_terms(projection.summary.career_terms, assignment))
        if self.roll == 12:
            projection.forced_stay = True
        elif self.roll <= terms_in_career:
            projection.forced_leave = True
        if success:
            new_rank = (projection.summary.rank or 0) + 1
            projection.summary.rank = new_rank
            career.update_current_term_rank(projection)
            rank_entry = career.current_ranks(projection).get(new_rank)
            if rank_entry and rank_entry.bonus:
                bonus = rank_entry.bonus
                choices = bonus.resolve_choices()
                if choices:
                    projection.pending_inputs.append(
                        PendingRankBonusChoice(
                            pending_id=(event.id, 0),
                            level=bonus.level,
                            instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                            options=choices,
                        )
                    )
                    return
                if bonus.skill:
                    projection.grant_skill(_rank_bonus_skill(bonus))
                elif bonus.characteristic:
                    char = bonus.characteristic
                    projection.summary.characteristics[char] = (
                        projection.summary.characteristics.get(char, 0) + bonus.level
                    )
            edu = projection.summary.characteristics.get(Chars.EDU, 0)
            tables = career.available_tables(edu, projection.summary.current_assignment)
            projection.pending_inputs.append(
                PendingSkillTable(
                    pending_id=(event.id, 0), instruction='Choose a skill table and roll 1D', options=tables
                )
            )
            queue_reenlist_or_aging(projection, event.id, 1)
            return
        queue_reenlist_or_aging(projection, event.id, 0)


# ── Commission ─────────────────────────────────────────────────────────────────


class CommissionHandler(EventHandlerBase):
    kind: Literal['commission'] = 'commission'
    attempt: bool
    roll: int = 0

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        if not self.attempt:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment, event.id)
            )
            return
        if career.commission is None:
            raise ReplayError(f'{career.name} does not support commission')
        dm = career.commission_dm(projection)
        dm += projection.pending_advancement_dm
        projection.pending_advancement_dm = 0
        if self.roll + dm < career.commission.target:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment, event.id)
            )
            return
        projection.summary.rank = 1
        if projection.summary.career_terms:
            projection.summary.career_terms[-1].commission = True
            projection.summary.career_terms[-1].rank_after_term = 1
        rank_entry = career.current_ranks(projection).get(1)
        if rank_entry and rank_entry.bonus:
            bonus = rank_entry.bonus
            choices = bonus.resolve_choices()
            if choices:
                projection.pending_inputs.append(
                    PendingRankBonusChoice(
                        pending_id=(event.id, 0),
                        level=bonus.level,
                        instruction=f'Rank 1 bonus: choose skill at level {bonus.level}',
                        options=choices,
                    )
                )
                return
            if bonus.skill:
                projection.grant_skill(_rank_bonus_skill(bonus))
            elif bonus.characteristic:
                char = bonus.characteristic
                projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = career.available_tables(edu, projection.summary.current_assignment)
        projection.pending_inputs.append(
            PendingSkillTable(pending_id=(event.id, 0), instruction='Choose a skill table and roll 1D', options=tables)
        )
        queue_reenlist_or_aging(projection, event.id, 1)


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
            career = projection.get_current_career()
            muster_out_setup(projection, career, event.id, 0, lose_current_term=False)


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
        elif projection.muster_out_career is not None:
            career = projection.muster_out_career
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
        choices: list[AnySkill] | None = None
        if isinstance(entry, list):
            choices = cast(list[AnySkill], list(entry))
        elif not isinstance(entry, _Chars):
            skill_cls = type(entry)
            fields = _level_fields(skill_cls)
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
                instruction=f'Choose one skill: {", ".join(type(s).name() for s in choices)}',
                options=cast(list[AnySkill | AdvancementDmOption], choices),
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
        else:
            _apply_skill_table_entry(projection, entry)
            if not reenlist_queued:
                projection.pending_inputs.append(_survive_pending(career, assignment_index, event.id))


# ── Characteristic Choice ──────────────────────────────────────────────────────


class CharacteristicChoiceHandler(EventHandlerBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'
    characteristic: Chars
    amount: int = 1

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.health.health_events import (
            PendingAgingChoice,
            PendingAgingChoiceMental,
            PendingNearlyKilled,
            check_aging_crisis,
            complete_aging,
        )

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
                p for p in projection.pending_inputs if isinstance(p, (PendingAgingChoice, PendingAgingChoiceMental))
            ]
            if not remaining:
                complete_aging(projection, event.id)


# ── Connections Roll ───────────────────────────────────────────────────────────


class ConnectionsRollHandler(EventHandlerBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind
    count: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.connection import make_connection

        for _ in range(self.count):
            projection.summary.connections.append(make_connection(self.connection_type))


# ── Skill Roll ─────────────────────────────────────────────────────────────────


class SkillRollHandler(EventHandlerBase):
    kind: Literal['skill_roll'] = 'skill_roll'
    skill: AnySkill | Chars
    modified_roll: int

    model_config = {'arbitrary_types_allowed': True}

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        pending_count_before = len(projection.pending_inputs)
        if fulfilled_pending is not None:
            fulfilled_pending.resolve(projection, event)
        if (
            len(projection.pending_inputs) == pending_count_before
            and projection.summary.current_career is not None
            and not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        ):
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment, event.id)
            )


# ── Life Event ─────────────────────────────────────────────────────────────────


class LifeEventHandler(EventHandlerBase):
    kind: Literal['life_event'] = 'life_event'
    roll: int  # 2D result (2-12) on the Life Events table

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.career.career_data import BenefitRollDm
        from ceres.character.domain.connection import Ally, Contact
        from ceres.character.domain.health.health_events import PendingInjuryTable
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeRequired

        if not (2 <= self.roll <= 12):
            raise ReplayError(f'Life event roll must be 2-12, got {self.roll}')
        in_career = projection.summary.current_career is not None
        career = projection.get_current_career() if in_career else None
        roll = self.roll
        _LIFE_EVENT_NARRATIVE = {
            2: 'Life event: sickness or injury',
            3: 'Life event: birth or death in the family',
            5: 'Life event: relationship strengthened (ally gained)',
            6: 'Life event: new relationship (ally gained)',
            7: 'Life event: new contact made',
            9: 'Life event: travel (qualification DM ahead)',
            10: 'Life event: good fortune (benefit roll bonus)',
            11: 'Life event: crime (lost a benefit roll)',
            12: 'Life event: unusual event — see sub-table',
        }
        if roll in _LIFE_EVENT_NARRATIVE:
            projection.summary.narrative.append(_LIFE_EVENT_NARRATIVE[roll])
        if roll == 2:
            projection.pending_inputs.append(
                PendingInjuryTable(
                    pending_id=(event.id, 0),
                    instruction='Roll 1D on Injury table (sickness/injury)',
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id, 1)
                )
        elif roll == 3:
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id)
                )
        elif roll == 4:
            projection.pending_inputs.append(
                PendingLifeEventChoice(
                    pending_id=(event.id, 0),
                    roll=4,
                    instruction='Ending relationship: gain a rival or enemy?',
                    options=[ConnectionKind.RIVAL, ConnectionKind.ENEMY],
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id, 1)
                )
        elif roll == 5:
            projection.summary.connections.append(Ally(source='Life event: improved relationship'))
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id)
                )
        elif roll == 6:
            projection.summary.connections.append(Ally(source='Life event: new relationship'))
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id)
                )
        elif roll == 7:
            projection.summary.connections.append(Contact(source='Life event: new contact'))
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id)
                )
        elif roll == 8:
            projection.pending_inputs.append(
                PendingLifeEventChoice(
                    pending_id=(event.id, 0),
                    roll=8,
                    instruction='Betrayal: gain a rival or enemy?',
                    options=[ConnectionKind.RIVAL, ConnectionKind.ENEMY],
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id, 1)
                )
        elif roll == 9:
            projection.pending_qualification_dm += 2
            projection.pending_inputs.append(
                PendingHomeworldChangeRequired(
                    pending_id=(event.id, 0),
                    instruction='You move to another world. Select your new homeworld.',
                    reason='Life Event 9: You move to another world.',
                    source_kind='life_event_move',
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id, 1)
                )
        elif roll == 10:
            if projection.summary.career_terms:
                projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms.append(
                    BenefitRollDm(amount=2)
                )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id)
                )
        elif roll == 11:
            projection.pending_inputs.append(
                PendingChoices(
                    pending_id=(event.id, 0),
                    instruction='Crime: choose a consequence',
                    choices=[LifeEventCrimeLoseBenefitRoll(), LifeEventCrimeTakePrisoner()],
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id, 1)
                )
        elif roll == 12:
            projection.pending_inputs.append(PendingLifeEventUnusual(pending_id=(event.id, 0)))
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment, event.id, 1)
                )


# ── Life Event Unusual ─────────────────────────────────────────────────────────


class LifeEventUnusualHandler(EventHandlerBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'
    roll: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        from ceres.character.domain.connection import Ally, Contact

        if not (1 <= self.roll <= 6):
            raise ReplayError(f'Life event unusual roll must be 1-6, got {self.roll}')
        if self.roll == 1:
            projection.summary.connections.append(Ally(source='Unusual event: useful ally'))
            projection.summary.narrative.append('Unusual event: gained a useful ally')
        elif self.roll == 2:
            projection.summary.connections.append(Contact(source='Unusual event: alien contact'))
            projection.grant_skill(
                cast(AnySkill, SpaceScience.model_validate({f: Level(value=1) for f in _level_fields(SpaceScience)}))
            )
            projection.summary.narrative.append('Unusual event: alien encounter — gained contact and Space Science 1')
        else:
            projection.summary.narrative.append('Unusual event: something strange (no mechanical effect)')


# ── Muster Out ─────────────────────────────────────────────────────────────────


class MusterOutHandler(EventHandlerBase):
    kind: Literal['muster_roll'] = 'muster_roll'
    table: Literal['cash', 'benefits']
    roll: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        muster_out_career = projection.muster_out_career
        if muster_out_career is None:
            raise ReplayError('No muster out career set')
        career = muster_out_career
        effective_roll = max(1, min(7, self.roll))
        row = career.muster_out.rows.get(effective_roll)
        if row is None:
            raise ReplayError(f'No muster out row for roll {effective_roll}')
        if self.table == 'cash':
            if projection.summary.muster_out_cash_count >= 3:
                raise ReplayError('Cash may only be taken a maximum of 3 times')
            projection.summary.cash += row.cash
            projection.summary.record_muster_out_cash_roll()
        else:
            for _ in range(row.count):
                row.benefit.apply(projection, event.id)
        remaining = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        if not remaining:
            if projection.summary.career_terms:
                projection.summary.career_terms[-1].require_muster_out().used = True
            projection.muster_out_career = None
            if not projection.summary.dead:
                queue_career_choice_indexed(projection, event.id, 0, 'Start a new career, or finish character creation')


# ── Benefit Choice ─────────────────────────────────────────────────────────────


class BenefitChoiceHandler(EventHandlerBase):
    kind: Literal['benefit_choice'] = 'benefit_choice'
    choice_index: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        if not isinstance(fulfilled_pending, PendingBenefitChoice):
            raise ReplayError('BenefitChoiceEvent must fulfill a PendingBenefitChoice')
        options = fulfilled_pending.benefit_options
        if not (0 <= self.choice_index < len(options)):
            raise ReplayError(f'choice_index {self.choice_index} out of range for {len(options)} options')
        options[self.choice_index].apply(projection, event.id)


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
            muster_out_setup(projection, career, event.id, 0, lose_current_term=False)
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
    assignment: str
    qualification_roll: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        new_assignment = career.assignment(self.assignment)
        if new_assignment is None:
            raise ReplayError(f'Unknown assignment {self.assignment!r} in career {career.name!r}')
        char = career.qualification.characteristic
        target = career.qualification.target
        dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
        if self.qualification_roll + dm >= target:
            projection.summary.current_assignment = new_assignment
            _start_new_career_term(projection, career, event.id)
        else:
            projection.pending_inputs.append(
                PendingReenlist(
                    pending_id=(event.id, 0),
                    instruction=(
                        f'Assignment change to {self.assignment!r} failed — reenlist with '
                        f'{projection.summary.current_assignment!r} or muster out?'
                    ),
                )
            )


# ── Injury/Nearly Killed ───────────────────────────────────────────────────────

# ── Choices Pending ────────────────────────────────────────────────────────────

# ── Skill Table Choice / Rank Bonus / Initial Training ────────────────────────

# ── Parole Roll ────────────────────────────────────────────────────────────────


class ParoleRollHandler(EventHandlerBase):
    kind: Literal['parole_roll'] = 'parole_roll'
    roll: int  # 1D result (1-6); Parole Threshold = roll + 2

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        pt = self.roll + 2
        projection.summary.parole_threshold = pt
        projection.summary.narrative.append(f'Prisoner: Parole Threshold set to {pt} (rolled {self.roll}+2)')


# ── InjuryTableHandler import from health for re-use ──────────────────────────

# Import InjuryTableHandler from health module to register it and make it available

# ── TypeAdapters for skill serialization ──────────────────────────────────────

_skill_adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)
_adv_dm_or_skill_adapter: TypeAdapter[AdvancementDmOption | AnySkill] = TypeAdapter(
    Annotated[AdvancementDmOption | AnySkill, Field(union_mode='left_to_right')]
)

# ── Skill-choice option builder ───────────────────────────────────────────────


def _build_skill_select_options(
    projection: CharacterProjection,
    options: Sequence[AnySkill | AdvancementDmOption],
    level: int | None,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for opt in options:
        if isinstance(opt, AdvancementDmOption):
            results.append((opt.label(), opt.model_dump_json()))
            continue
        skill_cls = type(opt)
        skill_name = skill_cls.name()
        if level == 0:
            skill = skill_cls()
            results.append((skill_name, _skill_adapter.dump_json(skill).decode()))
        else:
            choices = projection.skill_choices([skill_cls], level)
            for skill in choices:
                label = skill_name
                fields = _level_fields(skill_cls)
                if len(fields) > 1:
                    for fname, sname in zip(fields, skill_cls.specialities(), strict=False):
                        given = getattr(skill, fname).value
                        if given > 0:
                            label = f'{skill_name} ({sname})'
                            break
                results.append((label, _skill_adapter.dump_json(skill).decode()))
    return results


# ── Career helper functions ───────────────────────────────────────────────────


def _rank_bonus_skill(bonus: Any) -> AnySkill:
    from ceres.character.domain.skills import Level as _Level

    skill_cls = type(bonus.skill)
    fields = _level_fields(skill_cls)
    if len(fields) == 1:
        return skill_cls(**{fields[0]: _Level(value=bonus.level)})
    return skill_cls(**{f: _Level(value=bonus.level) for f in fields})


def _apply_auto_advance(projection: Any, career: Any, event_id: int) -> None:
    new_rank = (projection.summary.rank or 0) + 1
    projection.summary.rank = new_rank
    career.update_current_term_rank(projection)
    rank_entry = career.current_ranks(projection).get(new_rank)
    if rank_entry and rank_entry.bonus:
        bonus = rank_entry.bonus
        choices = bonus.resolve_choices()
        if choices:
            projection.pending_inputs.append(
                PendingRankBonusChoice(
                    pending_id=(event_id, 0),
                    level=bonus.level,
                    instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                    options=choices,
                )
            )
            return
        if bonus.skill:
            projection.grant_skill(_rank_bonus_skill(bonus))
        elif bonus.characteristic:
            char = bonus.characteristic
            projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
    edu = projection.summary.characteristics.get(Chars.EDU, 0)
    tables = career.available_tables(edu, projection.summary.current_assignment)
    projection.pending_inputs.append(
        PendingSkillTable(pending_id=(event_id, 0), instruction='Choose a skill table and roll 1D', options=tables)
    )
    queue_reenlist_or_aging(projection, event_id, 1)


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
    if assignment is None:
        raise ReplayError('No current assignment')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    return PendingAdvancement(pending_id=(event_id, pending_idx), instruction=f'Advancement: {char} {target}+')


def _apply_skill_table_entry(projection: Any, entry: Any) -> None:
    from ceres.character.domain.characteristics import Chars as _Chars

    if isinstance(entry, _Chars):
        projection.summary.characteristics[entry] = projection.summary.characteristics.get(entry, 0) + 1
    else:
        projection.increment_skill(entry)


def _set_forced_prison_career(projection: Any, description: str) -> None:
    from ceres.character.domain.career.prisoner import PRISONER

    projection.forced_next_career = PRISONER
    if projection.summary.career_terms:
        projection.summary.career_terms[-1].prison = description


def _apply_prisoner_advancement(projection: Any, event: Any, career: Any) -> None:
    assignment = projection.summary.current_assignment
    if assignment is None:
        raise ReplayError('No current assignment')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
    dm += projection.pending_advancement_dm
    projection.pending_advancement_dm = 0
    effective = event.roll + dm
    pt = projection.summary.parole_threshold or 0
    freed = effective > pt
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
                projection.grant_skill(_rank_bonus_skill(bonus))
            elif bonus.characteristic:
                char = bonus.characteristic
                projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
    if freed:
        projection.prisoner_freed = True
        projection.summary.narrative.append(f'Parole granted! (rolled {effective}, Parole Threshold was {pt})')
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


def _apply_mishap_ejection(
    projection: Any,
    career: Any,
    source_event_id: int,
    pending_idx: int,
    lose_current_term: bool = True,
) -> int:
    from ceres.character.domain.health.health_events import PendingAgingRoll

    projection.summary.age += 4
    if projection.summary.age >= 34:
        projection.muster_out_career = career
        projection.clear_current_career(ejected=True)
        projection.pending_inputs.append(
            PendingAgingRoll(pending_id=(source_event_id, pending_idx), instruction='Roll 2D on Aging table')
        )
        return pending_idx + 1
    return muster_out_setup(
        projection, career, source_event_id, pending_idx, lose_current_term=lose_current_term, ejected=True
    )


def purge_career_pendings(projection: CharacterProjection) -> None:
    projection.pending_inputs[:] = [
        p for p in projection.pending_inputs if not isinstance(p, _CAREER_PHASE_PENDING_TYPES)
    ]


def queue_career_choice_indexed(
    projection: CharacterProjection, event_id: int, idx: int, instruction: str = 'Choose a career'
) -> None:
    from ceres.character.domain.career.loader import selectable_careers

    if projection.forced_next_career:
        forced = projection.forced_next_career
        projection.forced_next_career = None
        projection.pending_inputs.append(
            PendingCareerChoice(
                pending_id=(event_id, idx),
                instruction=f'Next career: {forced.name} (mandatory)',
                options=[forced],
            )
        )
    else:
        career_options = sorted(selectable_careers(projection).values(), key=lambda c: c.name)
        projection.pending_inputs.append(
            PendingCareerChoice(
                pending_id=(event_id, idx),
                instruction=instruction,
                options=career_options,
            )
        )


def queue_career_choice(projection: CharacterProjection, event_id: int, instruction: str = 'Choose a career') -> None:
    queue_career_choice_indexed(projection, event_id, 0, instruction)


def queue_reenlist_or_aging(projection: CharacterProjection, event_id: int, idx: int) -> None:
    from ceres.character.domain.health.health_events import PendingAgingRoll

    if projection.prisoner_freed:
        projection.prisoner_freed = False
        projection.summary.age += 4
        career = projection.summary.current_career
        if projection.summary.age >= 34:
            if career:
                projection.muster_out_career = career
            projection.pending_reenlist = False
            projection.clear_current_career()
            projection.pending_inputs.append(
                PendingAgingRoll(pending_id=(event_id, idx), instruction='Roll 2D on Aging table')
            )
        elif career:
            muster_out_setup(projection, career, event_id, idx, lose_current_term=False)
        return

    projection.summary.age += 4
    if projection.forced_leave:
        projection.forced_leave = False
        career = projection.get_current_career() if projection.summary.current_career else None
        if career:
            if projection.summary.age >= 34:
                projection.muster_out_career = career
                projection.pending_reenlist = False
                projection.clear_current_career()
                projection.pending_inputs.append(
                    PendingAgingRoll(pending_id=(event_id, idx), instruction='Roll 2D on Aging table')
                )
            else:
                muster_out_setup(projection, career, event_id, idx, lose_current_term=False)
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
    career: CareerData,
    source_event_id: int,
    pending_idx: int = 0,
    lose_current_term: bool = False,
    clear_career: bool = True,
    ejected: bool = False,
) -> int:
    current_term = projection.summary.career_terms[-1] if projection.summary.career_terms else None
    muster_out = current_term.muster_out if current_term is not None else None
    run_terms = muster_out.terms if muster_out is not None else 0
    roll_count = run_terms + (projection.summary.rank or 0) // 2
    if lose_current_term:
        roll_count = max(0, roll_count - 1)
    if muster_out is not None:
        roll_count = max(0, roll_count - muster_out.lost_rolls) + muster_out.extra_rolls
    if clear_career:
        projection.clear_current_career(ejected=ejected)
    if roll_count > 0:
        projection.muster_out_career = career
        for _ in range(roll_count):
            projection.pending_inputs.append(
                PendingMusterOut(
                    pending_id=(source_event_id, pending_idx),
                )
            )
            pending_idx += 1
    else:
        queue_career_choice_indexed(projection, source_event_id, pending_idx)
        pending_idx += 1
    return pending_idx


def career_progress_pending(
    projection: Any, career: CareerData, event_id: int, pending_idx: int = 0
) -> PendingAdvancement | PendingCommissionChoice:
    if career.can_attempt_commission(projection):
        commission = career.commission
        if commission is None:
            raise ReplayError(f'{career.name} can attempt commission without commission rules')
        return PendingCommissionChoice(
            pending_id=(event_id, pending_idx),
            instruction=f'Attempt commission ({commission.characteristic} {commission.target}+) or roll advancement?',
        )
    assignment = projection.summary.current_assignment
    if assignment is None:
        raise ReplayError('No current assignment')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    return PendingAdvancement(pending_id=(event_id, pending_idx), instruction=f'Advancement: {char} {target}+')


# ── ChoiceBase subclasses for life events ─────────────────────────────────────


class LifeEventCrimeLoseBenefitRoll(ChoiceBase):
    kind: Literal['life_event_crime_lose_benefit_roll'] = 'life_event_crime_lose_benefit_roll'
    label: str = 'Lose one Benefit roll'

    def handle(self, projection: Any, event: Any) -> None:
        if projection.summary.career_terms:
            projection.summary.career_terms[-1].require_muster_out().lost_rolls += 1


class LifeEventCrimeTakePrisoner(ChoiceBase):
    kind: Literal['life_event_crime_take_prisoner'] = 'life_event_crime_take_prisoner'
    label: str = 'Take the Prisoner career next term'

    def handle(self, projection: Any, event: Any) -> None:
        from ceres.character.domain.career.prisoner import PRISONER

        projection.forced_next_career = PRISONER
        if projection.summary.career_terms:
            projection.summary.career_terms[
                -1
            ].prison = 'Crime life event — chose to take the Prisoner career next term.'


# ── Career Pending Input Types ────────────────────────────────────────────────


class PendingCareerChoice(PendingInputBase):
    kind: Literal['career_choice'] = 'career_choice'
    options: list[CareerData] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.domain.character_start import FinishCreationHandler
        from ceres.character.domain.precareer.precareer_events import PreCareerEntryHandler
        from ceres.character.mechanism.event_base import Event

        kind = form_str(form, 'kind', '')
        if kind == 'finish_creation':
            return Event(fulfills=self.pending_id, handler=FinishCreationHandler())
        if kind == 'precareer_entry':
            precareer = form_str(form, 'precareer', 'University')
            roll = form_int(form, 'roll', 7)
            return Event(fulfills=self.pending_id, handler=PreCareerEntryHandler(precareer=precareer, roll=roll))
        career = form_str(form, 'career')
        assignment = form_str(form, 'assignment')
        if not assignment:
            raise ValueError(f'Missing assignment for career {career!r}')
        roll = form_int(form, 'roll', 2)
        return Event(
            fulfills=self.pending_id,
            handler=CareerEntryHandler(career=career, assignment=assignment, qualification_roll=roll),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return []


class PendingDraftChoice(PendingInputBase):
    kind: Literal['draft_choice'] = 'draft_choice'
    can_draft: bool = True

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        choice = form_str(form, 'choice', 'drifter')
        if choice == 'draft':
            from ceres.character.domain.career.loader import load_careers

            roll = form_int(form, 'roll', 1)
            draft_careers = sorted(
                [c for c in load_careers().values() if c.does_draft()],
                key=lambda c: c.name,
            )
            career = draft_careers[max(0, min(roll, len(draft_careers)) - 1)]
            return Event(fulfills=self.pending_id, handler=DraftHandler(career=career.name))
        assignment = form_str(form, 'assignment', 'Wanderer')
        return Event(
            fulfills=self.pending_id,
            handler=CareerEntryHandler(career='Drifter', assignment=assignment, qualification_roll=2),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return []


class PendingDraftAssignmentChoice(PendingInputBase):
    kind: Literal['draft_assignment_choice'] = 'draft_assignment_choice'
    career: CareerData

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id,
            handler=DraftAssignmentHandler(career=self.career.name, assignment=form_str(form, 'assignment')),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options: list[tuple[str, str]] = [(a, a) for a in self.career.draft_assignments]
        return [
            Reference(name='career', value=self.career.name),
            Select(name='assignment', label='Assignment', options=options),
        ]


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

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=MishapHandler(roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6)]


class PendingAdvancement(PendingInputBase):
    kind: Literal['advancement_pending'] = 'advancement_pending'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=AdvancementHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]


class PendingCommissionChoice(PendingInputBase):
    kind: Literal['commission_choice'] = 'commission_choice'
    options: ClassVar[tuple[Literal['attempt'], Literal['skip']]] = ('attempt', 'skip')

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        choice = form_str(form, 'choice', 'skip')
        if choice == 'attempt':
            return Event(
                fulfills=self.pending_id, handler=CommissionHandler(attempt=True, roll=form_int(form, 'roll', 7))
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
    instruction: str = 'Stay, switch assignment, or muster out?'
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

        assignment = form_str(form, 'assignment', self.options[0].name if self.options else '')
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


class PendingMusterOut(PendingInputBase):
    kind: Literal['muster_roll_pending'] = 'muster_roll_pending'
    instruction: str = 'Muster out: choose cash or benefits table'
    options: ClassVar[tuple[Literal['cash'], Literal['benefits']]] = ('cash', 'benefits')

    def event_from_form(self, form: Any) -> Any:
        from typing import Literal as _Literal, cast as _cast

        from ceres.character.mechanism.event_base import Event

        table = _cast(
            _Literal['cash', 'benefits'],
            literal(form_str(form, 'table', 'benefits'), ('cash', 'benefits'), 'benefits'),
        )
        return Event(fulfills=self.pending_id, handler=MusterOutHandler(table=table, roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        table_options: list[tuple[str, str]] = [(opt.title(), opt) for opt in self.options]
        total_dm = 0
        if projection.summary.career_terms:
            mo = projection.summary.career_terms[-1].muster_out
            if mo is not None:
                total_dm = sum(dm.amount for dm in mo.benefit_roll_dms)
        if total_dm:
            roll_label = f'1D roll (1–6); DM+{total_dm} available on benefits table'
        else:
            roll_label = '1D roll (1–6, apply DMs first)'
        return [
            Select(name='table', label='Table', options=table_options),
            NumberEntry(name='roll', label=roll_label, min=1, max=7),
        ]


class PendingSkillChoice(PendingInputBase):
    kind: Literal['skill_choice'] = 'skill_choice'
    options: list[AnySkill] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        parsed = _adv_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return Event(fulfills=self.pending_id, handler=AdvancementDmChoiceHandler())
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=cast(AnySkill, parsed)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, None)
        return [Select(name='skill', label='Choose a skill', options=options)]


class PendingInitialTrainingChoice(PendingInputBase):
    kind: Literal['initial_training_choice'] = 'initial_training_choice'
    options: list[AnySkill | AdvancementDmOption] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        parsed = _adv_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return Event(fulfills=self.pending_id, handler=AdvancementDmChoiceHandler())
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=cast(AnySkill, parsed)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, 0)
        return [Select(name='skill', label='Choose a skill', options=options)]

    def on_skill_chosen(self, projection: Any, event: Any) -> None:
        projection.grant_skill(event.skill)
        remaining = [p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice)]
        if not remaining and projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(_survive_pending(career, projection.summary.current_assignment, event.id))


class PendingSkillTableChoice(PendingInputBase):
    kind: Literal['skill_table_choice'] = 'skill_table_choice'
    reenlist_queued: bool = False
    options: list[AnySkill | AdvancementDmOption] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        parsed = _adv_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return Event(fulfills=self.pending_id, handler=AdvancementDmChoiceHandler())
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=cast(AnySkill, parsed)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, None)
        return [Select(name='skill', label='Choose a skill', options=options)]

    def on_skill_chosen(self, projection: Any, event: Any) -> None:
        projection.grant_skill(event.skill)
        if projection.summary.current_career is not None and not self.reenlist_queued:
            career = projection.get_current_career()
            projection.pending_inputs.append(_survive_pending(career, projection.summary.current_assignment, event.id))


class PendingRankBonusChoice(PendingInputBase):
    kind: Literal['rank_bonus_choice'] = 'rank_bonus_choice'
    level: int
    options: list[AnySkill | AdvancementDmOption] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        parsed = _adv_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return Event(fulfills=self.pending_id, handler=AdvancementDmChoiceHandler())
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=cast(AnySkill, parsed)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, self.level)
        return [Select(name='skill', label='Choose a skill', options=options)]

    def on_skill_chosen(self, projection: Any, event: Any) -> None:
        projection.grant_skill(event.skill)
        career = projection.get_current_career()
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = career.available_tables(edu, projection.summary.current_assignment)
        projection.pending_inputs.append(
            PendingSkillTable(pending_id=(event.id, 0), instruction='Choose a skill table and roll 1D', options=tables)
        )
        queue_reenlist_or_aging(projection, event.id, 1)


class PendingBenefitChoice(PendingInputBase):
    kind: Literal['benefit_choice_pending'] = 'benefit_choice_pending'
    benefit_options: list[AnyBenefit]

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(
            fulfills=self.pending_id, handler=BenefitChoiceHandler(choice_index=form_int(form, 'choice_index', 0))
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(b.display_label, str(i)) for i, b in enumerate(self.benefit_options)]
        return [Select(name='choice_index', label='Choose benefit', options=options)]


class PendingChoices(PendingInputBase):
    kind: Literal['choices'] = 'choices'
    choices: list[SerializeAsAny[ChoiceBase]] = Field(default_factory=list)

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=CareerChoiceHandler(choice=form_str(form, 'choice', '')))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [Select(name='choice', label=self.instruction, options=[(c.label, c.kind) for c in self.choices])]


class PendingLifeEvent(PendingInputBase):
    kind: Literal['life_event'] = 'life_event'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=LifeEventHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', min=2, max=12)]


class PendingLifeEventChoice(PendingInputBase):
    kind: Literal['life_event_choice'] = 'life_event_choice'
    roll: int
    options: list[ConnectionKind] = Field(default_factory=list)

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        raw_ck = literal(
            form_str(form, 'connection_kind', ConnectionKind.RIVAL), tuple(ConnectionKind), ConnectionKind.RIVAL
        )
        return Event(
            fulfills=self.pending_id,
            handler=ConnectionKindChoiceHandler(connection_kind=ConnectionKind(raw_ck)),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [('Rival', ConnectionKind.RIVAL.value), ('Enemy', ConnectionKind.ENEMY.value)]
        return [Select(name='connection_kind', label='Connection type', options=options)]


class PendingLifeEventUnusual(PendingInputBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'
    instruction: str = 'Roll 1D on Unusual Events table'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=LifeEventUnusualHandler(roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6)]


class PendingConnectionsRoll(PendingInputBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind = ConnectionKind.CONTACT
    options: list[int] = Field(default_factory=list)

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        raw_ct = literal(
            form_str(form, 'connection_type', ConnectionKind.CONTACT), tuple(ConnectionKind), ConnectionKind.CONTACT
        )
        count = form_int(form, 'count', 1)
        return Event(
            fulfills=self.pending_id,
            handler=ConnectionsRollHandler(connection_type=ConnectionKind(raw_ct), count=count),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        count_options = (
            [(str(opt), str(opt)) for opt in self.options] if self.options else [(str(i), str(i)) for i in range(1, 7)]
        )
        return [
            Reference(name='connection_type', value=self.connection_type.value),
            Select(name='count', label='Count', options=count_options),
        ]


class PendingParoleRoll(PendingInputBase):
    kind: Literal['parole_roll'] = 'parole_roll'

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.mechanism.event_base import Event

        return Event(fulfills=self.pending_id, handler=ParoleRollHandler(roll=form_int(form, 'roll', 1)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', min=1, max=6)]


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
