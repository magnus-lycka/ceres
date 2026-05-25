from collections.abc import Sequence
from typing import Literal, cast

from ceres.character.careers.career_data import CareerData, RankBonus, SkillTableEntry
from ceres.character.careers.loader import (
    get_choice_handler,
    get_effect_handler,
    get_skill_roll_handler,
    load_careers,
)
from ceres.character.characteristics import UCP_STATS, Chars
from ceres.character.events import (
    AdvancementDmChoiceEvent,
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    AnyEvent,
    BackgroundSkillsEvent,
    BenefitChoiceEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    ConnectionKindChoiceEvent,
    ConnectionsRollEvent,
    DoubleInjuryTableEvent,
    InjuryTableEvent,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.projection import (
    Ally,
    AnyPending,
    CharacterProjection,
    CharacterSummary,
    Contact,
    PendingAdvancement,
    PendingAgingChoice,
    PendingAgingChoiceMental,
    PendingAgingCrisis,
    PendingAgingRoll,
    PendingBackgroundSkills,
    PendingBenefitChoice,
    PendingCareerChoice,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingCharacteristicChoice,
    PendingConnectionsRoll,
    PendingInitialTrainingChoice,
    PendingInjuryTable,
    PendingLifeEvent,
    PendingLifeEventChoice,
    PendingLifeEventUnusual,
    PendingMishap,
    PendingMusterOut,
    PendingNearlyKilled,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingSkillChoice,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingSurvive,
    PendingTermEvent,
    PendingUcp,
    ScheduledEffect,
    make_connection,
)
from ceres.character.skills import (
    AnySkill,
    BackgroundSkill,
    Level,
    Skill,
    SpaceScience,
    _skill_classes,
    skill_class_by_name,
    skill_names_for_category,
)

BACKGROUND_SKILLS: frozenset[type[Skill]] = frozenset(_skill_classes(BackgroundSkill))


class ReplayError(Exception):
    pass


def replay(character_id: int, events: Sequence[AnyEvent]) -> CharacterProjection:
    projection = CharacterProjection(character_id=character_id)
    for event in events:
        _apply(projection, event)
    return projection


def _apply(projection: CharacterProjection, event: AnyEvent) -> None:
    fulfilled_pending: AnyPending | None = None
    if event.fulfills is not None:
        fulfilled_pending = next((p for p in projection.pending_inputs if p.id == event.fulfills), None)
        _fulfill(projection, event)
    elif _has_blocking_pending(projection):
        raise ReplayError(
            f'Event {event.id} ({event.kind!r}) submitted while blocking pending input exists: '
            + ', '.join(p.id for p in projection.pending_inputs if p.blocking)
        )

    match event:
        case CharacterStartedEvent():
            _apply_character_started(projection, event)
        case UcpEvent():
            _apply_ucp(projection, event)
        case BackgroundSkillsEvent():
            _apply_background_skills(projection, event)
        case CareerEvent():
            _apply_career(projection, event)
        case SurviveEvent():
            _apply_survive(projection, event)
        case MishapEvent():
            _apply_mishap(projection, event)
        case TermEventEvent():
            _apply_term_event(projection, event)
        case SkillChoiceEvent():
            _apply_skill_choice(projection, event, fulfilled_pending)
        case AdvancementDmChoiceEvent():
            _apply_advancement_dm_choice(projection, event)
        case ConnectionKindChoiceEvent():
            _apply_connection_kind_choice(projection, event, fulfilled_pending)
        case CareerChoiceEvent():
            _apply_career_choice(projection, event)
        case BenefitChoiceEvent():
            _apply_benefit_choice(projection, event, fulfilled_pending)
        case AdvancementEvent():
            _apply_advancement(projection, event)
        case ReenlistEvent():
            _apply_reenlist(projection, event)
        case SkillTableEvent():
            _apply_skill_table(projection, event)
        case CharacteristicChoiceEvent():
            _apply_characteristic_choice(projection, event, fulfilled_pending)
        case ConnectionsRollEvent():
            _apply_connections_roll(projection, event)
        case SkillRollEvent():
            _apply_skill_roll(projection, event)
        case InjuryTableEvent():
            _apply_injury_table(projection, event)
        case DoubleInjuryTableEvent():
            _apply_double_injury_table(projection, event)
        case LifeEventEvent():
            _apply_life_event(projection, event)
        case LifeEventUnusualEvent():
            _apply_life_event_unusual(projection, event)
        case AgingRollEvent():
            _apply_aging_roll(projection, event)
        case MusterOutEvent():
            _apply_muster_out_event(projection, event)
        case AgingCrisisEvent():
            _apply_aging_crisis_event(projection, event)


def _fulfill(projection: CharacterProjection, event: AnyEvent) -> None:
    fulfills = event.fulfills
    matched = next((p for p in projection.pending_inputs if p.id == fulfills), None)
    if matched is None:
        raise ReplayError(f'Event {event.id} ({event.kind!r}) references unknown pending input {fulfills!r}')
    projection.pending_inputs.remove(matched)


def _has_blocking_pending(projection: CharacterProjection) -> bool:
    return any(p.blocking for p in projection.pending_inputs)


# ── setup ────────────────────────────────────────────────────────────────────


def _clear_current_career(projection: CharacterProjection) -> None:
    if projection.summary.current_career is not None:
        projection.summary.last_career = projection.summary.current_career
        projection.summary.last_assignment = projection.summary.current_assignment
    projection.summary.current_career = None
    projection.summary.current_assignment = None


_CAREER_PHASE_PENDING_TYPES = (
    PendingSurvive,
    PendingTermEvent,
    PendingMishap,
    PendingAdvancement,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingRankBonusChoice,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
)


def _purge_career_pendings(projection: CharacterProjection) -> None:
    """Remove pending inputs that require an active career and can no longer be fulfilled.

    Called when a career ends (mishap or reenlist=False) to clear inputs that were queued
    by prior career-phase processing and are now orphaned.
    """
    projection.pending_inputs[:] = [
        p for p in projection.pending_inputs if not isinstance(p, _CAREER_PHASE_PENDING_TYPES)
    ]


def _available_tables(career: CareerData, projection: CharacterProjection) -> list[str]:
    """Return the skill table names this character can currently choose from.

    Excludes tables with a min_edu requirement the character does not meet, and
    excludes assignment-specific tables that belong to a different assignment.
    """
    edu = projection.summary.characteristics.get(Chars.EDU, 0)
    assignment_names_lower = {a.name.lower() for a in career.assignments}
    current_lower = (projection.summary.current_assignment or '').lower()
    result = []
    for name, table in career.skill_tables.items():
        if name in assignment_names_lower and name != current_lower:
            continue
        if table.min_edu is not None and edu < table.min_edu:
            continue
        result.append(name)
    return sorted(result)


def _apply_character_started(projection: CharacterProjection, event: CharacterStartedEvent) -> None:
    projection.summary = CharacterSummary(name=event.name, species=event.sophont)
    projection.pending_inputs.append(PendingUcp(id=f'{event.id}.0', instruction='Provide characteristics (UCP)'))


def _apply_ucp(projection: CharacterProjection, event: UcpEvent) -> None:
    projection.summary.characteristics = _parse_ucp(event.ucp)
    edu = projection.summary.characteristics.get(Chars.EDU, 0)
    count = _background_skill_count(edu)
    if count > 0:
        projection.pending_inputs.append(
            PendingBackgroundSkills(
                id=f'{event.id}.0',
                instruction=f'Choose {count} background skill(s)',
                options=sorted(cls.name() for cls in BACKGROUND_SKILLS),
            )
        )


def _apply_background_skills(projection: CharacterProjection, event: BackgroundSkillsEvent) -> None:
    edu = projection.summary.characteristics.get(Chars.EDU, 0)
    expected = _background_skill_count(edu)
    if len(event.skills) != expected:
        raise ReplayError(f'Expected {expected} background skill(s), got {len(event.skills)}')
    invalid = [s for s in event.skills if type(s) not in BACKGROUND_SKILLS]
    if invalid:
        raise ReplayError(f'Invalid background skill(s): {", ".join(sorted(type(s).__name__ for s in invalid))}')
    for skill in event.skills:
        _grant_skill(projection, skill)
    career_options = sorted(load_careers().keys())
    projection.pending_inputs.append(
        PendingCareerChoice(
            id=f'{event.id}.0',
            instruction='Choose a career',
            options=career_options,
        )
    )


# ── career ───────────────────────────────────────────────────────────────────


def _apply_career(projection: CharacterProjection, event: CareerEvent) -> None:
    careers = load_careers()
    career = careers.get(event.career)
    if career is None:
        raise ReplayError(f'Unknown career: {event.career!r}')
    assignment = career.assignment(event.assignment)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {event.assignment!r} for career {event.career!r}')

    char = career.qualification.characteristic
    target = career.qualification.target
    dm = _char_dm(projection.summary.characteristics.get(char, 0))
    qual_effects = [se for se in projection.scheduled_effects if se.trigger == 'qualification' and se.consume]
    for se in qual_effects:
        dm += se.effect.get('amount', 0)
        projection.scheduled_effects.remove(se)
    if event.qualification_roll + dm < target:
        projection.summary.problems.append(f'Failed to qualify for {career.name}.')
        projection.pending_inputs.append(
            PendingCareerChoice(
                id=f'{event.id}.0',
                instruction='Qualification failed — choose another career',
                options=sorted(careers.keys()),
            )
        )
        return

    projection.summary.current_career = career.name
    projection.summary.current_assignment = assignment.name
    projection.summary.term_count += 1
    if projection.summary.rank is None:
        projection.summary.rank = 0

    if projection.summary.term_count == 1:
        # First term: initial training — non-choice skills at level 0, choice entries become pendings
        service_table = career.skill_tables['service_skills']
        choice_idx = 0
        for entry in service_table.entries.values():
            choices = entry.choices
            if choices is None and entry.skill is not None:
                choices = skill_names_for_category(entry.skill)
            if choices:
                projection.pending_inputs.append(
                    PendingInitialTrainingChoice(
                        id=f'{event.id}.{choice_idx}',
                        instruction=f'Initial training: choose one of {", ".join(choices)}',
                        options=choices,
                    )
                )
                choice_idx += 1
            else:
                _apply_initial_training_entry(projection, entry)
        if choice_idx == 0:
            projection.pending_inputs.append(_survive_pending(projection, career, assignment.name, event.id))
        # else: survive is deferred until all initial_training_choice pendings are resolved
    else:
        projection.pending_inputs.append(_survive_pending(projection, career, assignment.name, event.id))


def _apply_initial_training_entry(projection: CharacterProjection, entry: SkillTableEntry) -> None:
    if entry.choices:
        for skill in entry.choices:
            _grant_skill(projection, _skill_from_str(skill))
    elif entry.skill:
        _grant_skill(projection, _skill_from_str(entry.skill))
    # characteristic entries are not granted during initial training


def _survive_pending(
    projection: CharacterProjection, career: CareerData, assignment_name: str, event_id: int
) -> PendingSurvive:
    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r} in career {career.name!r}')
    char = assignment.survival.characteristic
    target = assignment.survival.target
    return PendingSurvive(id=f'{event_id}.0', instruction=f'Survive: {char} {target}+')


