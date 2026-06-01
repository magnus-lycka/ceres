import random
import re
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast

from pydantic import BaseModel, Field, TypeAdapter, field_serializer, field_validator

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.benefits import AnyBenefit, ItemBenefit
from ceres.character.characteristics import UCP_STATS, Chars, ConnectionKind, characteristic_dm

if TYPE_CHECKING:
    from ceres.character.careers.career_data import CareerData
from ceres.character.input_specs import InputSpec, NumberEntry, Reference, Select, form_int, form_str, literal
from ceres.character.skills import (
    AnySkill,
    BackgroundSkill,
    Skill,
    SpaceScience,
    _level_fields,
    _skill_classes,
    parse_skill_spec_option,
    skill_class_by_name,
    skill_from_str,
    skill_names_for_category,
)
from ceres.character.sophonts import Sophont, get_sophont
from ceres.character.state import (
    Ally,
    AutoFillContext,
    CareerTerm,
    CharacterProjection,
    CharacterSummary,
    Contact,
    PendingInputBase,
    ReplayError,
    ScheduledEffect,
    make_connection,
)

BACKGROUND_SKILLS: frozenset[type[Skill]] = frozenset(_skill_classes(BackgroundSkill))


def _background_skill_count(edu: int) -> int:
    return max(0, characteristic_dm(edu) + 3)


_CHOOSE_COUNT_RE = re.compile(r'Choose (\d+)')
_skill_adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)
_NON_SKILL_OPTION_LABELS: dict[str, str] = {'advancement_dm_4': 'DM+4 to next advancement roll'}


def _roll2d(rng: random.Random) -> int:
    return rng.randint(1, 6) + rng.randint(1, 6)


def _roll1d(rng: random.Random) -> int:
    return rng.randint(1, 6)


def _apply_simple_effect(projection: Any, effect: Any, source: str = '', source_event_id: int = 0) -> None:
    from ceres.character.careers.career_data import (
        AdvancementDmEffect,
        BenefitDmEffect,
        DecreaseCharacteristicEffect,
        GainAllyEffect,
        GainContactEffect,
        GainEnemyEffect,
        GainRivalEffect,
        GainSkillEffect,
        ParoleThresholdChangeEffect,
    )
    from ceres.character.skills import skill_from_str

    if isinstance(effect, GainSkillEffect):
        projection.grant_skill(skill_from_str(effect.skill, effect.level))
    elif isinstance(effect, DecreaseCharacteristicEffect):
        current = projection.summary.characteristics.get(effect.characteristic, 0)
        projection.summary.characteristics[effect.characteristic] = max(0, current - effect.amount)
    elif isinstance(effect, GainContactEffect):
        projection.summary.connections.append(make_connection(ConnectionKind.CONTACT, source=source))
    elif isinstance(effect, GainAllyEffect):
        projection.summary.connections.append(make_connection(ConnectionKind.ALLY, source=source))
    elif isinstance(effect, GainRivalEffect):
        projection.summary.connections.append(make_connection(ConnectionKind.RIVAL, source=source))
    elif isinstance(effect, GainEnemyEffect):
        projection.summary.connections.append(make_connection(ConnectionKind.ENEMY, source=source))
    elif isinstance(effect, AdvancementDmEffect):
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement', source_event_id=source_event_id, effect={'type': 'dm', 'amount': effect.amount}
            )
        )
    elif isinstance(effect, BenefitDmEffect):
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out', source_event_id=source_event_id, effect={'type': 'dm', 'amount': effect.amount}
            )
        )
    elif isinstance(effect, ParoleThresholdChangeEffect) and projection.summary.parole_threshold is not None:
        new_pt = projection.summary.parole_threshold + effect.amount
        projection.summary.parole_threshold = max(0, min(12, new_pt))
    # InjuryEffect, SkillChoiceEffect, etc. are handled before _apply_simple_effect is called


def _apply_auto_advance(projection: Any, career: Any, event_id: int) -> None:
    from ceres.character.skills import skill_from_str

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
                    id=f'{event_id}.0',
                    level=bonus.level,
                    instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                    options=choices,
                )
            )
            return
        if bonus.skill:
            projection.grant_skill(skill_from_str(bonus.skill, bonus.level))
        elif bonus.characteristic:
            char = bonus.characteristic
            projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
    edu = projection.summary.characteristics.get(Chars.EDU, 0)
    tables = career.available_tables(edu, projection.summary.current_assignment or '')
    projection.pending_inputs.append(
        PendingSkillTable(id=f'{event_id}.0', instruction='Choose a skill table and roll 1D', options=tables)
    )
    queue_reenlist_or_aging(projection, event_id, 1)


def _start_new_career_term(projection: Any, career: Any, event_id: int) -> None:

    purge_career_pendings(projection)
    assignment_name = projection.summary.current_assignment or ''
    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r} in career {career.name!r}')
    career.start_new_term(projection, assignment, event_id)


def _survive_pending(career: Any, assignment_name: str, event_id: int) -> Any:

    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r} in career {career.name!r}')
    return career.survival_pending(assignment, event_id)


def _advancement_pending(career: Any, assignment_name: str, event_id: int, pending_idx: int = 0) -> Any:

    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r}')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    return PendingAdvancement(id=f'{event_id}.{pending_idx}', instruction=f'Advancement: {char} {target}+')


def _apply_injury_table_result(projection: Any, roll: int, event_id: int) -> None:

    if roll == 6:
        return
    if roll == 5:
        projection.pending_inputs.append(
            PendingCharacteristicChoice(
                id=f'{event_id}.0',
                instruction='Injured: choose STR, DEX, or END to reduce by 1',
                options=[Chars.STR, Chars.DEX, Chars.END],
            )
        )
    elif roll == 4:
        projection.pending_inputs.append(
            PendingCharacteristicChoice(
                id=f'{event_id}.0',
                instruction='Scarred: choose STR, DEX, or END to reduce by 2',
                options=[Chars.STR, Chars.DEX, Chars.END],
            )
        )
    elif roll == 3:
        projection.pending_inputs.append(
            PendingCharacteristicChoice(
                id=f'{event_id}.0',
                instruction='Missing Eye or Limb: choose STR or DEX to reduce by 2',
                options=[Chars.STR, Chars.DEX],
            )
        )
    elif roll == 2:
        projection.pending_inputs.append(
            PendingCharacteristicChoice(
                id=f'{event_id}.0',
                instruction='Severely injured: roll 1D — choose STR, DEX, or END to reduce by that amount',
                options=[Chars.STR, Chars.DEX, Chars.END],
            )
        )
    elif roll == 1:
        projection.pending_inputs.append(
            PendingNearlyKilled(
                id=f'{event_id}.0',
                instruction=(
                    'Nearly killed: roll 1D — choose STR, DEX, or END to reduce by that amount; '
                    'the other two physical characteristics are each reduced by 2'
                ),
                options=[Chars.STR, Chars.DEX, Chars.END],
            )
        )


def _apply_muster_out_benefit(projection: Any, benefit: object, event_id: int = 0) -> None:
    from ceres.character.benefits import CharacteristicIncrease, ChoiceBenefit

    if isinstance(benefit, CharacteristicIncrease):
        current = projection.summary.characteristics.get(benefit.char, 0)
        projection.summary.characteristics[benefit.char] = min(15, current + benefit.amount)
    elif isinstance(benefit, ItemBenefit):
        projection.summary.benefits.append(benefit)
    elif isinstance(benefit, ChoiceBenefit):
        projection.pending_inputs.append(
            PendingBenefitChoice(
                id=f'{event_id}.benefit_choice',
                instruction=f'Choose one benefit: {benefit.display_label}',
                options=[b.display_label for b in benefit.options],
                benefit_options=list(benefit.options),
            )
        )


def _apply_skill_table_entry(projection: Any, entry: Any) -> None:
    if entry.characteristic:
        char = entry.characteristic
        projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + 1
    elif entry.skill:
        projection.increment_skill(entry.skill, entry.spec)


def _apply_mishap_ejection(
    projection: Any,
    career: Any,
    source_event_id: int,
    pending_idx: int,
    lose_current_term: bool = True,
) -> int:

    projection.summary.age += 4
    if projection.summary.age >= 34:
        projection.muster_out_career = career.name
        projection.clear_current_career()
        projection.pending_inputs.append(
            PendingAgingRoll(id=f'{source_event_id}.{pending_idx}', instruction='Roll 2D on Aging table')
        )
        return pending_idx + 1
    return muster_out_setup(projection, career, source_event_id, pending_idx, lose_current_term=lose_current_term)


def _apply_prisoner_advancement(projection: Any, event: Any, career: Any) -> None:

    assignment = career.assignment(projection.summary.current_assignment or '')
    if assignment is None:
        raise ReplayError(f'Unknown assignment {projection.summary.current_assignment!r}')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
    to_consume = [se for se in projection.scheduled_effects if se.trigger == 'advancement' and se.consume]
    for se in to_consume:
        dm += se.effect.get('amount', 0)
        projection.scheduled_effects.remove(se)
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
                    id=f'{event.id}.0',
                    level=bonus.level,
                    instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                    options=choices,
                )
            elif bonus.skill:
                projection.grant_skill(skill_from_str(bonus.skill, bonus.level))
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
        tables = career.available_tables(edu, projection.summary.current_assignment or '')
        projection.pending_inputs.append(
            PendingSkillTable(id=f'{event.id}.0', instruction='Choose a skill table and roll 1D', options=tables)
        )
        queue_reenlist_or_aging(projection, event.id, 1)
    else:
        queue_reenlist_or_aging(projection, event.id, 0)


class EventBase(BaseModel):
    id: int = 0  # assigned by store; 0 means unassigned
    fulfills: str | None = None

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        raise NotImplementedError(f'{type(self).__name__}.apply() not implemented')


class CharacterStartedEvent(EventBase):
    kind: Literal['character_started'] = 'character_started'
    sophont: Sophont
    homeworld: TravellerMapWorld
    player: str = 'NPC'
    name: str

    @field_validator('sophont', mode='before')
    @classmethod
    def _coerce_sophont(cls, v: object) -> Sophont:
        if isinstance(v, Sophont):
            return v
        if isinstance(v, str):
            result = get_sophont(v)
            if result is None:
                raise ValueError(f'Unknown sophont: {v!r}')
            return result
        raise ValueError(f'Expected Sophont or sophont name, got {type(v).__name__}')

    @field_serializer('sophont')
    def _serialize_sophont(self, v: Sophont) -> str:
        return v.name


class UcpEvent(EventBase):
    kind: Literal['ucp'] = 'ucp'
    ucp: str

    def _parse_characteristics(self, sophont: Any) -> dict[Chars, int]:

        ucp_stats = sophont.ucp_stats if isinstance(sophont, Sophont) else UCP_STATS
        if len(self.ucp) != len(ucp_stats):
            raise ReplayError(f'Invalid UCP: {self.ucp!r} — expected {len(ucp_stats)} hex digits')
        return {stat: int(digit, 16) for stat, digit in zip(ucp_stats, self.ucp, strict=True)}

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        projection.summary.characteristics = self._parse_characteristics(projection.summary.sophont)
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        count = _background_skill_count(edu)
        if count > 0:
            projection.pending_inputs.append(
                PendingBackgroundSkills(
                    id=f'{self.id}.0',
                    instruction=f'Choose {count} background skill(s)',
                    options=sorted(cls.name() for cls in BACKGROUND_SKILLS),
                )
            )


