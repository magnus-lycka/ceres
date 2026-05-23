from collections.abc import Sequence
from typing import Literal, cast

from ceres.character.careers.career_data import CareerData, SkillTableEntry
from ceres.character.careers.loader import get_effect_handler, get_skill_roll_handler, load_careers
from ceres.character.characteristics import UCP_STATS
from ceres.character.events import (
    AdvancementDmChoiceEvent,
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    AnyEvent,
    BackgroundSkillsEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    ConnectionKindChoiceEvent,
    ConnectionsRollEvent,
    InjuryTableEvent,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
    ReenlistEvent,
    ScholarEvent3ChoiceEvent,
    ScholarEvent8ChoiceEvent,
    ScholarMishap3ChoiceEvent,
    ScholarMishap5ChoiceEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.projection import CharacterProjection, CharacterSummary, Connection, PendingInput, ScheduledEffect
from ceres.character.skills import (
    AnySkill,
    BackgroundSkill,
    Level,
    ScienceSkill,
    Skill,
    SpaceScience,
    _skill_classes,
    skill_class_by_name,
    skill_list,
)

BACKGROUND_SKILLS: frozenset[type[Skill]] = frozenset(_skill_classes(BackgroundSkill))

_SCHOLAR_SCIENCES = sorted(s.type for s in skill_list(ScienceSkill))


class ReplayError(Exception):
    pass


def replay(character_id: int, events: Sequence[AnyEvent]) -> CharacterProjection:
    projection = CharacterProjection(character_id=character_id)
    for event in events:
        _apply(projection, event)
    return projection


def _apply(projection: CharacterProjection, event: AnyEvent) -> None:
    fulfilled_kind: str | None = None
    if event.fulfills is not None:
        fulfilled_kind = next((p.kind for p in projection.pending_inputs if p.id == event.fulfills), None)
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
            _apply_skill_choice(projection, event, fulfilled_kind)
        case AdvancementDmChoiceEvent():
            _apply_advancement_dm_choice(projection, event, fulfilled_kind)
        case ConnectionKindChoiceEvent():
            _apply_connection_kind_choice(projection, event, fulfilled_kind)
        case ScholarEvent3ChoiceEvent():
            _apply_scholar_event3_choice(projection, event)
        case ScholarEvent8ChoiceEvent():
            _apply_scholar_event8_choice(projection, event)
        case ScholarMishap3ChoiceEvent():
            _apply_scholar_mishap3_choice(projection, event)
        case ScholarMishap5ChoiceEvent():
            _apply_scholar_mishap5_choice(projection, event)
        case AdvancementEvent():
            _apply_advancement(projection, event)
        case ReenlistEvent():
            _apply_reenlist(projection, event)
        case SkillTableEvent():
            _apply_skill_table(projection, event)
        case CharacteristicChoiceEvent():
            _apply_characteristic_choice(projection, event, fulfilled_kind)
        case ConnectionsRollEvent():
            _apply_connections_roll(projection, event)
        case SkillRollEvent():
            _apply_skill_roll(projection, event)
        case InjuryTableEvent():
            _apply_injury_table(projection, event)
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


def _apply_character_started(projection: CharacterProjection, event: CharacterStartedEvent) -> None:
    projection.summary = CharacterSummary(name=event.name, species=event.sophont)
    projection.pending_inputs.append(
        PendingInput(id=f'{event.id}.0', kind='ucp', instruction='Provide characteristics (UCP)')
    )


def _apply_ucp(projection: CharacterProjection, event: UcpEvent) -> None:
    projection.summary.characteristics = _parse_ucp(event.ucp)
    edu = projection.summary.characteristics.get('EDU', 0)
    count = _background_skill_count(edu)
    if count > 0:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='background_skills',
                instruction=f'Choose {count} background skill(s)',
                options=sorted(cls.name() for cls in BACKGROUND_SKILLS),
            )
        )


