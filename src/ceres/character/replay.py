from collections.abc import Sequence
from typing import Literal, cast

from ceres.character.careers.career_data import CareerData, SkillTableEntry
from ceres.character.careers.loader import get_effect_handler, get_skill_roll_handler, load_careers
from ceres.character.characteristics import UCP_STATS
from ceres.character.events import (
    AdvancementEvent,
    AnyEvent,
    BackgroundSkillsEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    ConnectionsRollEvent,
    MishapEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.projection import CharacterProjection, CharacterSummary, Connection, PendingInput, ScheduledEffect

# All skill types valid as background skills in the Explorer edition.
# Art, Profession, and Science are represented by their specific subtypes.
BACKGROUND_SKILLS: frozenset[str] = frozenset(
    {
        'Admin',
        'Animals',
        'Performing Art',
        'Creative Art',
        'Presentation Art',
        'Athletics',
        'Carouse',
        'Drive',
        'Electronics',
        'Flyer',
        'Language',
        'Mechanic',
        'Medic',
        'Colonist Profession',
        'Crewmember Profession',
        'Freeloader Profession',
        'Hostile Environment Profession',
        'Spacer Profession',
        'Sport Profession',
        'Worker Profession',
        'Life Science',
        'Physical Science',
        'Robotic Science',
        'Social Science',
        'Space Science',
        'Seafarer',
        'Streetwise',
        'Survival',
        'Vacc Suit',
    }
)


_SCHOLAR_SCIENCES = sorted(['Life Science', 'Physical Science', 'Robotic Science', 'Social Science', 'Space Science'])


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
        case AdvancementEvent():
            _apply_advancement(projection, event)
        case ReenlistEvent():
            _apply_reenlist(projection, event)
        case SkillTableEvent():
            _apply_skill_table(projection, event)
        case CharacteristicChoiceEvent():
            _apply_characteristic_choice(projection, event)
        case ConnectionsRollEvent():
            _apply_connections_roll(projection, event)
        case SkillRollEvent():
            _apply_skill_roll(projection, event)


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
                options=sorted(BACKGROUND_SKILLS),
            )
        )


def _apply_background_skills(projection: CharacterProjection, event: BackgroundSkillsEvent) -> None:
    edu = projection.summary.characteristics.get('EDU', 0)
    expected = _background_skill_count(edu)
    if len(event.skills) != expected:
        raise ReplayError(f'Expected {expected} background skill(s), got {len(event.skills)}')
    invalid = [s for s in event.skills if s not in BACKGROUND_SKILLS]
    if invalid:
        raise ReplayError(f'Invalid background skill(s): {", ".join(sorted(invalid))}')
    for skill in event.skills:
        projection.summary.skills[skill] = 0
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
            _grant_skill(projection, skill, 0)
    elif entry.skill:
        _grant_skill(projection, entry.skill, 0)
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
        projection.summary.current_career = None
        projection.summary.current_assignment = None


def _apply_term_event(projection: CharacterProjection, event: TermEventEvent) -> None:
    career = _current_career(projection)
    term_event = career.events.get(event.roll)

    skill_choice_effect = None
    roll_mishap_effect = None
    auto_advance = False
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
    rank_entry = career.ranks.get(new_rank)
    if rank_entry and rank_entry.bonus:
        bonus = rank_entry.bonus
        if bonus.skill:
            _grant_skill(projection, bonus.skill, bonus.level)
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
        _increment_skill(projection, event.skill)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            assignment_name = projection.summary.current_assignment or ''
            projection.pending_inputs.append(_survive_pending(projection, career, assignment_name, event.id))
    elif fulfilled_kind in ('scout_event_11', 'scholar_event_11'):
        if event.skill == 'advancement_dm_4':
            projection.scheduled_effects.append(
                ScheduledEffect(trigger='advancement', source_event_id=event.id, effect={'type': 'dm', 'amount': 4})
            )
        else:
            _grant_skill(projection, event.skill, 1)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id))
    elif fulfilled_kind == 'scholar_event_3':
        if event.skill == 'accept':
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
    elif fulfilled_kind == 'scholar_event_3_science':
        _grant_skill(projection, event.skill, 1)
        # advancement was created when 'accept' was chosen
    elif fulfilled_kind == 'scholar_event_8':
        if event.skill == 'refuse':
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
    elif fulfilled_kind == 'scholar_mishap_3':
        _grant_skill(projection, 'Space Science', 1)
        if event.skill == 'openly':
            projection.summary.connections.append(Connection(kind='enemy', source='Planetary government interference'))
        else:
            soc = projection.summary.characteristics.get('SOC', 0)
            projection.summary.characteristics['SOC'] = max(0, soc - 2)
        # advancement was already created by _apply_mishap (stay_in_career=True)
    elif fulfilled_kind == 'scholar_mishap_5':
        if event.skill == 'give_up':
            projection.pending_inputs = [p for p in projection.pending_inputs if p.kind != 'advancement']
            projection.summary.current_career = None
            projection.summary.current_assignment = None
            projection.summary.age += 4
        # 'start_again': advancement is already there from _apply_mishap, career stays
    else:
        _grant_skill(projection, event.skill, 1)
        if projection.summary.current_career is not None:
            career = _current_career(projection)
            projection.pending_inputs.append(_advancement_pending(projection, career, event.id))


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


def _apply_characteristic_choice(projection: CharacterProjection, event: CharacteristicChoiceEvent) -> None:
    char = event.characteristic
    current = projection.summary.characteristics.get(char, 0)
    projection.summary.characteristics[char] = max(0, current - event.amount)


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
        rank_entry = career.ranks.get(new_rank)
        if rank_entry and rank_entry.bonus:
            bonus = rank_entry.bonus
            if bonus.skill:
                _grant_skill(projection, bonus.skill, bonus.level)
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
    if event.reenlist:
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
        projection.summary.current_career = None
        projection.summary.current_assignment = None


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
        _increment_skill(projection, entry.skill)


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


def _increment_skill(projection: CharacterProjection, skill: str) -> None:
    current = projection.summary.skills.get(skill, -1)
    projection.summary.skills[skill] = current + 1


def _grant_skill(projection: CharacterProjection, skill: str, level: int) -> None:
    current = projection.summary.skills.get(skill, -1)
    if level > current:
        projection.summary.skills[skill] = level


def _apply_simple_effect(
    projection: CharacterProjection, effect: object, source: str = '', source_event_id: int = 0
) -> None:
    effect_type = getattr(effect, 'type', None)
    if effect_type == 'gain_skill':
        skill = getattr(effect, 'skill', None)
        level = getattr(effect, 'level', 1)
        if skill:
            _grant_skill(projection, skill, level)
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
    # note, injury, benefit_dm, life_event, etc. are deferred


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
