from collections.abc import Sequence

from ceres.character.careers.career_data import (
    AdvancementDmEffect,
    AnyEffect,
    AutoAdvanceEffect,
    BenefitDmEffect,
    CareerData,
    DecreaseCharacteristicChoiceEffect,
    DecreaseCharacteristicEffect,
    GainAllyEffect,
    GainConnectionsRolledEffect,
    GainContactEffect,
    GainEnemyEffect,
    GainRivalEffect,
    GainSkillEffect,
    InjuryEffect,
    LifeEventEffect,
    ParoleThresholdChangeEffect,
    RollMishapEffect,
    SkillChoiceEffect,
    SkillTableEntry,
)
from ceres.character.careers.loader import (
    get_choice_handler,
    get_effect_handler,
    get_skill_roll_handler,
    load_careers,
    selectable_careers,
)
from ceres.character.characteristics import UCP_STATS, Chars, ConnectionKind, characteristic_dm
from ceres.character.events import (
    AdvancementDmChoiceEvent,
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    AnyEvent,
    AssignmentChangeChoiceEvent,
    BackgroundSkillsEvent,
    BenefitChoiceEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    CommissionEvent,
    ConnectionKindChoiceEvent,
    ConnectionsRollEvent,
    DoubleInjuryTableEvent,
    DraftAssignmentEvent,
    DraftEvent,
    FinishCreationEvent,
    InjuryTableEvent,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
    ParoleRollEvent,
    PreCareerEntryEvent,
    PreCareerEventEvent,
    PreCareerGraduationEvent,
    PreCareerSkillChoiceEvent,
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
    PendingAssignmentChangeChoice,
    PendingBackgroundSkills,
    PendingBenefitChoice,
    PendingCareerChoice,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingCharacteristicChoice,
    PendingCommissionChoice,
    PendingConnectionsRoll,
    PendingInitialTrainingChoice,
    PendingInjuryTable,
    PendingLifeEvent,
    PendingLifeEventChoice,
    PendingLifeEventUnusual,
    PendingMishap,
    PendingMusterOut,
    PendingNearlyKilled,
    PendingPreCareerEvent,
    PendingPreCareerGraduation,
    PendingPreCareerSkillChoice,
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
    Skill,
    SpaceScience,
    _level_fields,
    _skill_classes,
    parse_skill_spec_option,
    skill_class_by_name,
    skill_from_str,
    skill_names_for_category,
)

BACKGROUND_SKILLS: frozenset[type[Skill]] = frozenset(_skill_classes(BackgroundSkill))


class ReplayError(Exception):
    pass


def replay(character_id: int, events: Sequence[AnyEvent]) -> CharacterProjection:
    if not events or not isinstance(events[0], CharacterStartedEvent):
        raise ReplayError('First event must be CharacterStartedEvent')
    first = events[0]
    projection = CharacterProjection(
        character_id=character_id,
        summary=CharacterSummary(
            name=first.name,
            sophont=first.sophont,
            homeworld=first.homeworld,
        ),
    )
    projection.pending_inputs.append(PendingUcp(id=f'{first.id}.0', instruction='Provide characteristics (UCP)'))
    for event in events[1:]:
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
        case UcpEvent():
            _apply_ucp(projection, event)
        case BackgroundSkillsEvent():
            _apply_background_skills(projection, event)
        case CareerEvent():
            _apply_career(projection, event)
        case DraftEvent():
            _apply_draft(projection, event)
        case DraftAssignmentEvent():
            _apply_draft_assignment(projection, event)
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
        case CommissionEvent():
            _apply_commission(projection, event)
        case ReenlistEvent():
            _apply_reenlist(projection, event)
        case AssignmentChangeChoiceEvent():
            _apply_assignment_change_choice(projection, event)
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
        case FinishCreationEvent():
            pass  # fulfills the pending career choice; no further state change needed
        case PreCareerEntryEvent():
            _apply_precareer_entry(projection, event)
        case PreCareerSkillChoiceEvent():
            _apply_precareer_skill_choice(projection, event, fulfilled_pending)
        case PreCareerEventEvent():
            _apply_precareer_event(projection, event)
        case PreCareerGraduationEvent():
            _apply_precareer_graduation(projection, event)
        case ParoleRollEvent():
            _apply_parole_roll(projection, event)


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