def _apply_background_skills(projection: CharacterProjection, event: BackgroundSkillsEvent) -> None:
    edu = projection.summary.characteristics.get('EDU', 0)
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
        PendingInput(
            id=f'{event.id}.0',
            kind='career',
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
            PendingInput(
                id=f'{event.id}.0',
                kind='career',
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
        # First term: initial training — all service skills at level 0
        service_table = career.skill_tables['service_skills']
        for entry in service_table.entries.values():
            _apply_initial_training_entry(projection, entry)

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
) -> PendingInput:
    assignment = career.assignment(assignment_name)
    if assignment is None:
        raise ReplayError(f'Unknown assignment {assignment_name!r} in career {career.name!r}')
    char = assignment.survival.characteristic
    target = assignment.survival.target
    return PendingInput(id=f'{event_id}.0', kind='survive', instruction=f'Survive: {char} {target}+')


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
        projection.pending_inputs.append(
            PendingInput(id=f'{event.id}.0', kind='term_event', instruction='Roll 2D on Events table')
        )
    else:
        projection.pending_inputs.append(
            PendingInput(id=f'{event.id}.0', kind='mishap', instruction='Roll 1D on Mishap table')
        )


def _apply_mishap(projection: CharacterProjection, event: MishapEvent) -> None:
    career = _current_career(projection)
    mishap = career.mishaps.get(event.roll)
    pending_idx = 0
    if mishap:
        projection.summary.problems.append(mishap.text)
        for effect in mishap.effects:
            if effect.type == 'decrease_characteristic_choice':
                options = list(getattr(effect, 'options', []))
                amount = getattr(effect, 'amount', 1)
                projection.pending_inputs.append(
                    PendingInput(
                        id=f'{event.id}.{pending_idx}',
                        kind='characteristic_choice',
                        instruction=f'Choose characteristic to decrease by {amount}: {", ".join(options)}',
                        options=options,
                    )
                )
                pending_idx += 1
            elif effect.type == 'gain_connections_rolled':
                connection_type = getattr(effect, 'connection_type', 'contact')
                dice = getattr(effect, 'dice', '1d6')
                projection.pending_inputs.append(
                    PendingInput(
                        id=f'{event.id}.{pending_idx}',
                        kind='connections_roll',
                        instruction=f'Roll {dice.upper()} for number of {connection_type}s',
                        options=[str(i) for i in range(1, 7)],
                    )
                )
                pending_idx += 1
            elif effect.type == 'skill_choice':
                options = list(getattr(effect, 'options', []))
                projection.pending_inputs.append(
                    PendingInput(
                        id=f'{event.id}.{pending_idx}',
                        kind='skill_choice',
                        instruction=f'Choose one skill: {", ".join(options)}',
                        options=options,
                    )
                )
                pending_idx += 1
            elif effect.type == 'injury':
                severity = getattr(effect, 'severity', 'normal')
                if severity == 'normal':
                    projection.pending_inputs.append(
                        PendingInput(
                            id=f'{event.id}.{pending_idx}',
                            kind='characteristic_choice',
                            instruction='Injured: choose STR, DEX, or END to reduce by 1',
                            options=['STR', 'DEX', 'END'],
                        )
                    )
                    pending_idx += 1
                elif severity == 'severe':
                    projection.pending_inputs.append(
                        PendingInput(
                            id=f'{event.id}.{pending_idx}',
                            kind='characteristic_choice',
                            instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                            options=['STR', 'DEX', 'END'],
                        )
                    )
                    pending_idx += 1
                elif severity == 'from_table':
                    projection.pending_inputs.append(
                        PendingInput(
                            id=f'{event.id}.{pending_idx}',
                            kind='injury_table',
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
    stay = event.stay_in_career or (mishap is not None and mishap.stay_in_career)
    if stay:
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id, pending_idx))
    else:
        projection.summary.age += 4
        if projection.summary.age >= 34:
            # Save career for muster out after aging resolves (mishap = lose current term)
            projection.muster_out_career = career.name
            projection.summary.current_career = None
            projection.summary.current_assignment = None
            projection.pending_inputs.append(
                PendingInput(id=f'{event.id}.{pending_idx}', kind='aging_roll', instruction='Roll 2D on Aging table')
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
        projection.pending_inputs.append(
            PendingInput(id=f'{event.id}.{pending_idx}', kind='mishap', instruction=instruction)
        )
        # advancement pending created when mishap resolves with stay_in_career=True
    elif auto_advance:
        _apply_auto_advance(projection, career, event.id)
    elif life_event_pending:
        projection.pending_inputs.append(
            PendingInput(id=f'{event.id}.{pending_idx}', kind='life_event', instruction='Roll 2D on Life Events table')
        )
        # advancement pending created by _apply_life_event or _apply_life_event_unusual
    elif skill_choice_effect is not None:
        options = list(getattr(skill_choice_effect, 'options', []))
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.{pending_idx}',
                kind='skill_choice',
                instruction=f'Choose one skill: {", ".join(options)}',
                options=options,
            )
        )
        # advancement pending will be created after skill_choice is resolved
    elif not career_handler_invoked:
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    # If a career handler was invoked it owns the flow; _apply_skill_roll creates advancement