def _apply_survive(projection: CharacterProjection, event: SurviveEvent) -> None:
    career = _current_career(projection)
    assignment = career.assignment(projection.summary.current_assignment or '')
    if assignment is None:
        raise ReplayError(f'Unknown assignment {projection.summary.current_assignment!r}')

    char = assignment.survival.characteristic
    target = assignment.survival.target
    dm = _char_dm(projection.summary.characteristics.get(char, 0))
    success = event.roll != 2 and (event.roll + dm) >= target

    if success:
        projection.pending_inputs.append(PendingTermEvent(id=f'{event.id}.0', instruction='Roll 2D on Events table'))
    else:
        if event.roll == 2:
            projection.summary.narrative.append(
                f'Automatic mishap (rolled natural 2) in term {projection.summary.term_count}'
            )
        projection.pending_inputs.append(PendingMishap(id=f'{event.id}.0', instruction='Roll 1D on Mishap table'))


def _apply_mishap(projection: CharacterProjection, event: MishapEvent) -> None:
    career = _current_career(projection)
    mishap = career.mishaps.get(event.roll)
    pending_idx = 0
    if mishap:
        projection.summary.problems.append(mishap.text)
        projection.summary.narrative.append(f'Mishap ({career.name}): {mishap.text}')
        for effect in mishap.effects:
            if effect.type == 'decrease_characteristic_choice':
                options = list(getattr(effect, 'options', []))
                amount = getattr(effect, 'amount', 1)
                projection.pending_inputs.append(
                    PendingCharacteristicChoice(
                        id=f'{event.id}.{pending_idx}',
                        instruction=f'Choose characteristic to decrease by {amount}: {", ".join(options)}',
                        options=options,
                    )
                )
                pending_idx += 1
            elif effect.type == 'gain_connections_rolled':
                connection_type = getattr(effect, 'connection_type', 'contact')
                dice = getattr(effect, 'dice', '1d6')
                projection.pending_inputs.append(
                    PendingConnectionsRoll(
                        id=f'{event.id}.{pending_idx}',
                        instruction=f'Roll {dice.upper()} for number of {connection_type}s',
                        options=[str(i) for i in range(1, 7)],
                    )
                )
                pending_idx += 1
            elif effect.type == 'skill_choice':
                options = list(getattr(effect, 'options', []))
                projection.pending_inputs.append(
                    PendingSkillChoice(
                        id=f'{event.id}.{pending_idx}',
                        instruction=f'Choose one skill: {", ".join(options)}',
                        options=options,
                    )
                )
                pending_idx += 1
            elif effect.type == 'injury':
                severity = getattr(effect, 'severity', 'normal')
                if severity == 'normal':
                    projection.pending_inputs.append(
                        PendingCharacteristicChoice(
                            id=f'{event.id}.{pending_idx}',
                            instruction='Injured: choose STR, DEX, or END to reduce by 1',
                            options=[Chars.STR, Chars.DEX, Chars.END],
                        )
                    )
                    pending_idx += 1
                elif severity == 'severe':
                    projection.pending_inputs.append(
                        PendingCharacteristicChoice(
                            id=f'{event.id}.{pending_idx}',
                            instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                            options=[Chars.STR, Chars.DEX, Chars.END],
                        )
                    )
                    pending_idx += 1
                elif severity == 'from_table':
                    projection.pending_inputs.append(
                        PendingInjuryTable(
                            id=f'{event.id}.{pending_idx}',
                            instruction='Roll 1D on Injury table',
                            options=['1', '2', '3', '4', '5', '6'],
                        )
                    )
                    pending_idx += 1
            else:
                handler = get_effect_handler(career.name, effect.type)
                if handler:
                    pending_idx = handler(projection, effect, event.id, pending_idx)
                else:
                    _apply_simple_effect(projection, effect, source=mishap.text, source_event_id=event.id)
    defer = mishap is not None and mishap.defer_ejection
    if defer:
        pass  # handler owns the full ejection/stay flow; nothing automatic here
    elif event.stay_in_career or (mishap is not None and mishap.stay_in_career):
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id, pending_idx))
    else:
        # Career is ending — purge orphaned career-phase pendings that can no longer be fulfilled.
        _purge_career_pendings(projection)
        projection.summary.age += 4
        if projection.summary.age >= 34:
            # Save career for muster out after aging resolves (mishap = lose current term)
            projection.muster_out_career = career.name
            _clear_current_career(projection)
            projection.pending_inputs.append(
                PendingAgingRoll(id=f'{event.id}.{pending_idx}', instruction='Roll 2D on Aging table')
            )
        else:
            _apply_muster_out_setup(projection, career, event.id, pending_idx, lose_current_term=True)