def _purge_career_pendings(projection: CharacterProjection) -> None:
    """Remove pending inputs that require an active career and can no longer be fulfilled.

    Called when a career ends (mishap or reenlist=False) to clear inputs that were queued
    by prior career-phase processing and are now orphaned.
    """
    projection.pending_inputs[:] = [
        p for p in projection.pending_inputs if not isinstance(p, _CAREER_PHASE_PENDING_TYPES)
    ]


def _apply_ucp(projection: CharacterProjection, event: UcpEvent) -> None:
    projection.summary.characteristics = _parse_ucp(event.ucp, projection.summary.sophont)
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
        projection.grant_skill(skill)
    _queue_career_choice(projection, event.id, 'Choose a career')


def _queue_career_choice(projection: CharacterProjection, event_id: int, instruction: str) -> None:
    _queue_career_choice_indexed(projection, event_id, 0, instruction)


def _queue_career_choice_indexed(
    projection: CharacterProjection, event_id: int, idx: int, instruction: str = 'Choose a career'
) -> None:
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


# ── career ───────────────────────────────────────────────────────────────────


def _apply_career(projection: CharacterProjection, event: CareerEvent) -> None:
    careers = load_careers()
    career = careers.get(event.career)
    if career is None:
        raise ReplayError(f'Unknown career: {event.career!r}')
    assignment = career.assignment(event.assignment)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {event.assignment!r} for career {event.career!r}')

    career.start_career(projection, assignment, event.id, event.qualification_roll)


def _apply_draft(projection: CharacterProjection, event: DraftEvent) -> None:
    if projection.summary.drafted:
        raise ReplayError('A character may only enter the draft once')
    career = load_careers().get(event.career)
    if career is None:
        raise ReplayError(f'Unknown career: {event.career!r}')
    career.start_draft(projection, event.id, event.assignment)


def _apply_draft_assignment(projection: CharacterProjection, event: DraftAssignmentEvent) -> None:
    career = load_careers().get(event.career)
    if career is None:
        raise ReplayError(f'Unknown career: {event.career!r}')
    career.start_draft(projection, event.id, event.assignment)


def _survive_pending(career: CareerData, assignment_name: str, event_id: int) -> PendingSurvive:
    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r} in career {career.name!r}')
    return career.survival_pending(assignment, event_id)


def _apply_survive(projection: CharacterProjection, event: SurviveEvent) -> None:
    career = _current_career(projection)
    assignment = career.assignment(projection.summary.current_assignment or '')
    if assignment is None:
        raise ReplayError(f'Unknown assignment {projection.summary.current_assignment!r}')

    char = assignment.survival.characteristic
    target = assignment.survival.target
    dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
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
            if isinstance(effect, DecreaseCharacteristicChoiceEffect):
                projection.pending_inputs.append(
                    PendingCharacteristicChoice(
                        id=f'{event.id}.{pending_idx}',
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
                        id=f'{event.id}.{pending_idx}',
                        connection_type=effect.connection_type,
                        instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s',
                        options=[str(i) for i in range(1, 7)],
                    )
                )
                pending_idx += 1
            elif isinstance(effect, SkillChoiceEffect):
                projection.pending_inputs.append(
                    PendingSkillChoice(
                        id=f'{event.id}.{pending_idx}',
                        instruction=f'Choose one skill: {", ".join(effect.options)}',
                        options=effect.options,
                    )
                )
                pending_idx += 1
            elif isinstance(effect, InjuryEffect):
                if effect.severity == 'normal':
                    projection.pending_inputs.append(
                        PendingCharacteristicChoice(
                            id=f'{event.id}.{pending_idx}',
                            instruction='Injured: choose STR, DEX, or END to reduce by 1',
                            options=[Chars.STR, Chars.DEX, Chars.END],
                        )
                    )
                    pending_idx += 1
                elif effect.severity == 'severe':
                    projection.pending_inputs.append(
                        PendingCharacteristicChoice(
                            id=f'{event.id}.{pending_idx}',
                            instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                            options=[Chars.STR, Chars.DEX, Chars.END],
                        )
                    )
                    pending_idx += 1
                elif effect.severity == 'from_table':
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
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id, pending_idx)
        )
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
                    pending_idx = handler(projection, effect, event.id, pending_idx)
                    career_handler_invoked = True
                else:
                    _apply_simple_effect(projection, effect, source=term_event.text, source_event_id=event.id)

    if roll_mishap_effect is not None:
        instruction = (
            'Roll 1D on Mishap table (you are not ejected from this career)'
            if not roll_mishap_effect.leave
            else 'Roll 1D on Mishap table'
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
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.{pending_idx}',
                instruction=f'Choose one skill: {", ".join(skill_choice_effect.options)}',
                options=skill_choice_effect.options,
            )
        )
        # advancement pending will be created after skill_choice is resolved
    elif not career_handler_invoked:
        projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))
    # If a career handler was invoked it owns the flow; _apply_skill_roll creates advancement