def _apply_auto_advance(projection: CharacterProjection, career: CareerData, event_id: int) -> None:
    new_rank = (projection.summary.rank or 0) + 1
    projection.summary.rank = new_rank
    assignment_name = projection.summary.current_assignment or ''
    rank_entry = career.assignment_ranks(assignment_name).get(new_rank)
    if rank_entry and rank_entry.bonus:
        bonus = rank_entry.bonus
        if bonus.choices:
            projection.pending_inputs.append(
                PendingInput(
                    id=f'{event_id}.0',
                    kind=f'rank_bonus_choice_{bonus.level}',
                    instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                    options=bonus.choices,
                )
            )
            return  # reenlist pending deferred until after choice
        elif bonus.skill:
            _grant_skill(projection, _skill_from_str(bonus.skill, bonus.level))
        elif bonus.characteristic:
            char = bonus.characteristic
            projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.0', kind='reenlist', instruction='Reenlist or muster out?', options=['true', 'false']
        )
    )


def _apply_skill_choice(
    projection: CharacterProjection, event: SkillChoiceEvent, fulfilled_kind: str | None = None
) -> None:
    if fulfilled_kind == 'skill_table_choice':
        _grant_skill(projection, event.skill)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            assignment_name = projection.summary.current_assignment or ''
            projection.pending_inputs.append(_survive_pending(projection, career, assignment_name, event.id))
    elif fulfilled_kind in ('scout_event_11', 'scholar_event_11'):
        _grant_skill(projection, event.skill)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif fulfilled_kind == 'scholar_event_3_science':
        _grant_skill(projection, event.skill)
        # advancement was created when 'accept' was chosen
    elif fulfilled_kind == 'scholar_mishap_3_science':
        _grant_skill(projection, event.skill)
        # advancement was pre-created by _apply_mishap
    elif fulfilled_kind and fulfilled_kind.startswith('rank_bonus_choice_'):
        _grant_skill(projection, event.skill)
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0', kind='reenlist', instruction='Reenlist or muster out?', options=['true', 'false']
            )
        )
    else:
        _grant_skill(projection, event.skill)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id))


def _apply_advancement_dm_choice(
    projection: CharacterProjection, event: AdvancementDmChoiceEvent, fulfilled_kind: str | None = None
) -> None:
    projection.scheduled_effects.append(
        ScheduledEffect(trigger='advancement', source_event_id=event.id, effect={'type': 'dm', 'amount': 4})
    )
    if projection.summary.current_career is not None:
        career = _current_career(projection)
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))


def _apply_connection_kind_choice(
    projection: CharacterProjection, event: ConnectionKindChoiceEvent, fulfilled_kind: str | None = None
) -> None:
    projection.summary.connections.append(
        Connection(kind=event.connection_kind, source=f'Life event: {fulfilled_kind or "unknown"}')
    )
    # advancement was pre-created by _apply_life_event