class BackgroundSkillsEvent(EventBase):
    kind: Literal['background_skills'] = 'background_skills'
    skills: list[AnySkill]

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        expected = _background_skill_count(edu)
        if len(self.skills) != expected:
            raise ReplayError(f'Expected {expected} background skill(s), got {len(self.skills)}')
        invalid = [s for s in self.skills if type(s) not in BACKGROUND_SKILLS]
        if invalid:
            raise ReplayError(f'Invalid background skill(s): {", ".join(sorted(type(s).__name__ for s in invalid))}')
        for skill in self.skills:
            projection.grant_skill(skill)
        queue_career_choice(projection, self.id, 'Choose a career')


class CareerEvent(EventBase):
    kind: Literal['career'] = 'career'
    career: str
    assignment: str
    qualification_roll: int  # 2D result before characteristic DM

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.loader import load_careers

        careers = load_careers()
        career = careers.get(self.career)
        if career is None:
            raise ReplayError(f'Unknown career: {self.career!r}')
        assignment = career.assignment(self.assignment)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {self.assignment!r} for career {self.career!r}')
        career.start_career(projection, assignment, self.id, self.qualification_roll)


class DraftEvent(EventBase):
    kind: Literal['draft'] = 'draft'
    career: str
    assignment: str | None = None

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.loader import load_careers

        if projection.summary.drafted:
            raise ReplayError('A character may only enter the draft once')
        career = load_careers().get(self.career)
        if career is None:
            raise ReplayError(f'Unknown career: {self.career!r}')
        career.start_draft(projection, self.id, self.assignment)


class DraftAssignmentEvent(EventBase):
    kind: Literal['draft_assignment'] = 'draft_assignment'
    career: str
    assignment: str

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.loader import load_careers

        career = load_careers().get(self.career)
        if career is None:
            raise ReplayError(f'Unknown career: {self.career!r}')
        career.start_draft(projection, self.id, self.assignment)


class SurviveEvent(EventBase):
    kind: Literal['survive'] = 'survive'
    roll: int  # sum of 2D, before characteristic DM

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        assignment = career.assignment(projection.summary.current_assignment or '')
        if assignment is None:
            raise ReplayError(f'Unknown assignment {projection.summary.current_assignment!r}')
        char = assignment.survival.characteristic
        target = assignment.survival.target
        dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
        success = self.roll != 2 and (self.roll + dm) >= target
        if success:
            projection.pending_inputs.append(PendingTermEvent(id=f'{self.id}.0', instruction='Roll 2D on Events table'))
        else:
            if self.roll == 2:
                projection.summary.narrative.append(
                    f'Automatic mishap (rolled natural 2) in term {projection.summary.term_count}'
                )
            projection.pending_inputs.append(PendingMishap(id=f'{self.id}.0', instruction='Roll 1D on Mishap table'))


class MishapEvent(EventBase):
    kind: Literal['mishap'] = 'mishap'
    roll: int  # 1D result
    stay_in_career: bool = False  # True when the event says "mishap but you are not ejected"

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.career_data import (
            DecreaseCharacteristicChoiceEffect,
            GainConnectionsRolledEffect,
            InjuryEffect,
            SkillChoiceEffect,
        )
        from ceres.character.careers.loader import get_effect_handler

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
                            id=f'{self.id}.{pending_idx}',
                            instruction=(
                                f'Choose characteristic to decrease by {effect.amount}: {", ".join(effect.options)}'
                            ),
                            options=effect.options,
                        )
                    )
                    pending_idx += 1
                elif isinstance(effect, GainConnectionsRolledEffect):
                    projection.pending_inputs.append(
                        PendingConnectionsRoll(
                            id=f'{self.id}.{pending_idx}',
                            connection_type=effect.connection_type,
                            instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s',
                            options=[str(i) for i in range(1, 7)],
                        )
                    )
                    pending_idx += 1
                elif isinstance(effect, SkillChoiceEffect):
                    projection.pending_inputs.append(
                        PendingSkillChoice(
                            id=f'{self.id}.{pending_idx}',
                            instruction=f'Choose one skill: {", ".join(effect.options)}',
                            options=effect.options,
                        )
                    )
                    pending_idx += 1
                elif isinstance(effect, InjuryEffect):
                    if effect.severity == 'normal':
                        projection.pending_inputs.append(
                            PendingCharacteristicChoice(
                                id=f'{self.id}.{pending_idx}',
                                instruction='Injured: choose STR, DEX, or END to reduce by 1',
                                options=[Chars.STR, Chars.DEX, Chars.END],
                            )
                        )
                        pending_idx += 1
                    elif effect.severity == 'severe':
                        projection.pending_inputs.append(
                            PendingCharacteristicChoice(
                                id=f'{self.id}.{pending_idx}',
                                instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                                options=[Chars.STR, Chars.DEX, Chars.END],
                            )
                        )
                        pending_idx += 1
                    elif effect.severity == 'from_table':
                        projection.pending_inputs.append(
                            PendingInjuryTable(
                                id=f'{self.id}.{pending_idx}',
                                instruction='Roll 1D on Injury table',
                                options=['1', '2', '3', '4', '5', '6'],
                            )
                        )
                        pending_idx += 1
                else:
                    handler = get_effect_handler(career.name, effect.type)
                    if handler:
                        pending_idx = handler(projection, effect, self.id, pending_idx)
                    else:
                        _apply_simple_effect(projection, effect, source=mishap.text, source_event_id=self.id)
        defer = mishap is not None and mishap.defer_ejection
        if defer:
            pass  # handler owns the full ejection/stay flow; nothing automatic here
        elif self.stay_in_career or (mishap is not None and mishap.stay_in_career):
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', self.id, pending_idx)
            )
        else:
            purge_career_pendings(projection)
            projection.summary.age += 4
            if projection.summary.age >= 34:
                projection.muster_out_career = career.name
                projection.clear_current_career()
                projection.pending_inputs.append(
                    PendingAgingRoll(id=f'{self.id}.{pending_idx}', instruction='Roll 2D on Aging table')
                )
            else:
                muster_out_setup(projection, career, self.id, pending_idx, lose_current_term=True)


class TermEventEvent(EventBase):
    kind: Literal['term_event'] = 'term_event'
    roll: int  # sum of 2D

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.career_data import (
            AutoAdvanceEffect,
            LifeEventEffect,
            RollMishapEffect,
            SkillChoiceEffect,
        )
        from ceres.character.careers.loader import get_effect_handler

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
                f'Term {projection.summary.term_count} event ({career.name}): {term_event.text}'
            )
            for effect in term_event.effects:
                if isinstance(effect, SkillChoiceEffect):
                    skill_choice_effect = effect
                elif isinstance(effect, RollMishapEffect):
                    roll_mishap_effect = effect
                elif isinstance(effect, AutoAdvanceEffect):
                    auto_advance = True
                elif isinstance(effect, LifeEventEffect):
                    life_event_pending = True
                else:
                    handler = get_effect_handler(career.name, effect.type)
                    if handler:
                        pending_idx = handler(projection, effect, self.id, pending_idx)
                        career_handler_invoked = True
                    else:
                        _apply_simple_effect(projection, effect, source=term_event.text, source_event_id=self.id)
        if roll_mishap_effect is not None:
            instruction = (
                'Roll 1D on Mishap table (you are not ejected from this career)'
                if not roll_mishap_effect.leave
                else 'Roll 1D on Mishap table'
            )
            projection.pending_inputs.append(PendingMishap(id=f'{self.id}.{pending_idx}', instruction=instruction))
        elif auto_advance:
            _apply_auto_advance(projection, career, self.id)
        elif life_event_pending:
            projection.pending_inputs.append(
                PendingLifeEvent(id=f'{self.id}.{pending_idx}', instruction='Roll 2D on Life Events table')
            )
        elif skill_choice_effect is not None:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{self.id}.{pending_idx}',
                    instruction=f'Choose one skill: {", ".join(skill_choice_effect.options)}',
                    options=skill_choice_effect.options,
                )
            )
        elif not career_handler_invoked:
            projection.pending_inputs.append(career_progress_pending(projection, career, self.id))


class SkillChoiceEvent(EventBase):
    kind: Literal['skill_choice'] = 'skill_choice'
    skill: AnySkill

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        if isinstance(fulfilled_pending, PendingInitialTrainingChoice):
            projection.grant_skill(self.skill)
            remaining = [p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice)]
            if not remaining and projection.summary.current_career is not None:
                career = projection.get_current_career()
                projection.pending_inputs.append(
                    _survive_pending(career, projection.summary.current_assignment or '', self.id)
                )
        elif isinstance(fulfilled_pending, PendingSkillTableChoice):
            projection.grant_skill(self.skill)
            if projection.summary.current_career is not None and not fulfilled_pending.reenlist_queued:
                career = projection.get_current_career()
                projection.pending_inputs.append(
                    _survive_pending(career, projection.summary.current_assignment or '', self.id)
                )
        elif isinstance(fulfilled_pending, PendingCareerSkillChoice):
            projection.grant_skill(self.skill)
            if not fulfilled_pending.advancement_precreated and projection.summary.current_career is not None:
                career = projection.get_current_career()
                projection.pending_inputs.append(career_progress_pending(projection, career, self.id))
        elif isinstance(fulfilled_pending, PendingRankBonusChoice):
            projection.grant_skill(self.skill)
            career = projection.get_current_career()
            edu = projection.summary.characteristics.get(Chars.EDU, 0)
            tables = career.available_tables(edu, projection.summary.current_assignment or '')
            projection.pending_inputs.append(
                PendingSkillTable(id=f'{self.id}.0', instruction='Choose a skill table and roll 1D', options=tables)
            )
            queue_reenlist_or_aging(projection, self.id, 1)
        else:
            projection.grant_skill(self.skill)
            if projection.summary.current_career is not None:
                career = projection.get_current_career()
                projection.pending_inputs.append(career_progress_pending(projection, career, self.id))


class AdvancementDmChoiceEvent(EventBase):
    kind: Literal['advancement_dm_choice'] = 'advancement_dm_choice'

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        projection.scheduled_effects.append(
            ScheduledEffect(trigger='advancement', source_event_id=self.id, effect={'type': 'dm', 'amount': 4})
        )
        if projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', self.id)
            )