def _apply_auto_advance(projection: CharacterProjection, career: CareerData, event_id: int) -> None:
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
            return  # skill_table + reenlist pending deferred until after choice
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
    _queue_reenlist_or_aging(projection, event_id, 1)


def _apply_skill_choice(
    projection: CharacterProjection, event: SkillChoiceEvent, fulfilled_pending: AnyPending | None = None
) -> None:
    if isinstance(fulfilled_pending, PendingInitialTrainingChoice):
        projection.grant_skill(event.skill)
        remaining = [p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice)]
        if not remaining and projection.summary.current_career is not None:
            career = _current_career(projection)
            assignment_name = projection.summary.current_assignment or ''
            projection.pending_inputs.append(_survive_pending(career, assignment_name, event.id))
    elif isinstance(fulfilled_pending, PendingSkillTableChoice):
        projection.grant_skill(event.skill)
        if projection.summary.current_career is not None and not fulfilled_pending.reenlist_queued:
            career = _current_career(projection)
            assignment_name = projection.summary.current_assignment or ''
            projection.pending_inputs.append(_survive_pending(career, assignment_name, event.id))
    elif isinstance(fulfilled_pending, PendingCareerSkillChoice):
        projection.grant_skill(event.skill)
        if not fulfilled_pending.advancement_precreated and projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))
    elif isinstance(fulfilled_pending, PendingRankBonusChoice):
        projection.grant_skill(event.skill)
        career = _current_career(projection)
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = career.available_tables(edu, projection.summary.current_assignment or '')
        projection.pending_inputs.append(
            PendingSkillTable(id=f'{event.id}.0', instruction='Choose a skill table and roll 1D', options=tables)
        )
        _queue_reenlist_or_aging(projection, event.id, 1)
    else:
        projection.grant_skill(event.skill)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))


def _apply_advancement_dm_choice(projection: CharacterProjection, event: AdvancementDmChoiceEvent) -> None:
    projection.scheduled_effects.append(
        ScheduledEffect(trigger='advancement', source_event_id=event.id, effect={'type': 'dm', 'amount': 4})
    )
    if projection.summary.current_career is not None:
        career = _current_career(projection)
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id)
        )


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


def _apply_parole_roll(projection: CharacterProjection, event: ParoleRollEvent) -> None:
    pt = event.roll + 2
    projection.summary.parole_threshold = pt
    projection.summary.narrative.append(f'Prisoner: Parole Threshold set to {pt} (rolled {event.roll}+2)')


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
    if (
        len(projection.pending_inputs) == pending_count_before
        and projection.summary.current_career is not None
        and not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)
    ):
        # Handler applied effects directly and career is still active; advancement is next
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id)
        )
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


def _apply_life_event(projection: CharacterProjection, event: LifeEventEvent) -> None:
    if not (2 <= event.roll <= 12):
        raise ReplayError(f'Life event roll must be 2-12, got {event.roll}')
    in_career = projection.summary.current_career is not None
    career = _current_career(projection) if in_career else None
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
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id, 1)
            )
    elif roll == 3:
        # Birth or death — no mechanical effect
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id)
            )
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
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id, 1)
            )
    elif roll == 5:
        # Improved relationship — ally
        projection.summary.connections.append(Ally(source='Life event: improved relationship'))
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id)
            )
    elif roll == 6:
        # New relationship — ally
        projection.summary.connections.append(Ally(source='Life event: new relationship'))
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id)
            )
    elif roll == 7:
        # New contact
        projection.summary.connections.append(Contact(source='Life event: new contact'))
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id)
            )
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
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id, 1)
            )
    elif roll == 9:
        # Travel — DM+2 to next qualification roll
        projection.scheduled_effects.append(
            ScheduledEffect(trigger='qualification', source_event_id=event.id, effect={'type': 'dm', 'amount': 2})
        )
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id)
            )
    elif roll == 10:
        # Good fortune — DM+2 to any one Benefit roll
        projection.scheduled_effects.append(
            ScheduledEffect(trigger='muster_out', source_event_id=event.id, effect={'type': 'dm', 'amount': 2})
        )
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id)
            )
    elif roll == 11:
        # Crime — automatically lose one Benefit roll
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out_reduce', source_event_id=event.id, effect={'type': 'reduce', 'value': 1}
            )
        )
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id, 0)
            )
    elif roll == 12:
        # Unusual event — roll on unusual sub-table; advancement after that resolves
        projection.pending_inputs.append(
            PendingLifeEventUnusual(
                id=f'{event.id}.0',
                instruction='Roll 1D on Unusual Events table',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        if in_career and career is not None:
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id, 1)
            )


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
        projection.grant_skill(skill_from_str(SpaceScience.name(), 1))
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
        career = _current_career(projection) if projection.summary.current_career else None
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