def _apply_scholar_event3_choice(projection: CharacterProjection, event: ScholarEvent3ChoiceEvent) -> None:
    if event.choice == 'accept':
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='connections_roll',
                instruction='Roll D3 for number of Enemies gained',
                options=['1', '2', '3'],
            )
        )
        for i, label in enumerate(['first', 'second'], start=1):
            projection.pending_inputs.append(
                PendingInput(
                    id=f'{event.id}.{i}',
                    kind='scholar_event_3_science',
                    instruction=f'Choose {label} Science specialty to gain at level 1',
                    options=_SCHOLAR_SCIENCES,
                )
            )
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id, 3))
    else:
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id))


def _apply_scholar_event8_choice(projection: CharacterProjection, event: ScholarEvent8ChoiceEvent) -> None:
    if event.choice == 'refuse':
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    else:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='scholar_event_8_roll',
                instruction='Roll Deception 8+ or Admin 8+ to cheat successfully',
                options=['Deception', 'Admin'],
            )
        )


def _apply_scholar_mishap3_choice(projection: CharacterProjection, event: ScholarMishap3ChoiceEvent) -> None:
    if event.choice == 'openly':
        projection.summary.connections.append(Connection(kind='enemy', source='Planetary government interference'))
    else:
        soc = projection.summary.characteristics.get('SOC', 0)
        projection.summary.characteristics['SOC'] = max(0, soc - 2)
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event.id}.0',
            kind='scholar_mishap_3_science',
            instruction='Increase Science by one level: choose which broad science',
            options=_SCHOLAR_SCIENCES,
        )
    )
    # advancement was already created by _apply_mishap (stay_in_career=True)


def _apply_scholar_mishap5_choice(projection: CharacterProjection, event: ScholarMishap5ChoiceEvent) -> None:
    if event.choice == 'give_up':
        projection.pending_inputs = [p for p in projection.pending_inputs if p.kind != 'advancement']
        projection.summary.current_career = None
        projection.summary.current_assignment = None
        projection.summary.age += 4
    # 'start_again': advancement is already there from _apply_mishap, career stays


def _apply_skill_roll(projection: CharacterProjection, event: SkillRollEvent) -> None:
    career = _current_career(projection)
    handler = get_skill_roll_handler(career.name, event.context)
    pending_count_before = len(projection.pending_inputs)
    if handler:
        handler(projection, event)
    if len(projection.pending_inputs) == pending_count_before:
        # Handler applied effects directly; advancement is next
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    # Otherwise handler created its own pending (skill_choice or mishap-stay); it leads to advancement


def _apply_injury_table(projection: CharacterProjection, event: InjuryTableEvent) -> None:
    if not (1 <= event.roll <= 6):
        raise ReplayError(f'Injury table roll must be 1-6, got {event.roll}')
    if event.roll == 6:
        return  # lightly injured — no permanent effect
    elif event.roll == 5:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='characteristic_choice',
                instruction='Injured: choose STR, DEX, or END to reduce by 1',
                options=['STR', 'DEX', 'END'],
            )
        )
    elif event.roll == 4:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='characteristic_choice',
                instruction='Scarred: choose STR, DEX, or END to reduce by 2',
                options=['STR', 'DEX', 'END'],
            )
        )
    elif event.roll == 3:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='characteristic_choice',
                instruction='Missing Eye or Limb: choose STR or DEX to reduce by 2',
                options=['STR', 'DEX'],
            )
        )
    elif event.roll == 2:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='characteristic_choice',
                instruction='Severely injured: roll 1D — choose STR, DEX, or END to reduce by that amount',
                options=['STR', 'DEX', 'END'],
            )
        )
    elif event.roll == 1:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='nearly_killed',
                instruction=(
                    'Nearly killed: roll 1D — choose STR, DEX, or END to reduce by that amount; '
                    'the other two physical characteristics are each reduced by 2'
                ),
                options=['STR', 'DEX', 'END'],
            )
        )