class ConnectionKindChoiceEvent(EventBase):
    kind: Literal['connection_kind_choice'] = 'connection_kind_choice'
    connection_kind: ConnectionKind

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        source = (
            f'Life event roll {fulfilled_pending.roll}'
            if isinstance(fulfilled_pending, PendingLifeEventChoice)
            else 'unknown'
        )
        projection.summary.connections.append(make_connection(self.connection_kind, source=f'Life event: {source}'))
        _CHOICE_NARRATIVE = {
            4: {
                'rival': 'Life event: relationship ended, gained a rival',
                'enemy': 'Life event: relationship ended, gained an enemy',
            },
            8: {
                'rival': 'Life event: betrayal, gained a rival',
                'enemy': 'Life event: betrayal, gained an enemy',
            },
        }
        if isinstance(fulfilled_pending, PendingLifeEventChoice):
            kind_map = _CHOICE_NARRATIVE.get(fulfilled_pending.roll)
            if kind_map:
                entry = kind_map.get(self.connection_kind)
                if entry:
                    projection.summary.narrative.append(entry)
        # advancement was pre-created by _apply_life_event


class CareerChoiceEvent(EventBase):
    """Generic career-specific choice event replacing per-career event types."""

    kind: Literal['career_decision'] = 'career_decision'
    context: str  # key into the career's CHOICE_HANDLERS registry
    choice: str

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.loader import get_choice_handler

        career_name = projection.summary.current_career
        if career_name is None:
            raise ReplayError(f'CareerChoiceEvent submitted with no active career (context={self.context!r})')
        handler = get_choice_handler(career_name, self.context)
        if handler is None:
            raise ReplayError(f'No choice handler for career {career_name!r} context {self.context!r}')
        handler(projection, self)


class AdvancementEvent(EventBase):
    kind: Literal['advancement'] = 'advancement'
    roll: int  # sum of 2D, before characteristic DM

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        if career.name == 'Prisoner':
            _apply_prisoner_advancement(projection, self, career)
            return
        assignment = career.assignment(projection.summary.current_assignment or '')
        if assignment is None:
            raise ReplayError(f'Unknown assignment {projection.summary.current_assignment!r}')
        char = assignment.advancement.characteristic
        target = assignment.advancement.target
        dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
        to_consume = [se for se in projection.scheduled_effects if se.trigger == 'advancement' and se.consume]
        for se in to_consume:
            dm += se.effect.get('amount', 0)
            projection.scheduled_effects.remove(se)
        success = (self.roll + dm) >= target
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
                            id=f'{self.id}.0',
                            level=bonus.level,
                            instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                            options=choices,
                        )
                    )
                    return
                if bonus.skill:
                    projection.grant_skill(skill_from_str(bonus.skill, bonus.level))
                elif bonus.characteristic:
                    char = bonus.characteristic
                    projection.summary.characteristics[char] = (
                        projection.summary.characteristics.get(char, 0) + bonus.level
                    )
            edu = projection.summary.characteristics.get(Chars.EDU, 0)
            tables = career.available_tables(edu, projection.summary.current_assignment or '')
            projection.pending_inputs.append(
                PendingSkillTable(id=f'{self.id}.0', instruction='Choose a skill table and roll 1D', options=tables)
            )
            queue_reenlist_or_aging(projection, self.id, 1)
            return
        queue_reenlist_or_aging(projection, self.id, 0)


class CommissionEvent(EventBase):
    kind: Literal['commission'] = 'commission'
    attempt: bool
    roll: int = 0  # sum of 2D, before characteristic DM and term DM; ignored when attempt is False

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        if not self.attempt:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', self.id)
            )
            return
        if career.commission is None:
            raise ReplayError(f'{career.name} does not support commission')
        dm = career.commission_dm(projection)
        to_consume = [se for se in projection.scheduled_effects if se.trigger == 'advancement' and se.consume]
        for se in to_consume:
            dm += se.effect.get('amount', 0)
            projection.scheduled_effects.remove(se)
        if self.roll + dm < career.commission.target:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', self.id)
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
                        id=f'{self.id}.0',
                        level=bonus.level,
                        instruction=f'Rank 1 bonus: choose skill at level {bonus.level}',
                        options=choices,
                    )
                )
                return
            if bonus.skill:
                projection.grant_skill(skill_from_str(bonus.skill, bonus.level))
            elif bonus.characteristic:
                char = bonus.characteristic
                projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = career.available_tables(edu, projection.summary.current_assignment or '')
        projection.pending_inputs.append(
            PendingSkillTable(id=f'{self.id}.0', instruction='Choose a skill table and roll 1D', options=tables)
        )
        queue_reenlist_or_aging(projection, self.id, 1)


class ReenlistEvent(EventBase):
    kind: Literal['reenlist'] = 'reenlist'
    reenlist: bool

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        if self.reenlist:
            career = projection.get_current_career()
            _start_new_career_term(projection, career, self.id)
        else:
            purge_career_pendings(projection)
            career = projection.get_current_career()
            muster_out_setup(projection, career, self.id, 0, lose_current_term=False)


class SkillTableEvent(EventBase):
    kind: Literal['skill_table'] = 'skill_table'
    table: str  # 'personal_development', 'service_skills', 'advanced_education', or assignment name
    roll: int  # 1D result (1-6)

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        table = career.skill_tables.get(self.table)
        if table is None:
            raise ReplayError(f'Unknown skill table: {self.table!r}')
        if table.min_edu is not None:
            edu = projection.summary.characteristics.get(Chars.EDU, 0)
            if edu < table.min_edu:
                raise ReplayError(f'Table {self.table!r} requires EDU {table.min_edu}+, character has {edu}')
        if not (1 <= self.roll <= 6):
            raise ReplayError(f'Skill table roll must be 1-6, got {self.roll}')
        entry = table.entries.get(self.roll)
        if entry is None:
            raise ReplayError(f'No entry for roll {self.roll} in table {self.table!r}')
        assignment_name = projection.summary.current_assignment or ''
        choices = entry.choices
        if choices is None and entry.spec is None and entry.skill is not None:
            choices = skill_names_for_category(entry.skill)
            if choices is None:
                try:
                    cls = skill_class_by_name(entry.skill)
                    if len(_level_fields(cls)) > 1:
                        choices = [entry.skill]
                except ValueError:
                    pass
        reenlist_queued = any(
            isinstance(p, (PendingReenlist, PendingAssignmentChangeChoice, PendingAgingRoll, PendingMusterOut))
            for p in projection.pending_inputs
        )
        if choices:
            new_pending = PendingSkillTableChoice(
                id=f'{self.id}.0',
                instruction=f'Choose one skill: {", ".join(choices)}',
                options=choices,
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
                projection.pending_inputs.append(_survive_pending(career, assignment_name, self.id))


class CharacteristicChoiceEvent(EventBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'
    characteristic: Chars  # the chosen characteristic to apply the pending effect to
    amount: int = 1  # how much to reduce the characteristic by

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

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
            check_aging_crisis(projection, self.id)
        ):
            remaining = [
                p for p in projection.pending_inputs if isinstance(p, (PendingAgingChoice, PendingAgingChoiceMental))
            ]
            if not remaining:
                complete_aging(projection, self.id)


class ConnectionsRollEvent(EventBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind
    count: int  # final count (client applies the dice expression from the pending instruction)

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        for _ in range(self.count):
            projection.summary.connections.append(make_connection(self.connection_type))


class SkillRollEvent(EventBase):
    kind: Literal['skill_roll'] = 'skill_roll'
    context: str  # matches the pending kind — dispatch key for the career handler
    skill: AnySkill | Chars  # Chars for characteristic rolls (EDU, INT, etc.)
    modified_roll: int  # 2D + skill level + any other DMs already applied by the player

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.loader import get_skill_roll_handler

        career = projection.get_current_career()
        handler = get_skill_roll_handler(career.name, self.context)
        pending_count_before = len(projection.pending_inputs)
        if handler:
            handler(projection, self)
        if (
            len(projection.pending_inputs) == pending_count_before
            and projection.summary.current_career is not None
            and not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
        ):
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', self.id)
            )


class AgingRollEvent(EventBase):
    kind: Literal['aging_roll'] = 'aging_roll'
    roll: int  # 2D result (2-12) before the -term_count DM

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        if not (2 <= self.roll <= 12):
            raise ReplayError(f'Aging roll must be 2-12, got {self.roll}')
        effective = self.roll - projection.summary.term_count
        pending_idx = 0
        if effective >= 1:
            complete_aging(projection, self.id)
        elif effective == 0:
            projection.pending_inputs.append(
                PendingAgingChoice(
                    id=f'{self.id}.{pending_idx}',
                    instruction='Aging: choose STR, DEX, or END to reduce by 1',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
        elif effective == -1:
            for _ in range(2):
                projection.pending_inputs.append(
                    PendingAgingChoice(
                        id=f'{self.id}.{pending_idx}',
                        instruction='Aging: choose STR, DEX, or END to reduce by 1',
                        options=[Chars.STR, Chars.DEX, Chars.END],
                    )
                )
                pending_idx += 1
        elif effective == -2:
            for char in (Chars.STR, Chars.DEX, Chars.END):
                projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 1)
            if not check_aging_crisis(projection, self.id):
                complete_aging(projection, self.id)
        elif effective == -3:
            projection.pending_inputs.append(
                PendingAgingChoice(
                    id=f'{self.id}.{pending_idx}',
                    instruction='Aging: choose STR, DEX, or END to reduce by 2',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
            pending_idx += 1
            for _ in range(2):
                projection.pending_inputs.append(
                    PendingAgingChoice(
                        id=f'{self.id}.{pending_idx}',
                        instruction='Aging: choose STR, DEX, or END to reduce by 1',
                        options=[Chars.STR, Chars.DEX, Chars.END],
                    )
                )
                pending_idx += 1
        elif effective == -4:
            for _ in range(2):
                projection.pending_inputs.append(
                    PendingAgingChoice(
                        id=f'{self.id}.{pending_idx}',
                        instruction='Aging: choose STR, DEX, or END to reduce by 2',
                        options=[Chars.STR, Chars.DEX, Chars.END],
                    )
                )
                pending_idx += 1
            projection.pending_inputs.append(
                PendingAgingChoice(
                    id=f'{self.id}.{pending_idx}',
                    instruction='Aging: choose STR, DEX, or END to reduce by 1',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
        elif effective == -5:
            for char in (Chars.STR, Chars.DEX, Chars.END):
                projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 2)
            if not check_aging_crisis(projection, self.id):
                complete_aging(projection, self.id)
        else:  # <= -6
            for char in (Chars.STR, Chars.DEX, Chars.END):
                projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 2)
            if not check_aging_crisis(projection, self.id):
                projection.pending_inputs.append(
                    PendingAgingChoiceMental(
                        id=f'{self.id}.0',
                        instruction='Aging: choose INT or SOC to reduce by 1',
                        options=[Chars.INT, Chars.SOC],
                    )
                )


class InjuryTableEvent(EventBase):
    kind: Literal['injury_table'] = 'injury_table'
    roll: int  # 1D result (1-6) on the Injury table

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        if not (1 <= self.roll <= 6):
            raise ReplayError(f'Injury table roll must be 1-6, got {self.roll}')
        _apply_injury_table_result(projection, self.roll, self.id)


class DoubleInjuryTableEvent(EventBase):
    """Roll twice on the Injury table; the system takes the lower result."""

    kind: Literal['double_injury_table'] = 'double_injury_table'
    roll1: int  # first 1D result (1-6)
    roll2: int  # second 1D result (1-6)

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        for roll in (self.roll1, self.roll2):
            if not (1 <= roll <= 6):
                raise ReplayError(f'Double injury roll must be 1-6, got {roll}')
        _apply_injury_table_result(projection, min(self.roll1, self.roll2), self.id)


class LifeEventEvent(EventBase):
    kind: Literal['life_event'] = 'life_event'
    roll: int  # 2D result (2-12) on the Life Events table

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

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
                    id=f'{self.id}.0',
                    instruction='Roll 1D on Injury table (sickness/injury)',
                    options=['1', '2', '3', '4', '5', '6'],
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id, 1)
                )
        elif roll == 3:
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id)
                )
        elif roll == 4:
            projection.pending_inputs.append(
                PendingLifeEventChoice(
                    id=f'{self.id}.0',
                    roll=4,
                    instruction='Ending relationship: gain a rival or enemy?',
                    options=['rival', 'enemy'],
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id, 1)
                )
        elif roll == 5:
            projection.summary.connections.append(Ally(source='Life event: improved relationship'))
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id)
                )
        elif roll == 6:
            projection.summary.connections.append(Ally(source='Life event: new relationship'))
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id)
                )
        elif roll == 7:
            projection.summary.connections.append(Contact(source='Life event: new contact'))
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id)
                )
        elif roll == 8:
            projection.pending_inputs.append(
                PendingLifeEventChoice(
                    id=f'{self.id}.0',
                    roll=8,
                    instruction='Betrayal: gain a rival or enemy?',
                    options=['rival', 'enemy'],
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id, 1)
                )
        elif roll == 9:
            projection.scheduled_effects.append(
                ScheduledEffect(trigger='qualification', source_event_id=self.id, effect={'type': 'dm', 'amount': 2})
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id)
                )
        elif roll == 10:
            projection.scheduled_effects.append(
                ScheduledEffect(trigger='muster_out', source_event_id=self.id, effect={'type': 'dm', 'amount': 2})
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id)
                )
        elif roll == 11:
            projection.scheduled_effects.append(
                ScheduledEffect(
                    trigger='muster_out_reduce', source_event_id=self.id, effect={'type': 'reduce', 'value': 1}
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id, 0)
                )
        elif roll == 12:
            projection.pending_inputs.append(
                PendingLifeEventUnusual(
                    id=f'{self.id}.0',
                    instruction='Roll 1D on Unusual Events table',
                    options=['1', '2', '3', '4', '5', '6'],
                )
            )
            if in_career and career is not None:
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment or '', self.id, 1)
                )