def _apply_term_event(projection: CharacterProjection, event: TermEventEvent) -> None:
    career = _current_career(projection)
    term_event = career.events.get(event.roll)

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
            if effect.type == 'skill_choice':
                skill_choice_effect = effect
            elif effect.type == 'roll_mishap':
                roll_mishap_effect = effect
            elif effect.type == 'auto_advance':
                auto_advance = True
            elif effect.type == 'life_event':
                life_event_pending = True
            else:
                handler = get_effect_handler(career.name, effect.type)
                if handler:
                    pending_idx = handler(projection, effect, event.id, pending_idx)
                    career_handler_invoked = True
                else:
                    _apply_simple_effect(projection, effect, source=term_event.text, source_event_id=event.id)

    if roll_mishap_effect is not None:
        leave = getattr(roll_mishap_effect, 'leave', True)
        instruction = (
            'Roll 1D on Mishap table (you are not ejected from this career)' if not leave else 'Roll 1D on Mishap table'
        )
        projection.pending_inputs.append(PendingMishap(id=f'{event.id}.{pending_idx}', instruction=instruction))
        # advancement pending created when mishap resolves with stay_in_career=True
    elif auto_advance:
        _apply_auto_advance(projection, career, event.id)
    elif life_event_pending:
        projection.pending_inputs.append(
            PendingLifeEvent(id=f'{event.id}.{pending_idx}', instruction='Roll 2D on Life Events table')
        )
        # advancement pending created by _apply_life_event or _apply_life_event_unusual
    elif skill_choice_effect is not None:
        options = list(getattr(skill_choice_effect, 'options', []))
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.{pending_idx}',
                instruction=f'Choose one skill: {", ".join(options)}',
                options=options,
            )
        )
        # advancement pending will be created after skill_choice is resolved
    elif not career_handler_invoked:
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    # If a career handler was invoked it owns the flow; _apply_skill_roll creates advancement