def _apply_life_event(projection: CharacterProjection, event: LifeEventEvent) -> None:
    if not (2 <= event.roll <= 12):
        raise ReplayError(f'Life event roll must be 2-12, got {event.roll}')
    career = _current_career(projection)
    roll = event.roll
    if roll == 2:
        # Sickness or injury — roll on injury table, advancement after that resolves
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='injury_table',
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
            PendingInput(
                id=f'{event.id}.0',
                kind='life_event_4',
                instruction='Ending relationship: gain a rival or enemy?',
                options=['rival', 'enemy'],
            )
        )
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id, 1))
    elif roll == 5:
        # Improved relationship — ally
        projection.summary.connections.append(Connection(kind='ally', source='Life event: improved relationship'))
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 6:
        # New relationship — ally
        projection.summary.connections.append(Connection(kind='ally', source='Life event: new relationship'))
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 7:
        # New contact
        projection.summary.connections.append(Connection(kind='contact', source='Life event: new contact'))
        projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif roll == 8:
        # Betrayal — gain rival or enemy
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='life_event_8',
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
            PendingInput(
                id=f'{event.id}.0',
                kind='life_event_unusual',
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
        projection.summary.connections.append(Connection(kind='ally', source='Unusual event: useful ally'))
    elif roll == 2:
        # Aliens — gain contact + any science skill at level 1
        projection.summary.connections.append(Connection(kind='contact', source='Unusual event: alien contact'))
        _grant_skill(projection, _skill_from_str(SpaceScience.name(), 1))
    # rolls 3-6: no mechanical effect in Explorer edition
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
            PendingInput(
                id=f'{event.id}.{pending_idx}',
                kind='aging_choice',
                instruction='Aging: choose STR, DEX, or END to reduce by 1',
                options=['STR', 'DEX', 'END'],
            )
        )
    elif effective == -1:
        for _ in range(2):
            projection.pending_inputs.append(
                PendingInput(
                    id=f'{event.id}.{pending_idx}',
                    kind='aging_choice',
                    instruction='Aging: choose STR, DEX, or END to reduce by 1',
                    options=['STR', 'DEX', 'END'],
                )
            )
            pending_idx += 1
    elif effective == -2:
        for char in ('STR', 'DEX', 'END'):
            projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 1)
        if not _check_aging_crisis(projection, event.id):
            _complete_aging(projection, event.id)
    elif effective == -3:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.{pending_idx}',
                kind='aging_choice',
                instruction='Aging: choose STR, DEX, or END to reduce by 2',
                options=['STR', 'DEX', 'END'],
            )
        )
        pending_idx += 1
        for _ in range(2):
            projection.pending_inputs.append(
                PendingInput(
                    id=f'{event.id}.{pending_idx}',
                    kind='aging_choice',
                    instruction='Aging: choose STR, DEX, or END to reduce by 1',
                    options=['STR', 'DEX', 'END'],
                )
            )
            pending_idx += 1
    elif effective == -4:
        for _ in range(2):
            projection.pending_inputs.append(
                PendingInput(
                    id=f'{event.id}.{pending_idx}',
                    kind='aging_choice',
                    instruction='Aging: choose STR, DEX, or END to reduce by 2',
                    options=['STR', 'DEX', 'END'],
                )
            )
            pending_idx += 1
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.{pending_idx}',
                kind='aging_choice',
                instruction='Aging: choose STR, DEX, or END to reduce by 1',
                options=['STR', 'DEX', 'END'],
            )
        )
    elif effective == -5:
        for char in ('STR', 'DEX', 'END'):
            projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 2)
        if not _check_aging_crisis(projection, event.id):
            _complete_aging(projection, event.id)
    else:  # <= -6
        for char in ('STR', 'DEX', 'END'):
            projection.summary.characteristics[char] = max(0, projection.summary.characteristics.get(char, 0) - 2)
        if not _check_aging_crisis(projection, event.id):
            projection.pending_inputs.append(
                PendingInput(
                    id=f'{event.id}.0',
                    kind='aging_choice_mental',
                    instruction='Aging: choose INT or SOC to reduce by 1',
                    options=['INT', 'SOC'],
                )
            )