class LifeEventUnusualEvent(EventBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'
    roll: int  # 1D result (1-6) on the Unusual Event sub-table

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        if not (1 <= self.roll <= 6):
            raise ReplayError(f'Life event unusual roll must be 1-6, got {self.roll}')
        if self.roll == 1:
            projection.summary.connections.append(Ally(source='Unusual event: useful ally'))
            projection.summary.narrative.append('Unusual event: gained a useful ally')
        elif self.roll == 2:
            projection.summary.connections.append(Contact(source='Unusual event: alien contact'))
            projection.grant_skill(skill_from_str(SpaceScience.name(), 1))
            projection.summary.narrative.append('Unusual event: alien encounter — gained contact and Space Science 1')
        else:
            projection.summary.narrative.append('Unusual event: something strange (no mechanical effect)')
        # advancement was pre-created by LifeEventEvent at self.id.1


class MusterOutEvent(EventBase):
    kind: Literal['muster_out'] = 'muster_out'
    table: Literal['cash', 'benefits']
    roll: int  # 1D result (1-6), DMs already applied by player

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.loader import load_careers

        career_name = projection.muster_out_career
        if career_name is None:
            raise ReplayError('No muster out career set')
        careers = load_careers()
        career = careers.get(career_name)
        if career is None or career.muster_out is None:
            raise ReplayError(f'Career {career_name!r} has no muster out table')
        effective_roll = max(1, min(7, self.roll))
        row = career.muster_out.rows.get(effective_roll)
        if row is None:
            raise ReplayError(f'No muster out row for roll {effective_roll}')
        if self.table == 'cash':
            if projection.summary.muster_out_cash_count >= 3:
                raise ReplayError('Cash may only be taken a maximum of 3 times')
            projection.summary.cash += row.cash
            projection.summary.muster_out_cash_count += 1
        else:
            for _ in range(row.count):
                _apply_muster_out_benefit(projection, row.benefit, self.id)
        remaining = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        if not remaining:
            projection.muster_out_career = None
            if not projection.summary.dead:
                queue_career_choice_indexed(projection, self.id, 0, 'Start a new career, or finish character creation')


class BenefitChoiceEvent(EventBase):
    """Resolves a PendingBenefitChoice by selecting one option from the list."""

    kind: Literal['benefit_choice'] = 'benefit_choice'
    choice_index: int  # 0-based index into PendingBenefitChoice.benefit_options

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        if not isinstance(fulfilled_pending, PendingBenefitChoice):
            raise ReplayError('BenefitChoiceEvent must fulfill a PendingBenefitChoice')
        options = fulfilled_pending.benefit_options
        if not (0 <= self.choice_index < len(options)):
            raise ReplayError(f'choice_index {self.choice_index} out of range for {len(options)} options')
        _apply_muster_out_benefit(projection, options[self.choice_index], self.id)


class AgingCrisisEvent(EventBase):
    kind: Literal['aging_crisis'] = 'aging_crisis'
    paid: bool
    medical_roll: int = 0  # 1D result for medical cost; 0 if not paying

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.loader import load_careers

        career_name = projection.summary.current_career or projection.muster_out_career
        careers = load_careers()
        career = careers.get(career_name) if career_name else None
        if self.paid:
            for char in list(projection.summary.characteristics.keys()):
                if projection.summary.characteristics[char] == 0:
                    projection.summary.characteristics[char] = 1
            if projection.pending_reenlist is True:
                projection.summary.term_count += 1
            projection.pending_reenlist = None
            projection.muster_out_career = None
            if career:
                muster_out_setup(projection, career, self.id, 0, clear_career=True)
            else:
                projection.clear_current_career()
        else:
            projection.summary.dead = True
            projection.clear_current_career()
            projection.muster_out_career = None
            projection.pending_reenlist = None


class AssignmentChangeChoiceEvent(EventBase):
    """End-of-term choice for careers that allow intra-career assignment changes.

    choice is one of: 'same' (reenlist same assignment), 'muster_out', or an assignment name
    to attempt. When an assignment name is given, qualification_roll must be provided; on
    failure a PendingReenlist is created for the character to choose same or muster out.
    """

    kind: Literal['assignment_change_choice'] = 'assignment_change_choice'
    choice: str  # 'same', 'muster_out', or target assignment name
    qualification_roll: int | None = None  # required when choice is an assignment name

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        career = projection.get_current_career()
        if self.choice == 'same':
            _start_new_career_term(projection, career, self.id)
        elif self.choice == 'muster_out':
            purge_career_pendings(projection)
            muster_out_setup(projection, career, self.id, 0, lose_current_term=False)
        else:
            new_assignment = career.assignment(self.choice)
            if new_assignment is None:
                raise ReplayError(f'Unknown assignment {self.choice!r} in career {career.name!r}')
            if self.qualification_roll is None:
                raise ReplayError(f'qualification_roll required when changing assignment to {self.choice!r}')
            char = career.qualification.characteristic
            target = career.qualification.target
            dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
            if self.qualification_roll + dm >= target:
                projection.summary.current_assignment = self.choice
                _start_new_career_term(projection, career, self.id)
            else:
                projection.pending_inputs.append(
                    PendingReenlist(
                        id=f'{self.id}.0',
                        instruction=(
                            f'Assignment change to {self.choice!r} failed — reenlist with '
                            f'{projection.summary.current_assignment!r} or muster out?'
                        ),
                        options=['true', 'false'],
                    )
                )


class FinishCreationEvent(EventBase):
    """Player chooses to end character creation after completing muster out."""

    kind: Literal['finish_creation'] = 'finish_creation'

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        pass  # fulfills the pending career choice; no further state change needed


class PreCareerEntryEvent(EventBase):
    """Attempt to enter pre-career education (university or military academy)."""

    kind: Literal['precareer_entry'] = 'precareer_entry'
    precareer: str
    roll: int  # 2D result for entry check (before characteristic DM)

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.precareers.loader import load_precareers

        precareer = load_precareers().get(self.precareer)
        if precareer is None:
            raise ReplayError(f'Unknown pre-career: {self.precareer!r}')
        if projection.summary.term_count >= 3:
            raise ReplayError('Pre-career education is only available in terms 1–3')
        if projection.summary.precareer_completed is not None:
            raise ReplayError('A character may only attend one pre-career')
        dm = 0
        if precareer.entry is not None:
            char_val = projection.summary.characteristics.get(precareer.entry.characteristic, 0)
            dm += characteristic_dm(char_val)
            term_dm = precareer.entry_term_dms.get(projection.summary.term_count + 1, 0)
            dm += term_dm
            if precareer.entry_soc_bonus_min is not None:
                soc = projection.summary.characteristics.get(Chars.SOC, 0)
                if soc >= precareer.entry_soc_bonus_min:
                    dm += precareer.entry_soc_bonus
            if self.roll == 2 or self.roll + dm < precareer.entry.target:
                queue_career_choice(projection, self.id, 'Pre-career entry failed — choose a career')
                return
        projection.summary.precareer = self.precareer
        projection.summary.term_count += 1
        projection.summary.age += 4
        pending_idx = 0
        pending_idx = precareer.apply_entry(projection, self, pending_idx)
        projection.pending_inputs.append(
            PendingPreCareerEvent(
                id=f'{self.id}.{pending_idx}',
                instruction='Roll 2D on Pre-career Events table',
            )
        )
        pending_idx += 1
        if precareer.graduation is not None:
            char = precareer.graduation.characteristic
            target = precareer.graduation.target
            dms_desc = ', '.join(f'{k}: DM{v:+d}' for k, v in precareer.graduation_dms.items())
            instruction = f'Graduation: {char} {target}+'
            if dms_desc:
                instruction += f' (DMs: {dms_desc})'
            projection.pending_inputs.append(
                PendingPreCareerGraduation(
                    id=f'{self.id}.{pending_idx}',
                    instruction=instruction,
                )
            )
        elif precareer.graduation_requirement is not None:
            projection.pending_inputs.append(
                PendingPreCareerGraduation(
                    id=f'{self.id}.{pending_idx}',
                    instruction=f'Graduation: {precareer.graduation_requirement}',
                )
            )


class PreCareerSkillChoiceEvent(EventBase):
    """Choose a skill gained during university pre-career; level is set by the pending input."""

    kind: Literal['precareer_skill_choice'] = 'precareer_skill_choice'
    skill: str  # specific skill name (may include specialisation, e.g. 'Science (biology)')

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:

        level = fulfilled_pending.level if isinstance(fulfilled_pending, PendingPreCareerSkillChoice) else 0
        skill_name, spec = parse_skill_spec_option(self.skill)
        if level == 0:
            projection.grant_skill(skill_from_str(skill_name, 0))
        else:
            projection.increment_skill(skill_name, spec)
        projection.summary.precareer_skills.append(self.skill)


class PreCareerEventEvent(EventBase):
    """Roll on the Pre-career Events table."""

    kind: Literal['precareer_event'] = 'precareer_event'
    roll: int  # 2D result (2-12)

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.careers.career_data import GainConnectionsRolledEffect, LifeEventEffect, SkillChoiceEffect
        from ceres.character.precareers.loader import load_precareers

        precareer_name = projection.summary.precareer
        if precareer_name is None:
            raise ReplayError('No active pre-career for pre-career event')
        precareer = load_precareers().get(precareer_name)
        if precareer is None:
            raise ReplayError(f'Unknown pre-career: {precareer_name!r}')
        term_event = precareer.events.get(self.roll)
        if term_event is None:
            raise ReplayError(f'No pre-career event entry for roll {self.roll}')
        projection.summary.narrative.append(f'Pre-career event ({precareer_name}): {term_event.text}')
        pending_idx = 0
        if self.roll in (3, 11):
            if self.roll == 11:
                projection.summary.problems.append(
                    f'Pre-career event 11: {term_event.text} '
                    'Consult rules: flee to Drifter or be drafted (1D: 1-3 Army, 4-5 Marine, 6 Navy). '
                    'You do not graduate this term. SOC 9+ may allow avoiding the draft.'
                )
            remaining_grad = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerGraduation)]
            for p in remaining_grad:
                projection.pending_inputs.remove(p)
            projection.summary.precareer_completed = precareer_name
            projection.summary.precareer = None
            queue_career_choice(projection, self.id, 'Pre-career ended (no graduation) — choose a career')
            return
        for effect in term_event.effects:
            if isinstance(effect, GainConnectionsRolledEffect):
                max_count = {'d3': 3, '1d3': 3, 'd6': 6}.get(effect.dice.lower(), 3)
                projection.pending_inputs.append(
                    PendingConnectionsRoll(
                        id=f'{self.id}.{pending_idx}',
                        connection_type=effect.connection_type,
                        instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s gained',
                        options=[str(i) for i in range(1, max_count + 1)],
                    )
                )
                pending_idx += 1
            elif isinstance(effect, SkillChoiceEffect):
                all_skills = sorted(
                    cls.name() for cls in _skill_classes(AnySkill) if cls.name() != 'Jack-of-All-Trades'
                )
                opts = effect.options or all_skills
                projection.pending_inputs.append(
                    PendingSkillChoice(
                        id=f'{self.id}.{pending_idx}',
                        instruction='Choose any skill at level 0',
                        options=opts,
                    )
                )
                pending_idx += 1
            elif isinstance(effect, LifeEventEffect):
                projection.pending_inputs.append(
                    PendingLifeEvent(
                        id=f'{self.id}.{pending_idx}',
                        instruction='Roll 2D on Life Events table',
                    )
                )
                pending_idx += 1
            else:
                _apply_simple_effect(projection, effect, source=term_event.text, source_event_id=self.id)
        if self.roll == 12:
            projection.summary.characteristics[Chars.SOC] = projection.summary.characteristics.get(Chars.SOC, 0) + 1
        elif self.roll == 2:
            projection.summary.problems.append(
                'Pre-career event 2: you may test your PSI and attempt to enter the Psion career '
                'in any subsequent term (apply manually).'
            )
        elif self.roll == 4:
            projection.summary.problems.append(
                'Pre-career event 4: roll SOC 8+ — success: gain Rival; failure: gain Enemy. '
                'Natural 2: also fail to graduate and must take Prisoner career next term. Apply manually.'
            )