def _resolve_rank_bonus_choices(bonus: RankBonus) -> list[str] | None:
    """Return the choice list for a rank bonus, deriving it from skills.py if not explicit."""
    if bonus.choices:
        return bonus.choices
    if bonus.skill:
        return skill_names_for_category(bonus.skill)
    return None


def _apply_auto_advance(projection: CharacterProjection, career: CareerData, event_id: int) -> None:
    new_rank = (projection.summary.rank or 0) + 1
    projection.summary.rank = new_rank
    assignment_name = projection.summary.current_assignment or ''
    rank_entry = career.assignment_ranks(assignment_name).get(new_rank)
    if rank_entry and rank_entry.bonus:
        bonus = rank_entry.bonus
        choices = _resolve_rank_bonus_choices(bonus)
        if choices:
            projection.pending_inputs.append(
                PendingRankBonusChoice(
                    id=f'{event_id}.0',
                    level=bonus.level,
                    instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                    options=choices,
                )
            )
            return  # skill_table + reenlist pending deferred until after choice
        elif bonus.skill:
            _grant_skill(projection, _skill_from_str(bonus.skill, bonus.level))
        elif bonus.characteristic:
            char = bonus.characteristic
            projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
    tables = _available_tables(career, projection)
    projection.pending_inputs.append(
        PendingSkillTable(id=f'{event_id}.0', instruction='Choose a skill table and roll 1D', options=tables)
    )
    _queue_reenlist_or_aging(projection, event_id, 1)


def _apply_skill_choice(
    projection: CharacterProjection, event: SkillChoiceEvent, fulfilled_pending: AnyPending | None = None
) -> None:
    if isinstance(fulfilled_pending, PendingInitialTrainingChoice):
        _grant_skill(projection, event.skill)
        remaining = [p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice)]
        if not remaining and projection.summary.current_career is not None:
            career = _current_career(projection)
            assignment_name = projection.summary.current_assignment or ''
            projection.pending_inputs.append(_survive_pending(projection, career, assignment_name, event.id))
    elif isinstance(fulfilled_pending, PendingSkillTableChoice):
        _grant_skill(projection, event.skill)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            assignment_name = projection.summary.current_assignment or ''
            projection.pending_inputs.append(_survive_pending(projection, career, assignment_name, event.id))
    elif isinstance(fulfilled_pending, PendingCareerSkillChoice):
        _grant_skill(projection, event.skill)
        if not fulfilled_pending.advancement_precreated and projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif isinstance(fulfilled_pending, PendingRankBonusChoice):
        _grant_skill(projection, event.skill)
        career = _current_career(projection)
        tables = _available_tables(career, projection)
        projection.pending_inputs.append(
            PendingSkillTable(id=f'{event.id}.0', instruction='Choose a skill table and roll 1D', options=tables)
        )
        _queue_reenlist_or_aging(projection, event.id, 1)
    else:
        _grant_skill(projection, event.skill)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id))


def _apply_advancement_dm_choice(projection: CharacterProjection, event: AdvancementDmChoiceEvent) -> None:
    projection.scheduled_effects.append(
        ScheduledEffect(trigger='advancement', source_event_id=event.id, effect={'type': 'dm', 'amount': 4})
    )
    if projection.summary.current_career is not None:
        career = _current_career(projection)
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))


def _apply_connection_kind_choice(
    projection: CharacterProjection, event: ConnectionKindChoiceEvent, fulfilled_pending: AnyPending | None = None
) -> None:
    source = (
        f'Life event roll {fulfilled_pending.roll}'
        if isinstance(fulfilled_pending, PendingLifeEventChoice)
        else 'unknown'
    )
    projection.summary.connections.append(make_connection(event.connection_kind, source=f'Life event: {source}'))
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
            entry = kind_map.get(event.connection_kind)
            if entry:
                projection.summary.narrative.append(entry)
    # advancement was pre-created by _apply_life_event


def _apply_career_choice(projection: CharacterProjection, event: CareerChoiceEvent) -> None:
    career_name = projection.summary.current_career
    if career_name is None:
        raise ReplayError(f'CareerChoiceEvent submitted with no active career (context={event.context!r})')
    handler = get_choice_handler(career_name, event.context)
    if handler is None:
        raise ReplayError(f'No choice handler for career {career_name!r} context {event.context!r}')
    handler(projection, event)


def _apply_benefit_choice(
    projection: CharacterProjection, event: BenefitChoiceEvent, fulfilled_pending: AnyPending | None = None
) -> None:
    if not isinstance(fulfilled_pending, PendingBenefitChoice):
        raise ReplayError('BenefitChoiceEvent must fulfill a PendingBenefitChoice')
    options = fulfilled_pending.benefit_options
    if not (0 <= event.choice_index < len(options)):
        raise ReplayError(f'choice_index {event.choice_index} out of range for {len(options)} options')
    _apply_muster_out_benefit(projection, options[event.choice_index], event.id)