def _apply_mishap_ejection(
    projection: CharacterProjection,
    career: CareerData,
    source_event_id: int,
    pending_idx: int,
    lose_current_term: bool = True,
) -> int:
    """Age the character, then handle aging roll or muster out setup for mishap ejection."""
    projection.summary.age += 4
    if projection.summary.age >= 34:
        projection.muster_out_career = career.name
        _clear_current_career(projection)
        projection.pending_inputs.append(
            PendingAgingRoll(id=f'{source_event_id}.{pending_idx}', instruction='Roll 2D on Aging table')
        )
        return pending_idx + 1
    return _apply_muster_out_setup(
        projection, career, source_event_id, pending_idx, lose_current_term=lose_current_term
    )


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
    add_effects = [se for se in projection.scheduled_effects if se.trigger == 'muster_out_add' and se.consume]
    for se in add_effects:
        roll_count += se.effect.get('value', 1)
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
    else:
        _queue_career_choice_indexed(projection, source_event_id, pending_idx)
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
        if not projection.summary.dead:
            _queue_career_choice_indexed(projection, event.id, 0, 'Start a new career, or finish character creation')


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
    elif isinstance(fulfilled_pending, (PendingAgingChoice, PendingAgingChoiceMental)) and not _check_aging_crisis(
        projection, event.id
    ):
        remaining = [
            p for p in projection.pending_inputs if isinstance(p, (PendingAgingChoice, PendingAgingChoiceMental))
        ]
        if not remaining:
            _complete_aging(projection, event.id)


def _apply_advancement(projection: CharacterProjection, event: AdvancementEvent) -> None:
    career = _current_career(projection)
    if career.name == 'Prisoner':
        _apply_prisoner_advancement(projection, event, career)
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
    success = (event.roll + dm) >= target

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
                        id=f'{event.id}.0',
                        level=bonus.level,
                        instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                        options=choices,
                    )
                )
                return  # skill_table + reenlist pending deferred until after choice
            if bonus.skill:
                projection.grant_skill(skill_from_str(bonus.skill, bonus.level))
            elif bonus.characteristic:
                char = bonus.characteristic
                projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = career.available_tables(edu, projection.summary.current_assignment or '')
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


def _apply_prisoner_advancement(projection: CharacterProjection, event: AdvancementEvent, career: CareerData) -> None:
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
        return  # reenlist deferred until after rank bonus choice resolves

    if success:
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = career.available_tables(edu, projection.summary.current_assignment or '')
        projection.pending_inputs.append(
            PendingSkillTable(id=f'{event.id}.0', instruction='Choose a skill table and roll 1D', options=tables)
        )
        _queue_reenlist_or_aging(projection, event.id, 1)
    else:
        _queue_reenlist_or_aging(projection, event.id, 0)


def _apply_commission(projection: CharacterProjection, event: CommissionEvent) -> None:
    career = _current_career(projection)
    if not event.attempt:
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id)
        )
        return
    if career.commission is None:
        raise ReplayError(f'{career.name} does not support commission')

    dm = career.commission_dm(projection)
    to_consume = [se for se in projection.scheduled_effects if se.trigger == 'advancement' and se.consume]
    for se in to_consume:
        dm += se.effect.get('amount', 0)
        projection.scheduled_effects.remove(se)
    if event.roll + dm < career.commission.target:
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id)
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
                    id=f'{event.id}.0',
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
        PendingSkillTable(id=f'{event.id}.0', instruction='Choose a skill table and roll 1D', options=tables)
    )
    _queue_reenlist_or_aging(projection, event.id, 1)