class PreCareerGraduationEvent(EventBase):
    """Roll for graduation from pre-career education."""

    kind: Literal['precareer_graduation'] = 'precareer_graduation'
    roll: int  # 2D result for graduation check (before characteristic DM)

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        from ceres.character.precareers.loader import load_precareers

        precareer_name = projection.summary.precareer
        if precareer_name is None:
            raise ReplayError('No active pre-career for graduation')
        precareer = load_precareers().get(precareer_name)
        if precareer is None:
            raise ReplayError(f'Unknown pre-career: {precareer_name!r}')
        graduated = True
        honours = False
        if precareer.graduation is not None:
            dm = characteristic_dm(projection.summary.characteristics.get(precareer.graduation.characteristic, 0))
            for key, dm_val in precareer.graduation_dms.items():
                try:
                    char_name, threshold_str = key.split('_', 1)
                    threshold = int(threshold_str.rstrip('+'))
                    char = Chars(char_name)
                    if projection.summary.characteristics.get(char, 0) >= threshold:
                        dm += dm_val
                except ValueError, KeyError:
                    pass
            effective = self.roll + dm
            graduated = self.roll != 2 and effective >= precareer.graduation.target
            if precareer.honours_target is not None:
                honours = effective >= precareer.honours_target
        elif precareer.honours_target is not None:
            honours = self.roll >= precareer.honours_target
        pending_graduation_idx = 0
        if graduated:
            projection.summary.narrative.append(
                f'Graduated from {precareer_name}' + (' with honours!' if honours else '.')
            )
            pending_graduation_idx = precareer.apply_graduation(projection, self, honours)
        else:
            projection.summary.narrative.append(f'Did not graduate from {precareer_name}.')
            precareer.apply_failed_graduation(projection, self)
        projection.summary.precareer_completed = precareer_name
        projection.summary.precareer = None
        projection.summary.precareer_skills = []
        queue_career_choice_indexed(
            projection, self.id, pending_graduation_idx, 'Pre-career complete — choose a career'
        )


class ParoleRollEvent(EventBase):
    """Initial Parole Threshold roll when entering Prisoner career."""

    kind: Literal['parole_roll'] = 'parole_roll'
    roll: int  # 1D result (1-6); Parole Threshold = roll + 2

    def apply(self, projection: Any, fulfilled_pending: Any = None) -> None:
        pt = self.roll + 2
        projection.summary.parole_threshold = pt
        projection.summary.narrative.append(f'Prisoner: Parole Threshold set to {pt} (rolled {self.roll}+2)')


# ── Free functions (formerly CharacterProjection methods) ─────────────────────


def purge_career_pendings(projection: CharacterProjection) -> None:
    """Remove pending inputs that require an active career and can no longer be fulfilled.

    Called when a career ends (mishap or reenlist=False) to clear inputs that were queued
    by prior career-phase processing and are now orphaned.
    """
    projection.pending_inputs[:] = [
        p for p in projection.pending_inputs if not isinstance(p, _CAREER_PHASE_PENDING_TYPES)
    ]


def queue_career_choice_indexed(
    projection: CharacterProjection, event_id: int, idx: int, instruction: str = 'Choose a career'
) -> None:
    from ceres.character.careers.loader import selectable_careers

    if projection.forced_next_career:
        career_name = projection.forced_next_career
        projection.forced_next_career = None
        projection.pending_inputs.append(
            PendingCareerChoice(
                id=f'{event_id}.{idx}',
                instruction=f'Next career: {career_name} (mandatory)',
                options=[career_name],
            )
        )
    else:
        career_options = sorted(selectable_careers(projection).keys())
        projection.pending_inputs.append(
            PendingCareerChoice(
                id=f'{event_id}.{idx}',
                instruction=instruction,
                options=career_options,
            )
        )


def queue_career_choice(projection: CharacterProjection, event_id: int, instruction: str = 'Choose a career') -> None:
    queue_career_choice_indexed(projection, event_id, 0, instruction)


def queue_reenlist_or_aging(projection: CharacterProjection, event_id: int, idx: int) -> None:
    from ceres.character.careers.loader import load_careers

    if projection.prisoner_freed:
        projection.prisoner_freed = False
        projection.summary.age += 4
        career_name = projection.summary.current_career
        careers = load_careers()
        career = careers.get(career_name) if career_name else None
        if projection.summary.age >= 34:
            if career:
                projection.muster_out_career = career.name
            projection.pending_reenlist = False
            projection.clear_current_career()
            projection.pending_inputs.append(
                PendingAgingRoll(id=f'{event_id}.{idx}', instruction='Roll 2D on Aging table')
            )
        elif career:
            muster_out_setup(projection, career, event_id, idx, lose_current_term=False)
        return

    projection.summary.age += 4
    if projection.summary.age >= 34:
        projection.pending_inputs.append(PendingAgingRoll(id=f'{event_id}.{idx}', instruction='Roll 2D on Aging table'))
    else:
        career = projection.get_current_career() if projection.summary.current_career else None
        if career and career.allows_assignment_change and len(career.assignments) > 1:
            current = projection.summary.current_assignment or ''
            others = [a.name for a in career.assignments if a.name != current]
            options = ['same', *others]
            if career.name != 'Prisoner':
                options.append('muster_out')
            projection.pending_inputs.append(
                PendingAssignmentChangeChoice(
                    id=f'{event_id}.{idx}',
                    instruction='Reenlist same assignment, switch assignment, or muster out?',
                    options=options,
                )
            )
        else:
            projection.pending_inputs.append(
                PendingReenlist(
                    id=f'{event_id}.{idx}',
                    instruction='Reenlist or muster out?',
                    options=['true', 'false'],
                )
            )


def muster_out_setup(
    projection,
    career: CareerData,
    source_event_id: int,
    pending_idx: int = 0,
    lose_current_term: bool = False,
    clear_career: bool = True,
) -> int:
    roll_count = projection.summary.term_count + (projection.summary.rank or 0) // 2
    if lose_current_term:
        roll_count = max(0, roll_count - 1)
    reduce_effects = [se for se in projection.scheduled_effects if se.trigger == 'muster_out_reduce' and se.consume]
    for se in reduce_effects:
        roll_count = max(0, roll_count - se.effect.get('value', 1))
        projection.scheduled_effects.remove(se)
    add_effects = [se for se in projection.scheduled_effects if se.trigger == 'muster_out_add' and se.consume]
    for se in add_effects:
        roll_count += se.effect.get('value', 1)
        projection.scheduled_effects.remove(se)
    if clear_career:
        projection.clear_current_career()
    if roll_count > 0:
        projection.muster_out_career = career.name
        for _ in range(roll_count):
            projection.pending_inputs.append(
                PendingMusterOut(
                    id=f'{source_event_id}.{pending_idx}',
                    instruction='Muster out: choose cash or benefits table',
                    options=['cash', 'benefits'],
                )
            )
            pending_idx += 1
    else:
        queue_career_choice_indexed(projection, source_event_id, pending_idx)
        pending_idx += 1
    return pending_idx