def _apply_skill_roll(projection: CharacterProjection, event: SkillRollEvent) -> None:
    career = _current_career(projection)
    handler = get_skill_roll_handler(career.name, event.context)
    pending_count_before = len(projection.pending_inputs)
    if handler:
        handler(projection, event)
    if len(projection.pending_inputs) == pending_count_before and projection.summary.current_career is not None:
        # Handler applied effects directly and career is still active; advancement is next
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    # Otherwise handler created its own pending (skill_choice or mishap-stay), or ejected the career


def _apply_injury_table(projection: CharacterProjection, event: InjuryTableEvent) -> None:
    if not (1 <= event.roll <= 6):
        raise ReplayError(f'Injury table roll must be 1-6, got {event.roll}')
    _apply_injury_table_result(projection, event.roll, event.id)


def _apply_double_injury_table(projection: CharacterProjection, event: DoubleInjuryTableEvent) -> None:
    for roll in (event.roll1, event.roll2):
        if not (1 <= roll <= 6):
            raise ReplayError(f'Double injury roll must be 1-6, got {roll}')
    _apply_injury_table_result(projection, min(event.roll1, event.roll2), event.id)


def _apply_injury_table_result(projection: CharacterProjection, roll: int, event_id: int) -> None:
    if roll == 6:
        return  # lightly injured — no permanent effect
    elif roll == 5:
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


def _apply_life_event(projection: CharacterProjection, event: LifeEventEvent) -> None:
    if not (2 <= event.roll <= 12):
        raise ReplayError(f'Life event roll must be 2-12, got {event.roll}')
    career = _current_career(projection)
    roll = event.roll
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
    # Rolls 4 and 8 have a rival-or-enemy choice; narrative is deferred to _apply_connection_kind_choice
    if roll in _LIFE_EVENT_NARRATIVE:
        projection.summary.narrative.append(_LIFE_EVENT_NARRATIVE[roll])
    if roll == 2:
        # Sickness or injury — roll on injury table, advancement after that resolves
        projection.pending_inputs.append(
            PendingInjuryTable(
                id=f'{event.id}.0',
                instruction='Roll 1D on Injury table (sickness/injury)',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id, 1))
    elif roll == 3:
        # Birth or death — no mechanical effect
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 4:
        # Ending of relationship — choose to gain rival or enemy
        projection.pending_inputs.append(
            PendingLifeEventChoice(
                id=f'{event.id}.0',
                roll=4,
                instruction='Ending relationship: gain a rival or enemy?',
                options=['rival', 'enemy'],
            )
        )
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id, 1))
    elif roll == 5:
        # Improved relationship — ally
        projection.summary.connections.append(Ally(source='Life event: improved relationship'))
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 6:
        # New relationship — ally
        projection.summary.connections.append(Ally(source='Life event: new relationship'))
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 7:
        # New contact
        projection.summary.connections.append(Contact(source='Life event: new contact'))
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 8:
        # Betrayal — gain rival or enemy
        projection.pending_inputs.append(
            PendingLifeEventChoice(
                id=f'{event.id}.0',
                roll=8,
                instruction='Betrayal: gain a rival or enemy?',
                options=['rival', 'enemy'],
            )
        )
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id, 1))
    elif roll == 9:
        # Travel — DM+2 to next qualification roll
        projection.scheduled_effects.append(
            ScheduledEffect(trigger='qualification', source_event_id=event.id, effect={'type': 'dm', 'amount': 2})
        )
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 10:
        # Good fortune — DM+2 to any one Benefit roll
        projection.scheduled_effects.append(
            ScheduledEffect(trigger='muster_out', source_event_id=event.id, effect={'type': 'dm', 'amount': 2})
        )
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 11:
        # Crime — lose one Benefit roll
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out_reduce', source_event_id=event.id, effect={'type': 'reduce', 'value': 1}
            )
        )
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 12:
        # Unusual event — roll on unusual sub-table; advancement after that resolves
        projection.pending_inputs.append(
            PendingLifeEventUnusual(
                id=f'{event.id}.0',
                instruction='Roll 1D on Unusual Events table',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id, 1))


def _apply_life_event_unusual(projection: CharacterProjection, event: LifeEventUnusualEvent) -> None:
    if not (1 <= event.roll <= 6):
        raise ReplayError(f'Life event unusual roll must be 1-6, got {event.roll}')
    roll = event.roll
    if roll == 1:
        # Useful ally — gain ally
        projection.summary.connections.append(Ally(source='Unusual event: useful ally'))
        projection.summary.narrative.append('Unusual event: gained a useful ally')
    elif roll == 2:
        # Aliens — gain contact + any science skill at level 1
        projection.summary.connections.append(Contact(source='Unusual event: alien contact'))
        _grant_skill(projection, _skill_from_str(SpaceScience.name(), 1))
        projection.summary.narrative.append('Unusual event: alien encounter — gained contact and Space Science 1')
    else:
        # rolls 3-6: no mechanical effect in Explorer edition
        projection.summary.narrative.append('Unusual event: something strange (no mechanical effect)')
    # advancement was pre-created by _apply_life_event at event.id.1