def _queue_reenlist_or_aging(projection: CharacterProjection, event_id: int, idx: int) -> None:
    # Prisoner freed via parole — head straight to muster out
    if projection.prisoner_freed:
        projection.prisoner_freed = False
        projection.summary.age += 4
        career_name = projection.summary.current_career
        careers = load_careers()
        career = careers.get(career_name) if career_name else None
        if projection.summary.age >= 34:
            if career:
                projection.muster_out_career = career.name
            projection.pending_reenlist = False  # not a mishap; use lose_current_term=False in _complete_aging
            _clear_current_career(projection)
            projection.pending_inputs.append(
                PendingAgingRoll(id=f'{event_id}.{idx}', instruction='Roll 2D on Aging table')
            )
        elif career:
            _apply_muster_out_setup(projection, career, event_id, idx, lose_current_term=False)
        return

    projection.summary.age += 4
    if projection.summary.age >= 34:
        projection.pending_inputs.append(PendingAgingRoll(id=f'{event_id}.{idx}', instruction='Roll 2D on Aging table'))
    else:
        career = _current_career(projection) if projection.summary.current_career else None
        if career and career.allows_assignment_change and len(career.assignments) > 1:
            current = projection.summary.current_assignment or ''
            others = [a.name for a in career.assignments if a.name != current]
            # Prisoner cannot muster out voluntarily; other careers always include muster_out
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


def _start_new_career_term(projection: CharacterProjection, career: CareerData, event_id: int) -> None:
    """Begin a new term in the career (same assignment). Increments term count and queues skill table."""
    _purge_career_pendings(projection)
    assignment_name = projection.summary.current_assignment or ''
    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r} in career {career.name!r}')
    career.start_new_term(projection, assignment, event_id)


def _apply_reenlist(projection: CharacterProjection, event: ReenlistEvent) -> None:
    if event.reenlist:
        career = _current_career(projection)
        _start_new_career_term(projection, career, event.id)
    else:
        _purge_career_pendings(projection)
        career = _current_career(projection)
        _apply_muster_out_setup(projection, career, event.id, 0, lose_current_term=False)


def _apply_assignment_change_choice(projection: CharacterProjection, event: AssignmentChangeChoiceEvent) -> None:
    career = _current_career(projection)
    if event.choice == 'same':
        _start_new_career_term(projection, career, event.id)
    elif event.choice == 'muster_out':
        _purge_career_pendings(projection)
        _apply_muster_out_setup(projection, career, event.id, 0, lose_current_term=False)
    else:
        # Attempt assignment change — verify the assignment exists
        new_assignment = career.assignment(event.choice)
        if new_assignment is None:
            raise ReplayError(f'Unknown assignment {event.choice!r} in career {career.name!r}')
        if event.qualification_roll is None:
            raise ReplayError(f'qualification_roll required when changing assignment to {event.choice!r}')
        char = career.qualification.characteristic
        target = career.qualification.target
        dm = characteristic_dm(projection.summary.characteristics.get(char, 0))
        if event.qualification_roll + dm >= target:
            projection.summary.current_assignment = event.choice
            _start_new_career_term(projection, career, event.id)
        else:
            # Failed qualification — character chooses to stay (same) or muster out
            projection.pending_inputs.append(
                PendingReenlist(
                    id=f'{event.id}.0',
                    instruction=(
                        f'Assignment change to {event.choice!r} failed — reenlist with '
                        f'{projection.summary.current_assignment!r} or muster out?'
                    ),
                    options=['true', 'false'],
                )
            )


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
            id=f'{event.id}.0',
            instruction=f'Choose one skill: {", ".join(choices)}',
            options=choices,
            reenlist_queued=reenlist_queued,
        )
        if reenlist_queued:
            # Insert before the aging/reenlist/muster-out pending so the skill choice resolves first
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
            projection.pending_inputs.append(_survive_pending(career, assignment_name, event.id))


def _apply_skill_table_entry(projection: CharacterProjection, entry: SkillTableEntry) -> None:
    if entry.characteristic:
        char = entry.characteristic
        projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + 1
    elif entry.skill:
        projection.increment_skill(entry.skill, entry.spec)


# ── helpers ──────────────────────────────────────────────────────────────────


def _advancement_pending(
    career: CareerData, assignment_name: str, event_id: int, pending_idx: int = 0
) -> PendingAdvancement:
    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r}')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    return PendingAdvancement(id=f'{event_id}.{pending_idx}', instruction=f'Advancement: {char} {target}+')