def _complete_aging(projection: CharacterProjection, source_event_id: int) -> None:
    if projection.pending_reenlist is True:
        projection.summary.term_count += 1
        career = _current_career(projection)
        tables = sorted(career.skill_tables.keys())
        projection.pending_inputs.append(
            PendingInput(
                id=f'{source_event_id}.0',
                kind='skill_table',
                instruction='Choose a skill table and roll 1D',
                options=tables,
            )
        )
    elif projection.muster_out_career is not None:
        # reenlist=False (pending_reenlist=False) or mishap ejection (pending_reenlist=None)
        careers = load_careers()
        career = careers.get(projection.muster_out_career)
        lose = projection.pending_reenlist is None  # None=mishap path → lose current term
        projection.muster_out_career = None  # reset before setup re-sets it if needed
        if career:
            _apply_muster_out_setup(projection, career, source_event_id, 0, lose_current_term=lose, clear_career=False)
    projection.pending_reenlist = None


def _check_aging_crisis(projection: CharacterProjection, source_event_id: int) -> bool:
    if any(v == 0 for v in projection.summary.characteristics.values()):
        projection.pending_inputs = [
            p for p in projection.pending_inputs if p.kind not in ('aging_choice', 'aging_choice_mental')
        ]
        projection.pending_inputs.append(
            PendingInput(
                id=f'{source_event_id}.crisis',
                kind='aging_crisis',
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
        if projection.pending_reenlist is True:
            projection.summary.term_count += 1
        projection.pending_reenlist = None
        projection.muster_out_career = None
        if career:
            _apply_muster_out_setup(projection, career, event.id, 0, clear_career=True)
        else:
            projection.summary.current_career = None
            projection.summary.current_assignment = None
    else:
        projection.summary.dead = True
        projection.summary.current_career = None
        projection.summary.current_assignment = None
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
        projection.summary.current_career = None
        projection.summary.current_assignment = None
    if roll_count > 0:
        projection.muster_out_career = career.name
        for _ in range(roll_count):
            projection.pending_inputs.append(
                PendingInput(
                    id=f'{source_event_id}.{pending_idx}',
                    kind='muster_out',
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
        _apply_muster_out_benefit(projection, row.benefit)

    remaining = [p for p in projection.pending_inputs if p.kind == 'muster_out']
    if not remaining:
        projection.muster_out_career = None


def _apply_muster_out_benefit(projection: CharacterProjection, benefit: str) -> None:
    if benefit in ('int_plus_1', 'edu_plus_1', 'soc_plus_1'):
        char = benefit.split('_')[0].upper()
        current = projection.summary.characteristics.get(char, 0)
        projection.summary.characteristics[char] = min(15, current + 1)
    elif benefit == 'two_ship_shares':
        projection.summary.benefits.extend(['ship_share', 'ship_share'])
    else:
        projection.summary.benefits.append(benefit)


def _apply_characteristic_choice(
    projection: CharacterProjection, event: CharacteristicChoiceEvent, fulfilled_kind: str | None = None
) -> None:
    char = event.characteristic
    current = projection.summary.characteristics.get(char, 0)
    projection.summary.characteristics[char] = max(0, current - event.amount)
    if fulfilled_kind == 'nearly_killed':
        for other in ('STR', 'DEX', 'END'):
            if other != char:
                projection.summary.characteristics[other] = max(0, projection.summary.characteristics.get(other, 0) - 2)
    elif fulfilled_kind in ('aging_choice', 'aging_choice_mental'):
        if not _check_aging_crisis(projection, event.id):
            remaining = [p for p in projection.pending_inputs if p.kind in ('aging_choice', 'aging_choice_mental')]
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
            if bonus.choices:
                projection.pending_inputs.append(
                    PendingInput(
                        id=f'{event.id}.0',
                        kind=f'rank_bonus_choice_{bonus.level}',
                        instruction=f'Rank {new_rank} bonus: choose skill at level {bonus.level}',
                        options=bonus.choices,
                    )
                )
                return  # reenlist pending deferred until after choice
            elif bonus.skill:
                _grant_skill(projection, _skill_from_str(bonus.skill, bonus.level))
            elif bonus.characteristic:
                char = bonus.characteristic
                projection.summary.characteristics[char] = projection.summary.characteristics.get(char, 0) + bonus.level

    projection.pending_inputs.append(
        PendingInput(
            id=f'{event.id}.0',
            kind='reenlist',
            instruction='Reenlist or muster out?',
            options=['true', 'false'],
        )
    )


def _apply_reenlist(projection: CharacterProjection, event: ReenlistEvent) -> None:
    projection.summary.age += 4
    if projection.summary.age >= 34:
        projection.pending_reenlist = event.reenlist
        if not event.reenlist:
            # Save career for muster out after aging resolves
            projection.muster_out_career = projection.summary.current_career
            projection.summary.current_career = None
            projection.summary.current_assignment = None
        # term_count and skill_table pending deferred to _complete_aging after aging resolves
        projection.pending_inputs.append(
            PendingInput(id=f'{event.id}.0', kind='aging_roll', instruction='Roll 2D on Aging table')
        )
    elif event.reenlist:
        career = _current_career(projection)
        projection.summary.term_count += 1
        assignment_name = projection.summary.current_assignment or ''
        assignment = career.assignment(assignment_name)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {assignment_name!r} in career {career.name!r}')
        tables = sorted(career.skill_tables.keys())
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='skill_table',
                instruction='Choose a skill table and roll 1D',
                options=tables,
            )
        )
    else:
        career = _current_career(projection)
        _apply_muster_out_setup(projection, career, event.id, 0, lose_current_term=False)


def _apply_skill_table(projection: CharacterProjection, event: SkillTableEvent) -> None:
    career = _current_career(projection)
    table = career.skill_tables.get(event.table)
    if table is None:
        raise ReplayError(f'Unknown skill table: {event.table!r}')
    if table.min_edu is not None:
        edu = projection.summary.characteristics.get('EDU', 0)
        if edu < table.min_edu:
            raise ReplayError(f'Table {event.table!r} requires EDU {table.min_edu}+, character has {edu}')
    if not (1 <= event.roll <= 6):
        raise ReplayError(f'Skill table roll must be 1-6, got {event.roll}')
    entry = table.entries.get(event.roll)
    if entry is None:
        raise ReplayError(f'No entry for roll {event.roll} in table {event.table!r}')
    assignment_name = projection.summary.current_assignment or ''
    if entry.choices:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='skill_table_choice',
                instruction=f'Choose one skill: {", ".join(entry.choices)}',
                options=entry.choices,
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
) -> PendingInput:
    assignment = career.assignment(projection.summary.current_assignment or '')
    if assignment is None:
        raise ReplayError(f'Unknown assignment {projection.summary.current_assignment!r}')
    char = assignment.advancement.characteristic
    target = assignment.advancement.target
    return PendingInput(
        id=f'{event_id}.{pending_idx}', kind='advancement', instruction=f'Advancement: {char} {target}+'
    )


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
    from typing import Any

    skill_cls = skill_class_by_name(skill_name)
    existing = next((s for s in projection.summary.skills if type(s) is skill_cls), None)
    if existing is None:
        _cls: Any = skill_cls
        projection.summary.skills.append(cast(AnySkill, _cls()))
        return
    choices = projection.skill_choices([skill_cls], None)
    if choices:
        _grant_skill(projection, choices[0])


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
        projection.summary.connections.append(Connection(kind=kind, source=source))
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
        projection.summary.connections.append(Connection(kind=event.connection_type, source=''))


# ── characteristic DM and UCP parsing ────────────────────────────────────────


def _parse_ucp(ucp: str) -> dict[str, int]:
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