def _apply_aging_roll(projection: CharacterProjection, event: AgingRollEvent) -> None:
    if not (2 <= event.roll <= 12):
        raise ReplayError(f'Aging roll must be 2-12, got {event.roll}')
    effective = event.roll - projection.summary.term_count
    pending_idx = 0

    if effective >= 1:
        _complete_aging(projection, event.id)
    elif effective == 0:
        projection.pending_inputs.append(
            PendingAgingChoice(
                id=f'{event.id}.{pending_idx}',
                instruction='Aging: choose STR, DEX, or END to reduce by 1',
                options=[Chars.STR, Chars.DEX, Chars.END],
            )
        )
    elif effective == -1:
        for _ in range(2):
            projection.pending_inputs.append(
                PendingAgingChoice(
                    id=f'{event.id}.{pending_idx}',
                    instruction='Aging: choose STR, DEX, or END to reduce by 1',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
            pending_idx += 1
    elif effective == -2:
        for char in (Chars.STR, Chars.DEX, Chars.END):
            projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 1)
        if not _check_aging_crisis(projection, event.id):
            _complete_aging(projection, event.id)
    elif effective == -3:
        projection.pending_inputs.append(
            PendingAgingChoice(
                id=f'{event.id}.{pending_idx}',
                instruction='Aging: choose STR, DEX, or END to reduce by 2',
                options=[Chars.STR, Chars.DEX, Chars.END],
            )
        )
        pending_idx += 1
        for _ in range(2):
            projection.pending_inputs.append(
                PendingAgingChoice(
                    id=f'{event.id}.{pending_idx}',
                    instruction='Aging: choose STR, DEX, or END to reduce by 1',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
            pending_idx += 1
    elif effective == -4:
        for _ in range(2):
            projection.pending_inputs.append(
                PendingAgingChoice(
                    id=f'{event.id}.{pending_idx}',
                    instruction='Aging: choose STR, DEX, or END to reduce by 2',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                )
            )
            pending_idx += 1
        projection.pending_inputs.append(
            PendingAgingChoice(
                id=f'{event.id}.{pending_idx}',
                instruction='Aging: choose STR, DEX, or END to reduce by 1',
                options=[Chars.STR, Chars.DEX, Chars.END],
            )
        )
    elif effective == -5:
        for char in (Chars.STR, Chars.DEX, Chars.END):
            projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 2)
        if not _check_aging_crisis(projection, event.id):
            _complete_aging(projection, event.id)
    else:  # <= -6
        for char in (Chars.STR, Chars.DEX, Chars.END):
            projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 2)
        if not _check_aging_crisis(projection, event.id):
            projection.pending_inputs.append(
                PendingAgingChoiceMental(
                    id=f'{event.id}.0',
                    instruction='Aging: choose INT or SOC to reduce by 1',
                    options=[Chars.INT, Chars.SOC],
                )
            )


def _complete_aging(projection: CharacterProjection, source_event_id: int) -> None:
    if projection.muster_out_career is not None:
        # mishap ejection (pending_reenlist=None) or legacy reenlist=False-before-aging path
        careers = load_careers()
        career = careers.get(projection.muster_out_career)
        lose = projection.pending_reenlist is None  # None=mishap path → lose current term
        projection.muster_out_career = None  # reset before setup re-sets it if needed
        if career:
            _apply_muster_out_setup(projection, career, source_event_id, 0, lose_current_term=lose, clear_career=False)
    else:
        # end-of-term aging: reenlist decision comes after aging resolves
        projection.pending_inputs.append(
            PendingReenlist(
                id=f'{source_event_id}.0',
                instruction='Reenlist or muster out?',
                options=['true', 'false'],
            )
        )
    projection.pending_reenlist = None


def _check_aging_crisis(projection: CharacterProjection, source_event_id: int) -> bool:
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


def _apply_aging_crisis_event(projection: CharacterProjection, event: AgingCrisisEvent) -> None:
    career_name = projection.summary.current_career or projection.muster_out_career
    careers = load_careers()
    career = careers.get(career_name) if career_name else None

    if event.paid:
        for char in list(projection.summary.characteristics.keys()):
            if projection.summary.characteristics[char] == 0:
                projection.summary.characteristics[char] = 1
        # pending_reenlist=True would mean a reenlist decision was deferred across an aging crisis,
        # but aging always precedes the reenlist prompt so this branch is currently unreachable.
        if projection.pending_reenlist is True:
            projection.summary.term_count += 1
        projection.pending_reenlist = None
        projection.muster_out_career = None
        if career:
            _apply_muster_out_setup(projection, career, event.id, 0, clear_career=True)
        else:
            _clear_current_career(projection)
    else:
        projection.summary.dead = True
        _clear_current_career(projection)
        projection.muster_out_career = None
        projection.pending_reenlist = None


def _apply_muster_out_setup(
    projection: CharacterProjection,
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
    if clear_career:
        _clear_current_career(projection)
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
    return pending_idx


def _apply_muster_out_event(projection: CharacterProjection, event: MusterOutEvent) -> None:
    career_name = projection.muster_out_career
    if career_name is None:
        raise ReplayError('No muster out career set')
    careers = load_careers()
    career = careers.get(career_name)
    if career is None or career.muster_out is None:
        raise ReplayError(f'Career {career_name!r} has no muster out table')

    effective_roll = max(1, min(7, event.roll))
    row = career.muster_out.rows.get(effective_roll)
    if row is None:
        raise ReplayError(f'No muster out row for roll {effective_roll}')

    if event.table == 'cash':
        if projection.summary.muster_out_cash_count >= 3:
            raise ReplayError('Cash may only be taken a maximum of 3 times')
        projection.summary.cash += row.cash
        projection.summary.muster_out_cash_count += 1
    else:
        for _ in range(row.count):
            _apply_muster_out_benefit(projection, row.benefit, event.id)

    remaining = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
    if not remaining:
        projection.muster_out_career = None


def _apply_muster_out_benefit(projection: CharacterProjection, benefit: object, event_id: int = 0) -> None:
    from ceres.character.benefits import CharacteristicIncrease, ChoiceBenefit, ItemBenefit

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


def _apply_characteristic_choice(
    projection: CharacterProjection, event: CharacteristicChoiceEvent, fulfilled_pending: AnyPending | None = None
) -> None:
    char = event.characteristic
    current = projection.summary.characteristics.get(char, 0)
    projection.summary.characteristics[char] = max(0, current - event.amount)
    if isinstance(fulfilled_pending, PendingNearlyKilled):
        for other in (Chars.STR, Chars.DEX, Chars.END):
            if other != char:
                projection.summary.characteristics[other] = max(0, projection.summary.characteristics.get(other, 0) - 2)
    elif isinstance(fulfilled_pending, (PendingAgingChoice, PendingAgingChoiceMental)):
        if not _check_aging_crisis(projection, event.id):
            remaining = [
                p for p in projection.pending_inputs if isinstance(p, (PendingAgingChoice, PendingAgingChoiceMental))
            ]
            if not remaining:
                _complete_aging(projection, event.id)


def _apply_advancement(projection: CharacterProjection, event: AdvancementEvent) -> None:
    career = _current_career(projection)
    assignment = career.assignment(projection.summary.current_assignment or '')
    if assignment is None:
        raise ReplayError(f'Unknown assignment {projection.summary.current_assignment!r}')

    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    dm = _char_dm(projection.summary.characteristics.get(char, 0))
    to_consume = [se for se in projection.scheduled_effects if se.trigger == 'advancement' and se.consume]
    for se in to_consume:
        dm += se.effect.get('amount', 0)
        projection.scheduled_effects.remove(se)
    success = (event.roll + dm) >= target

    if success:
        new_rank = (projection.summary.rank or 0) + 1
        projection.summary.rank = new_rank
        assignment_name = projection.summary.current_assignment or ''
        rank_entry = career.assignment_ranks(assignment_name).get(new_rank)
        if rank_entry and rank_entry.bonus:
            bonus = rank_entry.bonus
            choices = _resolve_rank_bonus_choices(bonus)
            if choices:
                projection.pending_inputs.append(
                    PendingRankBonusChoice(
                        id=f'{event.id}.0',
                        level=bonus.level,
                        instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                        options=choices,
                    )
                )
                return  # skill_table + reenlist pending deferred until after choice
            elif bonus.skill:
                _grant_skill(projection, _skill_from_str(bonus.skill, bonus.level))
            elif bonus.characteristic:
                char = bonus.characteristic
                projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
        tables = _available_tables(career, projection)
        projection.pending_inputs.append(
            PendingSkillTable(
                id=f'{event.id}.0',
                instruction='Choose a skill table and roll 1D',
                options=tables,
            )
        )
        _queue_reenlist_or_aging(projection, event.id, 1)
        return

    _queue_reenlist_or_aging(projection, event.id, 0)


def _queue_reenlist_or_aging(projection: CharacterProjection, event_id: int, idx: int) -> None:
    projection.summary.age += 4
    if projection.summary.age >= 34:
        projection.pending_inputs.append(PendingAgingRoll(id=f'{event_id}.{idx}', instruction='Roll 2D on Aging table'))
    else:
        projection.pending_inputs.append(
            PendingReenlist(
                id=f'{event_id}.{idx}',
                instruction='Reenlist or muster out?',
                options=['true', 'false'],
            )
        )


def _apply_reenlist(projection: CharacterProjection, event: ReenlistEvent) -> None:
    if event.reenlist:
        career = _current_career(projection)
        projection.summary.term_count += 1
        # Clear all orphaned career-phase pendings from the ending term (survive, skill table choices, etc.).
        _purge_career_pendings(projection)
        assignment_name = projection.summary.current_assignment or ''
        assignment = career.assignment(assignment_name)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {assignment_name!r} in career {career.name!r}')
        tables = _available_tables(career, projection)
        projection.pending_inputs.append(
            PendingSkillTable(
                id=f'{event.id}.0',
                instruction='Choose a skill table and roll 1D',
                options=tables,
            )
        )
    else:
        # Mustering out — purge orphaned career-phase pendings queued by the last skill table.
        _purge_career_pendings(projection)
        career = _current_career(projection)
        _apply_muster_out_setup(projection, career, event.id, 0, lose_current_term=False)


def _apply_skill_table(projection: CharacterProjection, event: SkillTableEvent) -> None:
    career = _current_career(projection)
    table = career.skill_tables.get(event.table)
    if table is None:
        raise ReplayError(f'Unknown skill table: {event.table!r}')
    if table.min_edu is not None:
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        if edu < table.min_edu:
            raise ReplayError(f'Table {event.table!r} requires EDU {table.min_edu}+, character has {edu}')
    if not (1 <= event.roll <= 6):
        raise ReplayError(f'Skill table roll must be 1-6, got {event.roll}')
    entry = table.entries.get(event.roll)
    if entry is None:
        raise ReplayError(f'No entry for roll {event.roll} in table {event.table!r}')
    assignment_name = projection.summary.current_assignment or ''
    choices = entry.choices
    if choices is None and entry.skill is not None:
        choices = skill_names_for_category(entry.skill)
    if choices:
        projection.pending_inputs.append(
            PendingSkillTableChoice(
                id=f'{event.id}.0',
                instruction=f'Choose one skill: {", ".join(choices)}',
                options=choices,
            )
        )
        # survive pending created after choice is made in _apply_skill_choice
    else:
        _apply_skill_table_entry(projection, entry)
        projection.pending_inputs.append(_survive_pending(projection, career, assignment_name, event.id))


def _apply_skill_table_entry(projection: CharacterProjection, entry: SkillTableEntry) -> None:
    if entry.characteristic:
        char = entry.characteristic
        projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + 1
    elif entry.skill:
        _increment_yaml_skill(projection, entry.skill)


# ── helpers ──────────────────────────────────────────────────────────────────


def _advancement_pending(
    projection: CharacterProjection, career: CareerData, event_id: int, pending_idx: int = 0
) -> PendingAdvancement:
    assignment = career.assignment(projection.summary.current_assignment or '')
    if assignment is None:
        raise ReplayError(f'Unknown assignment {projection.summary.current_assignment!r}')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    return PendingAdvancement(id=f'{event_id}.{pending_idx}', instruction=f'Advancement: {char} {target}+')


def _current_career(projection: CharacterProjection) -> CareerData:
    career_name = projection.summary.current_career
    if career_name is None:
        raise ReplayError('No active career')
    careers = load_careers()
    career = careers.get(career_name)
    if career is None:
        raise ReplayError(f'Unknown career: {career_name!r}')
    return career


def _skill_from_str(name: str, level: int = 0) -> AnySkill:
    from typing import Any

    skill_cls = skill_class_by_name(name)
    _cls: Any = skill_cls
    if level == 0:
        return cast(AnySkill, _cls())
    if not _cls().specialities():
        return cast(AnySkill, _cls(level=Level(value=level)))
    # Specialised skill from YAML without explicit specialization (placeholder until YAML fixed)
    from ceres.character.projection import _level_fields

    fields = {f: Level(value=level) for f in _level_fields(skill_cls)}
    return cast(AnySkill, _cls(**fields))


def _increment_yaml_skill(projection: CharacterProjection, skill_name: str) -> None:
    from typing import cast as _cast

    from ceres.character.projection import _level_fields
    from ceres.character.skills import AnySkill as _AnySkill

    skill_cls = skill_class_by_name(skill_name)
    existing = next((s for s in projection.summary.skills if type(s) is skill_cls), None)
    if existing is None:
        # Career tables grant skills at level 1 (new skill: gain it, then increase by 1)
        new_skill = skill_cls()
        fields = _level_fields(skill_cls)
        getattr(new_skill, fields[0]).set(1)
        projection.summary.skills.append(_cast(_AnySkill, new_skill))
        return
    fields = _level_fields(skill_cls)
    if len(fields) == 1:
        current = getattr(existing, fields[0]).value
        if current < 4:
            getattr(existing, fields[0]).set(current + 1)
    else:
        # Specialised skill: increment the first specialization below 4
        for field in fields:
            current = getattr(existing, field).value
            if current < 4:
                getattr(existing, field).set(current + 1)
                break


def _grant_skill(projection: CharacterProjection, skill: AnySkill) -> None:
    from ceres.character.projection import _level_fields

    skill_cls = type(skill)
    existing = next((s for s in projection.summary.skills if type(s) is skill_cls), None)
    if existing is None:
        projection.summary.skills.append(skill_cls())
        existing = projection.summary.skills[-1]
    for field in _level_fields(skill_cls):
        given = getattr(skill, field).value
        if given > 0:
            current = getattr(existing, field).value
            getattr(existing, field).set(max(current, given))


def _apply_simple_effect(
    projection: CharacterProjection, effect: object, source: str = '', source_event_id: int = 0
) -> None:
    effect_type = getattr(effect, 'type', None)
    if effect_type == 'gain_skill':
        skill = getattr(effect, 'skill', None)
        level = getattr(effect, 'level', 1)
        if skill:
            _grant_skill(projection, _skill_from_str(skill, level))
    elif effect_type == 'decrease_characteristic':
        char = getattr(effect, 'characteristic', None)
        amount = getattr(effect, 'amount', 1)
        if char:
            current = projection.summary.characteristics.get(char, 0)
            projection.summary.characteristics[char] = max(0, current - amount)
    elif effect_type in ('gain_contact', 'gain_ally', 'gain_rival', 'gain_enemy'):
        kind = cast(Literal['contact', 'ally', 'rival', 'enemy'], effect_type.removeprefix('gain_'))
        projection.summary.connections.append(make_connection(kind, source=source))
    elif effect_type == 'advancement_dm':
        amount = getattr(effect, 'amount', 0)
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement', source_event_id=source_event_id, effect={'type': 'dm', 'amount': amount}
            )
        )
    elif effect_type == 'benefit_dm':
        amount = getattr(effect, 'amount', 0)
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out', source_event_id=source_event_id, effect={'type': 'dm', 'amount': amount}
            )
        )
    # note, injury, life_event, etc. are deferred


def _apply_connections_roll(projection: CharacterProjection, event: ConnectionsRollEvent) -> None:
    for _ in range(event.count):
        projection.summary.connections.append(make_connection(event.connection_type))


# ── characteristic DM and UCP parsing ────────────────────────────────────────


def _parse_ucp(ucp: str) -> dict[Chars, int]:
    if len(ucp) != 6:
        raise ReplayError(f'Invalid UCP: {ucp!r} — expected 6 hex digits')
    return {stat: int(digit, 16) for stat, digit in zip(UCP_STATS, ucp, strict=True)}


def _char_dm(value: int) -> int:
    if value == 0:
        return -3
    if value <= 2:
        return -2
    if value <= 5:
        return -1
    if value <= 8:
        return 0
    if value <= 11:
        return 1
    if value <= 14:
        return 2
    return 3


def _edu_dm(edu: int) -> int:
    return _char_dm(edu)


def _background_skill_count(edu: int) -> int:
    return max(0, _char_dm(edu) + 3)