def complete_aging(projection: CharacterProjection, source_event_id: int) -> None:
    from ceres.character.careers.loader import load_careers

    if projection.muster_out_career is not None:
        careers = load_careers()
        career = careers.get(projection.muster_out_career)
        lose = projection.pending_reenlist is None
        projection.muster_out_career = None
        if career:
            muster_out_setup(projection, career, source_event_id, 0, lose_current_term=lose, clear_career=False)
    else:
        career = projection.get_current_career() if projection.summary.current_career else None
        if career and career.allows_assignment_change and len(career.assignments) > 1:
            current = projection.summary.current_assignment or ''
            others = [a.name for a in career.assignments if a.name != current]
            projection.pending_inputs.append(
                PendingAssignmentChangeChoice(
                    id=f'{source_event_id}.0',
                    instruction='Reenlist same assignment, switch assignment, or muster out?',
                    options=['same', *others, 'muster_out'],
                )
            )
        else:
            projection.pending_inputs.append(
                PendingReenlist(
                    id=f'{source_event_id}.0',
                    instruction='Reenlist or muster out?',
                    options=['true', 'false'],
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
                id=f'{source_event_id}.crisis',
                instruction='Aging crisis: pay for medical care or die?',
                options=['pay', 'die'],
            )
        )
        return True
    return False


def career_progress_pending(
    projection, career: CareerData, event_id: int, pending_idx: int = 0
) -> PendingAdvancement | PendingCommissionChoice:
    if career.can_attempt_commission(projection):
        commission = career.commission
        if commission is None:
            raise ReplayError(f'{career.name} can attempt commission without commission rules')
        return PendingCommissionChoice(
            id=f'{event_id}.{pending_idx}',
            instruction=f'Attempt commission ({commission.characteristic} {commission.target}+) or roll advancement?',
            options=['attempt', 'skip'],
        )
    assignment_name = projection.summary.current_assignment or ''
    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r}')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    return PendingAdvancement(id=f'{event_id}.{pending_idx}', instruction=f'Advancement: {char} {target}+')


# ── Skill-choice option builder ───────────────────────────────────────────────


def _build_skill_select_options(
    projection: CharacterProjection,
    options: list[str],
    level: int | None,
) -> list[tuple[str, str]]:
    """Build (display_label, form_value) pairs for skill-choice pending inputs."""
    results: list[tuple[str, str]] = []
    for opt in options:
        if opt in _NON_SKILL_OPTION_LABELS:
            results.append((_NON_SKILL_OPTION_LABELS[opt], opt))
            continue
        try:
            skill_cls = skill_class_by_name(opt)
        except ValueError:
            continue
        if level == 0:
            skill = cast(AnySkill, skill_cls())
            results.append((opt, _skill_adapter.dump_json(skill).decode()))
        else:
            choices = projection.skill_choices([skill_cls], level)
            for skill in choices:
                label = opt
                fields = _level_fields(skill_cls)
                if len(fields) > 1:
                    for fname, sname in zip(fields, skill_cls.specialities(), strict=False):
                        given = getattr(skill, fname).value
                        if given > 0:
                            label = f'{opt} ({sname})'
                            break
                results.append((label, _skill_adapter.dump_json(skill).decode()))
    return results


# ── Pending-input types ───────────────────────────────────────────────────────