def _career_progress_pending(
    career: CareerData, projection: CharacterProjection, event_id: int, pending_idx: int = 0
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
    return _advancement_pending(career, projection.summary.current_assignment or '', event_id, pending_idx)


def _current_career(projection: CharacterProjection) -> CareerData:
    career_name = projection.summary.current_career
    if career_name is None:
        raise ReplayError('No active career')
    careers = load_careers()
    career = careers.get(career_name)
    if career is None:
        raise ReplayError(f'Unknown career: {career_name!r}')
    return career


def _apply_simple_effect(
    projection: CharacterProjection, effect: AnyEffect, source: str = '', source_event_id: int = 0
) -> None:
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


def _apply_connections_roll(projection: CharacterProjection, event: ConnectionsRollEvent) -> None:
    for _ in range(event.count):
        projection.summary.connections.append(make_connection(event.connection_type))


# ── pre-career education ──────────────────────────────────────────────────────


def _apply_precareer_entry(projection: CharacterProjection, event: PreCareerEntryEvent) -> None:
    from ceres.character.precareers.loader import load_precareers

    precareer = load_precareers().get(event.precareer)
    if precareer is None:
        raise ReplayError(f'Unknown pre-career: {event.precareer!r}')
    if projection.summary.term_count >= 3:
        raise ReplayError('Pre-career education is only available in terms 1–3')
    if projection.summary.precareer_completed is not None:
        raise ReplayError('A character may only attend one pre-career')

    dm = 0
    if precareer.entry is not None:
        char_val = projection.summary.characteristics.get(precareer.entry.characteristic, 0)
        dm += characteristic_dm(char_val)
        # DM-N based on which term this is (term_count is 0-based before this term)
        term_dm = precareer.entry_term_dms.get(projection.summary.term_count + 1, 0)
        dm += term_dm
        if precareer.entry_soc_bonus_min is not None:
            soc = projection.summary.characteristics.get(Chars.SOC, 0)
            if soc >= precareer.entry_soc_bonus_min:
                dm += precareer.entry_soc_bonus
        if event.roll == 2 or event.roll + dm < precareer.entry.target:
            # Entry failed — must enter a career this term
            _queue_career_choice(projection, event.id, 'Pre-career entry failed — choose a career')
            return

    # Entry successful
    projection.summary.precareer = event.precareer
    projection.summary.term_count += 1
    projection.summary.age += 4
    pending_idx = 0

    pending_idx = precareer.apply_entry(projection, event, pending_idx)

    projection.pending_inputs.append(
        PendingPreCareerEvent(
            id=f'{event.id}.{pending_idx}',
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
                id=f'{event.id}.{pending_idx}',
                instruction=instruction,
            )
        )
    elif precareer.graduation_requirement is not None:
        projection.pending_inputs.append(
            PendingPreCareerGraduation(
                id=f'{event.id}.{pending_idx}',
                instruction=f'Graduation: {precareer.graduation_requirement}',
            )
        )


def _apply_precareer_skill_choice(
    projection: CharacterProjection,
    event: PreCareerSkillChoiceEvent,
    fulfilled_pending: AnyPending | None,
) -> None:
    level = fulfilled_pending.level if isinstance(fulfilled_pending, PendingPreCareerSkillChoice) else 0
    skill_name, spec = parse_skill_spec_option(event.skill)
    if level == 0:
        projection.grant_skill(skill_from_str(skill_name, 0))
    else:
        projection.increment_skill(skill_name, spec)
    projection.summary.precareer_skills.append(event.skill)


def _apply_precareer_event(projection: CharacterProjection, event: PreCareerEventEvent) -> None:
    from ceres.character.precareers.loader import load_precareers

    precareer_name = projection.summary.precareer
    if precareer_name is None:
        raise ReplayError('No active pre-career for pre-career event')
    precareer = load_precareers().get(precareer_name)
    if precareer is None:
        raise ReplayError(f'Unknown pre-career: {precareer_name!r}')

    term_event = precareer.events.get(event.roll)
    if term_event is None:
        raise ReplayError(f'No pre-career event entry for roll {event.roll}')

    projection.summary.narrative.append(f'Pre-career event ({precareer_name}): {term_event.text}')
    pending_idx = 0

    # Events 3 and 11 force a graduation failure
    if event.roll in (3, 11):
        if event.roll == 11:
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
        _queue_career_choice(projection, event.id, 'Pre-career ended (no graduation) — choose a career')
        return

    # Handle effects
    for effect in term_event.effects:
        if isinstance(effect, GainConnectionsRolledEffect):
            max_count = {'d3': 3, '1d3': 3, 'd6': 6}.get(effect.dice.lower(), 3)
            projection.pending_inputs.append(
                PendingConnectionsRoll(
                    id=f'{event.id}.{pending_idx}',
                    connection_type=effect.connection_type,
                    instruction=f'Roll {effect.dice.upper()} for number of {effect.connection_type}s gained',
                    options=[str(i) for i in range(1, max_count + 1)],
                )
            )
            pending_idx += 1
        elif isinstance(effect, SkillChoiceEffect):
            all_skills = sorted(cls.name() for cls in _skill_classes(AnySkill) if cls.name() != 'Jack-of-All-Trades')
            opts = effect.options or all_skills
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.{pending_idx}',
                    instruction='Choose any skill at level 0',
                    options=opts,
                )
            )
            pending_idx += 1
        elif isinstance(effect, LifeEventEffect):
            projection.pending_inputs.append(
                PendingLifeEvent(
                    id=f'{event.id}.{pending_idx}',
                    instruction='Roll 2D on Life Events table',
                )
            )
            pending_idx += 1
        else:
            _apply_simple_effect(projection, effect, source=term_event.text, source_event_id=event.id)

    # Event 12: SOC +1 (not captured in effects data)
    if event.roll == 12:
        projection.summary.characteristics[Chars.SOC] = projection.summary.characteristics.get(Chars.SOC, 0) + 1
    # Events 2 and 4: note for manual handling
    elif event.roll == 2:
        projection.summary.problems.append(
            'Pre-career event 2: you may test your PSI and attempt to enter the Psion career '
            'in any subsequent term (apply manually).'
        )
    elif event.roll == 4:
        projection.summary.problems.append(
            'Pre-career event 4: roll SOC 8+ — success: gain Rival; failure: gain Enemy. '
            'Natural 2: also fail to graduate and must take Prisoner career next term. Apply manually.'
        )