class PendingUcp(PendingInputBase):
    kind: Literal['ucp'] = 'ucp'
    stat_names: list[str] = Field(default_factory=lambda: [s.value for s in UCP_STATS])

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        sophont = projection.summary.sophont
        n = len(sophont.ucp_stats) if sophont is not None else 6
        ucp = ''.join(f'{_roll2d(rng):X}' for _ in range(n))
        return UcpEvent(ucp=ucp, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        ucp = ''.join(f'{form_int(form, stat, 0):X}' for stat in self.stat_names)
        return UcpEvent(ucp=ucp, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            NumberEntry(
                name=stat,
                label=stat,
                default=projection.summary.characteristics.get(Chars(stat), 7),
                min=1,
                max=15,
            )
            for stat in self.stat_names
        ]


class PendingBackgroundSkills(PendingInputBase):
    kind: Literal['background_skills'] = 'background_skills'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        m = _CHOOSE_COUNT_RE.search(self.instruction)
        count = int(m.group(1)) if m else 3
        shuffled = list(self.options)
        rng.shuffle(shuffled)
        skills: list[AnySkill] = []
        for name in shuffled:
            if len(skills) >= count:
                break
            try:
                cls = skill_class_by_name(name)
                skills.append(cast(AnySkill, cls()))
            except ValueError:
                pass
        return BackgroundSkillsEvent(skills=skills, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        raw = form.getlist('skill')
        skills = [_skill_adapter.validate_json(j) for j in raw]
        return BackgroundSkillsEvent(skills=skills, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        m = _CHOOSE_COUNT_RE.search(self.instruction)
        count = int(m.group(1)) if m else 1
        options: list[tuple[str, str]] = []
        for opt in self.options:
            try:
                cls = skill_class_by_name(opt)
            except ValueError:
                continue
            skill = cast(AnySkill, cls())
            options.append((opt, _skill_adapter.dump_json(skill).decode()))
        return [Select(name='skill', label='Skills', options=options, min_select=count, max_select=count)]


class PendingCareerChoice(PendingInputBase):
    kind: Literal['career_choice'] = 'career_choice'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        if projection.summary.term_count >= ctx.max_terms:
            return FinishCreationEvent(fulfills=self.id)
        available = self.options or sorted(ctx.careers.keys())
        career_data = None
        if ctx.career in available:
            career_data = ctx.careers.get(ctx.career)
        if career_data is None:
            from ceres.character.careers.loader import load_careers as _load_careers

            all_careers = _load_careers()
            chosen_name = rng.choice(available) if available else rng.choice(sorted(ctx.careers.keys()))
            career_data = all_careers.get(chosen_name) or ctx.careers.get(chosen_name)
        if career_data is None:
            career_data = ctx.careers[rng.choice(sorted(ctx.careers.keys()))]
        if ctx.assignment and any(a.name == ctx.assignment for a in career_data.assignments):
            assignment = ctx.assignment
        else:
            assignment = rng.choice([a.name for a in career_data.assignments])
        return CareerEvent(
            career=career_data.name,
            assignment=assignment,
            qualification_roll=12,
            fulfills=self.id,
        )

    def event_from_form(self, form: Any) -> AnyEvent:
        kind = form_str(form, 'kind', '')
        if kind == 'finish_creation':
            return FinishCreationEvent(fulfills=self.id)
        if kind == 'precareer_entry':
            precareer = form_str(form, 'precareer', 'University')
            roll = form_int(form, 'roll', 7)
            return PreCareerEntryEvent(precareer=precareer, roll=roll, fulfills=self.id)
        career = form_str(form, 'career')
        assignment = form_str(form, 'assignment')
        roll = form_int(form, 'roll', 2)
        return CareerEvent(career=career, assignment=assignment, qualification_roll=roll, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        # Career choice uses a complex HTMX-driven form; no generic InputSpec
        return []


class PendingDraftChoice(PendingInputBase):
    kind: Literal['draft_choice'] = 'draft_choice'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        draft_careers = [career for career in ctx.careers.values() if career.does_draft()]
        career = rng.choice(draft_careers)
        return DraftEvent(career=career.name, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        choice = form_str(form, 'choice', 'drifter')
        if choice == 'draft':
            roll = form_int(form, 'roll', 1)
            _DRAFT_ORDER = ['Navy', 'Army', 'Marines', 'Merchant', 'Scout', 'Agent']
            career_name = _DRAFT_ORDER[max(0, min(roll, len(_DRAFT_ORDER)) - 1)]
            return DraftEvent(career=career_name, fulfills=self.id)
        assignment = form_str(form, 'assignment', 'Wanderer')
        return CareerEvent(career='Drifter', assignment=assignment, qualification_roll=2, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        # Draft choice uses toggle JS panels; no generic InputSpec
        return []


class PendingDraftAssignmentChoice(PendingInputBase):
    kind: Literal['draft_assignment_choice'] = 'draft_assignment_choice'
    career: str

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return DraftAssignmentEvent(
            career=self.career,
            assignment=rng.choice(self.options),
            fulfills=self.id,
        )

    def event_from_form(self, form: Any) -> AnyEvent:
        return DraftAssignmentEvent(
            career=self.career,
            assignment=form_str(form, 'assignment'),
            fulfills=self.id,
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(opt, opt) for opt in self.options]
        return [
            Reference(name='career', value=self.career),
            Select(name='assignment', label='Assignment', options=options),
        ]


class PendingSurvive(PendingInputBase):
    kind: Literal['survive'] = 'survive'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return SurviveEvent(roll=_roll2d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return SurviveEvent(roll=form_int(form, 'roll', 2), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', default=7, min=2, max=12)]


class PendingTermEvent(PendingInputBase):
    kind: Literal['term_event'] = 'term_event'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return TermEventEvent(roll=_roll2d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return TermEventEvent(roll=form_int(form, 'roll', 2), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', default=7, min=2, max=12)]


class PendingMishap(PendingInputBase):
    kind: Literal['mishap'] = 'mishap'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return MishapEvent(roll=_roll1d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return MishapEvent(roll=form_int(form, 'roll', 1), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', default=3, min=1, max=6)]


class PendingAdvancement(PendingInputBase):
    kind: Literal['advancement'] = 'advancement'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return AdvancementEvent(roll=_roll2d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return AdvancementEvent(roll=form_int(form, 'roll', 2), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', default=7, min=2, max=12)]


class PendingCommissionChoice(PendingInputBase):
    kind: Literal['commission_choice'] = 'commission_choice'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return CommissionEvent(attempt=False, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        choice = form_str(form, 'choice', 'skip')
        if choice == 'attempt':
            return CommissionEvent(attempt=True, roll=form_int(form, 'roll', 7), fulfills=self.id)
        return CommissionEvent(attempt=False, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(
                name='choice',
                label='Commission',
                options=[('Attempt commission', 'attempt'), ('Skip (roll advancement)', 'skip')],
            ),
            NumberEntry(name='roll', label='Commission roll (2D, if attempting)', default=7, min=2, max=12),
        ]


class PendingSkillTable(PendingInputBase):
    kind: Literal['skill_table'] = 'skill_table'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        table = rng.choice(self.options) if self.options else 'service_skills'
        return SkillTableEvent(table=table, roll=_roll1d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return SkillTableEvent(
            table=form_str(form, 'table'),
            roll=form_int(form, 'roll', 1),
            fulfills=self.id,
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        table_options = [(opt.replace('_', ' ').title(), opt) for opt in self.options]
        return [
            Select(name='table', label='Table', options=table_options),
            NumberEntry(name='roll', label='1D roll (1–6)', default=3, min=1, max=6),
        ]


class PendingReenlist(PendingInputBase):
    kind: Literal['reenlist'] = 'reenlist'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return ReenlistEvent(reenlist=projection.summary.term_count < ctx.max_terms, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        reenlist = form_str(form, 'reenlist', 'false').lower() in ('true', '1', 'yes')
        return ReenlistEvent(reenlist=reenlist, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        # Reenlist uses big inline buttons; no generic InputSpec
        return []


class PendingAssignmentChangeChoice(PendingInputBase):
    """End-of-term choice for careers that allow intra-career assignment changes.

    options: ['same', 'muster_out', *other_assignment_names]
    Resolved by AssignmentChangeChoiceEvent.
    """

    kind: Literal['assignment_change_choice'] = 'assignment_change_choice'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        if projection.summary.term_count < ctx.max_terms:
            return AssignmentChangeChoiceEvent(choice='same', fulfills=self.id)
        if 'muster_out' in self.options:
            return AssignmentChangeChoiceEvent(choice='muster_out', fulfills=self.id)
        return AssignmentChangeChoiceEvent(choice='same', fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        choice = form_str(form, 'choice', 'muster_out')
        roll = form_int(form, 'roll', 7) if choice not in ('same', 'muster_out') else None
        return AssignmentChangeChoiceEvent(choice=choice, qualification_roll=roll, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        labels = {'same': 'Stay in current assignment', 'muster_out': 'Muster out'}
        options = [(labels.get(opt, opt), opt) for opt in self.options]
        return [
            Select(name='choice', label='Assignment choice', options=options),
            NumberEntry(
                name='roll', label='Qualification roll (2D, if switching assignment)', default=7, min=2, max=12
            ),
        ]


class PendingMusterOut(PendingInputBase):
    kind: Literal['muster_out'] = 'muster_out'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        tables: list[Literal['cash', 'benefits']] = ['cash', 'benefits']
        return MusterOutEvent(table=rng.choice(tables), roll=_roll1d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        from typing import Literal as _Literal, cast as _cast

        table = _cast(
            _Literal['cash', 'benefits'],
            literal(form_str(form, 'table', 'benefits'), ('cash', 'benefits'), 'benefits'),
        )
        return MusterOutEvent(table=table, roll=form_int(form, 'roll', 1), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        table_options = [(opt.title(), opt) for opt in self.options]
        return [
            Select(name='table', label='Table', options=table_options),
            NumberEntry(name='roll', label='1D roll (1–6, apply DMs first)', default=3, min=1, max=7),
        ]


class PendingSkillChoice(PendingInputBase):
    kind: Literal['skill_choice'] = 'skill_choice'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        skill = projection._pick_skill_auto(self.options, rng, None)
        if skill is not None:
            return SkillChoiceEvent(skill=skill, fulfills=self.id)
        return AdvancementDmChoiceEvent(fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        skill_str = form_str(form, 'skill', '{}')
        if skill_str == 'advancement_dm_4':
            return AdvancementDmChoiceEvent(fulfills=self.id)
        skill = _skill_adapter.validate_json(skill_str)
        return SkillChoiceEvent(skill=skill, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, None)
        return [Select(name='skill', label='Choose a skill', options=options)]


class PendingInitialTrainingChoice(PendingInputBase):
    kind: Literal['initial_training_choice'] = 'initial_training_choice'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        skill = projection._pick_skill_auto(self.options, rng, 0)
        if skill is not None:
            return SkillChoiceEvent(skill=skill, fulfills=self.id)
        return AdvancementDmChoiceEvent(fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        skill_str = form_str(form, 'skill', '{}')
        if skill_str == 'advancement_dm_4':
            return AdvancementDmChoiceEvent(fulfills=self.id)
        skill = _skill_adapter.validate_json(skill_str)
        return SkillChoiceEvent(skill=skill, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, 0)
        return [Select(name='skill', label='Choose a skill', options=options)]


class PendingSkillTableChoice(PendingInputBase):
    kind: Literal['skill_table_choice'] = 'skill_table_choice'
    reenlist_queued: bool = False  # True when reenlist/aging already queued (end-of-term path)

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        skill = projection._pick_skill_auto(self.options, rng, None)
        if skill is not None:
            return SkillChoiceEvent(skill=skill, fulfills=self.id)
        return AdvancementDmChoiceEvent(fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        skill_str = form_str(form, 'skill', '{}')
        if skill_str == 'advancement_dm_4':
            return AdvancementDmChoiceEvent(fulfills=self.id)
        skill = _skill_adapter.validate_json(skill_str)
        return SkillChoiceEvent(skill=skill, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, None)
        return [Select(name='skill', label='Choose a skill', options=options)]


class PendingRankBonusChoice(PendingInputBase):
    kind: Literal['rank_bonus_choice'] = 'rank_bonus_choice'
    level: int

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        skill = projection._pick_skill_auto(self.options, rng, self.level)
        if skill is not None:
            return SkillChoiceEvent(skill=skill, fulfills=self.id)
        return AdvancementDmChoiceEvent(fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        skill_str = form_str(form, 'skill', '{}')
        if skill_str == 'advancement_dm_4':
            return AdvancementDmChoiceEvent(fulfills=self.id)
        skill = _skill_adapter.validate_json(skill_str)
        return SkillChoiceEvent(skill=skill, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, self.level)
        return [Select(name='skill', label='Choose a skill', options=options)]


class PendingCharacteristicChoice(PendingInputBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        char = rng.choice(self.options) if self.options else 'STR'
        return CharacteristicChoiceEvent(characteristic=Chars(char), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return CharacteristicChoiceEvent(
            characteristic=Chars(form_str(form, 'characteristic', Chars.STR)),
            fulfills=self.id,
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(opt, opt) for opt in self.options]
        return [Select(name='characteristic', label='Characteristic', options=options)]


class PendingNearlyKilled(PendingInputBase):
    kind: Literal['nearly_killed'] = 'nearly_killed'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return InjuryTableEvent(roll=_roll1d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return InjuryTableEvent(roll=form_int(form, 'roll', 1), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', default=3, min=1, max=6)]


class PendingInjuryTable(PendingInputBase):
    kind: Literal['injury_table'] = 'injury_table'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return InjuryTableEvent(roll=_roll1d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return InjuryTableEvent(roll=form_int(form, 'roll', 1), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', default=3, min=1, max=6)]


class PendingDoubleInjuryRoll(PendingInputBase):
    """Roll 1D twice; system takes the lower result and applies Injury table."""

    kind: Literal['double_injury_roll'] = 'double_injury_roll'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return DoubleInjuryTableEvent(roll1=_roll1d(rng), roll2=_roll1d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return DoubleInjuryTableEvent(
            roll1=form_int(form, 'roll1', 1),
            roll2=form_int(form, 'roll2', 1),
            fulfills=self.id,
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            NumberEntry(name='roll1', label='First 1D roll (1–6)', default=3, min=1, max=6),
            NumberEntry(name='roll2', label='Second 1D roll (1–6)', default=3, min=1, max=6),
        ]


class PendingBenefitChoice(PendingInputBase):
    """Player must pick one option from a ChoiceBenefit muster-out row."""

    kind: Literal['benefit_choice_pending'] = 'benefit_choice_pending'
    benefit_options: list[AnyBenefit]

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return BenefitChoiceEvent(
            choice_index=rng.randint(0, len(self.benefit_options) - 1),
            fulfills=self.id,
        )

    def event_from_form(self, form: Any) -> AnyEvent:
        return BenefitChoiceEvent(choice_index=form_int(form, 'choice_index', 0), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(opt, str(i)) for i, opt in enumerate(self.options)]
        return [Select(name='choice_index', label='Choose benefit', options=options)]


class PendingAgingRoll(PendingInputBase):
    kind: Literal['aging_roll'] = 'aging_roll'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return AgingRollEvent(roll=_roll2d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return AgingRollEvent(roll=form_int(form, 'roll', 2), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', default=7, min=2, max=12)]


class PendingAgingChoice(PendingInputBase):
    kind: Literal['aging_choice'] = 'aging_choice'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        char = rng.choice(self.options) if self.options else 'STR'
        return CharacteristicChoiceEvent(characteristic=Chars(char), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return CharacteristicChoiceEvent(
            characteristic=Chars(form_str(form, 'characteristic', Chars.STR)),
            fulfills=self.id,
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(opt, opt) for opt in self.options]
        return [Select(name='characteristic', label='Characteristic', options=options)]


class PendingAgingChoiceMental(PendingInputBase):
    kind: Literal['aging_choice_mental'] = 'aging_choice_mental'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        char = rng.choice(self.options) if self.options else 'STR'
        return CharacteristicChoiceEvent(characteristic=Chars(char), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return CharacteristicChoiceEvent(
            characteristic=Chars(form_str(form, 'characteristic', Chars.STR)),
            fulfills=self.id,
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(opt, opt) for opt in self.options]
        return [Select(name='characteristic', label='Characteristic', options=options)]


class PendingAgingCrisis(PendingInputBase):
    kind: Literal['aging_crisis'] = 'aging_crisis'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return AgingCrisisEvent(paid=False, medical_roll=0, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        paid = form_str(form, 'paid', 'false').lower() in ('true', '1', 'yes')
        medical_roll = form_int(form, 'medical_roll', 0)
        return AgingCrisisEvent(paid=paid, medical_roll=medical_roll, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(
                name='paid',
                label='Medical care',
                options=[('Pay for medical care', 'true'), ('Cannot afford / decline', 'false')],
            ),
            NumberEntry(name='medical_roll', label='Medical roll (1D, if paying)', default=3, min=0, max=6),
        ]


class PendingLifeEvent(PendingInputBase):
    kind: Literal['life_event'] = 'life_event'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return LifeEventEvent(roll=_roll2d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return LifeEventEvent(roll=form_int(form, 'roll', 2), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', default=7, min=2, max=12)]


class PendingLifeEventChoice(PendingInputBase):
    """Life event that requires a connection kind choice (rolls 4 and 8)."""

    kind: Literal['life_event_choice'] = 'life_event_choice'
    roll: int

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return ConnectionKindChoiceEvent(connection_kind=rng.choice(list(ConnectionKind)), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        raw_ck = literal(form_str(form, 'connection_kind', 'rival'), tuple(ConnectionKind), 'rival')
        return ConnectionKindChoiceEvent(connection_kind=ConnectionKind(raw_ck), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [('Rival', 'rival'), ('Enemy', 'enemy')]
        return [Select(name='connection_kind', label='Connection type', options=options)]


class PendingLifeEventUnusual(PendingInputBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return LifeEventUnusualEvent(roll=_roll1d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return LifeEventUnusualEvent(roll=form_int(form, 'roll', 1), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', default=3, min=1, max=6)]


class PendingConnectionsRoll(PendingInputBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind = ConnectionKind.CONTACT

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return ConnectionsRollEvent(
            connection_type=self.connection_type,
            count=_roll1d(rng),
            fulfills=self.id,
        )

    def event_from_form(self, form: Any) -> AnyEvent:
        raw_ct = literal(form_str(form, 'connection_type', 'contact'), tuple(ConnectionKind), 'contact')
        count = form_int(form, 'count', 1)
        return ConnectionsRollEvent(connection_type=ConnectionKind(raw_ct), count=count, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        count_options = (
            [(str(opt), opt) for opt in self.options] if self.options else [(str(i), str(i)) for i in range(1, 7)]
        )
        return [
            Reference(name='connection_type', value=self.connection_type.value),
            Select(name='count', label='Count', options=count_options),
        ]


class PendingCareerEvent(PendingInputBase):
    """Career-specific event requiring player input; career+roll identifies the exact event."""

    kind: Literal['career_event'] = 'career_event'
    career: str
    roll: int

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        context = f'{self.career.lower()}_event_{self.roll}'
        choice = rng.choice(list(self.options)) if self.options else ''
        return CareerChoiceEvent(context=context, choice=choice, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        context = f'{self.career.lower()}_event_{self.roll}'
        choice = form_str(form, 'choice', '')
        return CareerChoiceEvent(context=context, choice=choice, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        # Career event uses inline submit buttons; choice is submitted via button value
        return []


class PendingCareerMishap(PendingInputBase):
    """Career-specific mishap requiring player input; career+roll identifies the exact mishap."""

    kind: Literal['career_mishap'] = 'career_mishap'
    career: str
    roll: int

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        context = f'{self.career.lower()}_mishap_{self.roll}'
        choice = rng.choice(list(self.options)) if self.options else ''
        return CareerChoiceEvent(context=context, choice=choice, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        context = f'{self.career.lower()}_mishap_{self.roll}'
        choice = form_str(form, 'choice', '')
        return CareerChoiceEvent(context=context, choice=choice, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        # Career mishap uses inline submit buttons; choice is submitted via button value
        return []


class PendingCareerSkillChoice(PendingInputBase):
    """Skill choice triggered by a career event or mishap."""

    kind: Literal['career_skill_choice'] = 'career_skill_choice'
    career: str
    roll: int
    mishap: bool = False
    advancement_precreated: bool = False

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        skill = projection._pick_skill_auto(self.options, rng, None)
        if skill is not None:
            return SkillChoiceEvent(skill=skill, fulfills=self.id)
        return AdvancementDmChoiceEvent(fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        skill_str = form_str(form, 'skill', '{}')
        if skill_str == 'advancement_dm_4':
            return AdvancementDmChoiceEvent(fulfills=self.id)
        skill = _skill_adapter.validate_json(skill_str)
        return SkillChoiceEvent(skill=skill, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = _build_skill_select_options(projection, self.options, None)
        return [Select(name='skill', label='Choose a skill', options=options)]


class PendingCareerSkillRoll(PendingInputBase):
    """Skill roll required by a specific career event; context matches SkillRollEvent.context."""

    kind: Literal['career_skill_roll'] = 'career_skill_roll'
    career: str
    roll: int
    context: str

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        skill_str = rng.choice(self.options) if self.options else 'Admin'
        try:
            auto_skill: AnySkill | Chars = Chars(skill_str)
        except ValueError:
            auto_skill = cast(AnySkill, skill_class_by_name(skill_str)())
        return SkillRollEvent(context=self.context, skill=auto_skill, modified_roll=_roll2d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        skill_str = form_str(form, 'skill')
        modified_roll = form_int(form, 'modified_roll', 8)
        try:
            skill: AnySkill | Chars = Chars(skill_str)
        except ValueError:
            skill = _skill_adapter.validate_python({'type': skill_str})
        return SkillRollEvent(context=self.context, skill=skill, modified_roll=modified_roll, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        skill_options = [(opt, opt) for opt in self.options]
        return [
            Select(name='skill', label='Skill to roll', options=skill_options),
            NumberEntry(name='modified_roll', label='Modified roll (2D + skill level + DMs)', default=8, min=2, max=20),
        ]


class PendingPreCareerSkillChoice(PendingInputBase):
    """University: choose one skill at the given level (0 or 1) from the pre-career skill list."""

    kind: Literal['precareer_skill_choice'] = 'precareer_skill_choice'
    level: int

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        skill_name = rng.choice(self.options) if self.options else 'Admin'
        return PreCareerSkillChoiceEvent(skill=skill_name, fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        skill = form_str(form, 'skill')
        return PreCareerSkillChoiceEvent(skill=skill, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(opt, opt) for opt in self.options]
        return [Select(name='skill', label='Choose a skill', options=options)]


class PendingPreCareerEvent(PendingInputBase):
    """Roll 2D on the Pre-career Events table."""

    kind: Literal['precareer_event'] = 'precareer_event'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return PreCareerEventEvent(roll=_roll2d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return PreCareerEventEvent(roll=form_int(form, 'roll', 7), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', default=7, min=2, max=12)]


class PendingPreCareerGraduation(PendingInputBase):
    """Roll 2D for graduation from pre-career education."""

    kind: Literal['precareer_graduation'] = 'precareer_graduation'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return PreCareerGraduationEvent(roll=_roll2d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return PreCareerGraduationEvent(roll=form_int(form, 'roll', 7), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll (2–12)', default=7, min=2, max=12)]


class PendingParoleRoll(PendingInputBase):
    """Roll 1D to determine initial Parole Threshold when entering Prisoner career."""

    kind: Literal['parole_roll'] = 'parole_roll'

    def auto_event(self, projection: CharacterProjection, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        return ParoleRollEvent(roll=_roll1d(rng), fulfills=self.id)

    def event_from_form(self, form: Any) -> AnyEvent:
        return ParoleRollEvent(roll=form_int(form, 'roll', 1), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='1D roll (1–6)', default=3, min=1, max=6)]


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
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
)
type AnyPending = Annotated[
    PendingUcp
    | PendingBackgroundSkills
    | PendingCareerChoice
    | PendingDraftChoice
    | PendingDraftAssignmentChoice
    | PendingSurvive
    | PendingTermEvent
    | PendingMishap
    | PendingAdvancement
    | PendingCommissionChoice
    | PendingSkillTable
    | PendingReenlist
    | PendingAssignmentChangeChoice
    | PendingMusterOut
    | PendingSkillChoice
    | PendingInitialTrainingChoice
    | PendingSkillTableChoice
    | PendingRankBonusChoice
    | PendingCharacteristicChoice
    | PendingNearlyKilled
    | PendingInjuryTable
    | PendingDoubleInjuryRoll
    | PendingBenefitChoice
    | PendingAgingRoll
    | PendingAgingChoice
    | PendingAgingChoiceMental
    | PendingAgingCrisis
    | PendingLifeEvent
    | PendingLifeEventChoice
    | PendingLifeEventUnusual
    | PendingConnectionsRoll
    | PendingCareerEvent
    | PendingCareerMishap
    | PendingCareerSkillChoice
    | PendingCareerSkillRoll
    | PendingPreCareerSkillChoice
    | PendingPreCareerEvent
    | PendingPreCareerGraduation
    | PendingParoleRoll,
    Field(discriminator='kind'),
]


type AnyEvent = Annotated[
    AgingCrisisEvent
    | AgingRollEvent
    | AdvancementDmChoiceEvent
    | CharacterStartedEvent
    | UcpEvent
    | BackgroundSkillsEvent
    | CareerEvent
    | DraftEvent
    | DraftAssignmentEvent
    | SurviveEvent
    | MishapEvent
    | TermEventEvent
    | SkillChoiceEvent
    | AdvancementEvent
    | CommissionEvent
    | ReenlistEvent
    | SkillTableEvent
    | CharacteristicChoiceEvent
    | ConnectionsRollEvent
    | ConnectionKindChoiceEvent
    | SkillRollEvent
    | InjuryTableEvent
    | DoubleInjuryTableEvent
    | LifeEventEvent
    | LifeEventUnusualEvent
    | MusterOutEvent
    | BenefitChoiceEvent
    | CareerChoiceEvent
    | AssignmentChangeChoiceEvent
    | FinishCreationEvent
    | PreCareerEntryEvent
    | PreCareerSkillChoiceEvent
    | PreCareerEventEvent
    | PreCareerGraduationEvent
    | ParoleRollEvent,
    Field(discriminator='kind'),
]


__all__ = [
    'AdvancementDmChoiceEvent',
    'AdvancementEvent',
    'AgingCrisisEvent',
    'AgingRollEvent',
    'AnyEvent',
    'AnyPending',
    'AssignmentChangeChoiceEvent',
    'AutoFillContext',
    'BackgroundSkillsEvent',
    'BenefitChoiceEvent',
    'CareerChoiceEvent',
    'CareerEvent',
    'CareerTerm',
    'CharacterProjection',
    'CharacterStartedEvent',
    'CharacterSummary',
    'CharacteristicChoiceEvent',
    'CommissionEvent',
    'ConnectionKind',
    'ConnectionKindChoiceEvent',
    'ConnectionsRollEvent',
    'DoubleInjuryTableEvent',
    'DraftAssignmentEvent',
    'DraftEvent',
    'EventBase',
    'FinishCreationEvent',
    'InjuryTableEvent',
    'LifeEventEvent',
    'LifeEventUnusualEvent',
    'MishapEvent',
    'MusterOutEvent',
    'ParoleRollEvent',
    'PendingAdvancement',
    'PendingAgingChoice',
    'PendingAgingChoiceMental',
    'PendingAgingCrisis',
    'PendingAgingRoll',
    'PendingAssignmentChangeChoice',
    'PendingBackgroundSkills',
    'PendingBenefitChoice',
    'PendingCareerChoice',
    'PendingCareerEvent',
    'PendingCareerMishap',
    'PendingCareerSkillChoice',
    'PendingCareerSkillRoll',
    'PendingCharacteristicChoice',
    'PendingCommissionChoice',
    'PendingConnectionsRoll',
    'PendingDoubleInjuryRoll',
    'PendingDraftAssignmentChoice',
    'PendingDraftChoice',
    'PendingInitialTrainingChoice',
    'PendingInjuryTable',
    'PendingInputBase',
    'PendingLifeEvent',
    'PendingLifeEventChoice',
    'PendingLifeEventUnusual',
    'PendingMishap',
    'PendingMusterOut',
    'PendingNearlyKilled',
    'PendingParoleRoll',
    'PendingPreCareerEvent',
    'PendingPreCareerGraduation',
    'PendingPreCareerSkillChoice',
    'PendingRankBonusChoice',
    'PendingReenlist',
    'PendingSkillChoice',
    'PendingSkillTable',
    'PendingSkillTableChoice',
    'PendingSurvive',
    'PendingTermEvent',
    'PendingUcp',
    'PreCareerEntryEvent',
    'PreCareerEventEvent',
    'PreCareerGraduationEvent',
    'PreCareerSkillChoiceEvent',
    'ReenlistEvent',
    'ReplayError',
    'ScheduledEffect',
    'SkillChoiceEvent',
    'SkillRollEvent',
    'SkillTableEvent',
    'SurviveEvent',
    'TermEventEvent',
    'UcpEvent',
    'career_progress_pending',
    'check_aging_crisis',
    'complete_aging',
    'muster_out_setup',
    'purge_career_pendings',
    'queue_career_choice',
    'queue_career_choice_indexed',
    'queue_reenlist_or_aging',
]