def _apply_precareer_graduation(projection: CharacterProjection, event: PreCareerGraduationEvent) -> None:
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
            # Parse 'END_8+' → check END >= 8
            try:
                char_name, threshold_str = key.split('_', 1)
                threshold = int(threshold_str.rstrip('+'))
                char = Chars(char_name)
                if projection.summary.characteristics.get(char, 0) >= threshold:
                    dm += dm_val
            except ValueError, KeyError:
                pass
        effective = event.roll + dm
        graduated = event.roll != 2 and effective >= precareer.graduation.target
        if precareer.honours_target is not None:
            honours = effective >= precareer.honours_target
    elif precareer.honours_target is not None:
        # graduation_requirement is text-based (e.g. PSI 6+); use raw roll for honours
        honours = event.roll >= precareer.honours_target

    # Index for the career choice pending — companion handlers advance this to avoid ID collisions
    pending_graduation_idx = 0

    if graduated:
        projection.summary.narrative.append(f'Graduated from {precareer_name}' + (' with honours!' if honours else '.'))
        pending_graduation_idx = precareer.apply_graduation(projection, event, honours)
    else:
        projection.summary.narrative.append(f'Did not graduate from {precareer_name}.')
        precareer.apply_failed_graduation(projection, event)

    projection.summary.precareer_completed = precareer_name
    projection.summary.precareer = None
    projection.summary.precareer_skills = []
    _queue_career_choice_indexed(projection, event.id, pending_graduation_idx, 'Pre-career complete — choose a career')


# ── characteristic DM and UCP parsing ────────────────────────────────────────


def _parse_ucp(ucp: str, sophont: object = None) -> dict[Chars, int]:
    from ceres.character.sophonts import Sophont

    ucp_stats = sophont.ucp_stats if isinstance(sophont, Sophont) else UCP_STATS
    if len(ucp) != len(ucp_stats):
        raise ReplayError(f'Invalid UCP: {ucp!r} — expected {len(ucp_stats)} hex digits')
    return {stat: int(digit, 16) for stat, digit in zip(ucp_stats, ucp, strict=True)}


def _background_skill_count(edu: int) -> int:
    return max(0, characteristic_dm(edu) + 3)
