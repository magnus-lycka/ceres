from collections.abc import Callable
from functools import cache
import importlib
from pathlib import Path

import yaml

from ceres.character.careers.career_data import (
    AdvancementDmEffect,
    AnyEffect,
    AssignmentData,
    AutoAdvanceEffect,
    BenefitDmEffect,
    CareerData,
    CareerDispatchEffect,
    CareerEventEntry,
    CharCheck,
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
    MishapEntry,
    MusterOutData,
    MusterOutRow,
    ParoleThresholdChangeEffect,
    RankBonus,
    RankEntry,
    RollMishapEffect,
    SkillChoiceEffect,
    SkillTable,
    SkillTableEntry,
)

_CAREERS_DIR = Path(__file__).parent

# Populated when load_careers() runs; maps career_name → effect_type → handler
_effect_handlers: dict[str, dict[str, Callable]] = {}
# Maps career_name → context → handler
_skill_roll_handlers: dict[str, dict[str, Callable]] = {}
# Maps career_name → context → handler for CareerChoiceEvent
_choice_handlers: dict[str, dict[str, Callable]] = {}


def get_effect_handler(career_name: str, effect_type: str) -> Callable | None:
    return _effect_handlers.get(career_name, {}).get(effect_type)


def get_skill_roll_handler(career_name: str, context: str) -> Callable | None:
    return _skill_roll_handlers.get(career_name, {}).get(context)


def get_choice_handler(career_name: str, context: str) -> Callable | None:
    return _choice_handlers.get(career_name, {}).get(context)


def _parse_effect(raw: dict) -> AnyEffect:
    match raw.get('type', ''):
        case 'gain_skill':
            return GainSkillEffect(**raw)
        case 'decrease_characteristic':
            return DecreaseCharacteristicEffect(**raw)
        case 'decrease_characteristic_choice':
            return DecreaseCharacteristicChoiceEffect(**raw)
        case 'gain_contact':
            return GainContactEffect()
        case 'gain_ally':
            return GainAllyEffect()
        case 'gain_rival':
            return GainRivalEffect()
        case 'gain_enemy':
            return GainEnemyEffect()
        case 'gain_connections_rolled':
            return GainConnectionsRolledEffect(**raw)
        case 'skill_choice':
            return SkillChoiceEffect(**raw)
        case 'injury':
            return InjuryEffect(**raw)
        case 'roll_mishap':
            return RollMishapEffect(**raw)
        case 'auto_advance':
            return AutoAdvanceEffect()
        case 'life_event':
            return LifeEventEffect()
        case 'advancement_dm':
            return AdvancementDmEffect(**raw)
        case 'benefit_dm':
            return BenefitDmEffect(**raw)
        case 'parole_threshold_change':
            return ParoleThresholdChangeEffect(**raw)
        case type_str:
            return CareerDispatchEffect(type=type_str)


def _parse_skill_table(raw: dict) -> SkillTable:
    min_edu = raw.pop('min_edu', None)
    entries = {}
    for roll, entry in raw.items():
        if isinstance(entry, str):
            entries[int(roll)] = SkillTableEntry(skill=entry)
        elif isinstance(entry, dict):
            entries[int(roll)] = SkillTableEntry(**entry)
    return SkillTable(min_edu=min_edu, entries=entries)


def _parse_rank_entry(rank: int, raw: dict | None) -> RankEntry:
    if raw is None:
        return RankEntry(rank=rank)
    bonus_raw = raw.get('bonus')
    bonus = RankBonus(**bonus_raw) if bonus_raw else None
    return RankEntry(rank=rank, title=raw.get('title'), bonus=bonus)


def _parse_career_event(raw: dict) -> CareerEventEntry:
    effects = [_parse_effect(e) for e in raw.get('effects', [])]
    return CareerEventEntry(text=raw['text'], effects=effects)


def _parse_mishap(raw: dict) -> MishapEntry:
    effects = [_parse_effect(e) for e in raw.get('effects', [])]
    return MishapEntry(
        text=raw['text'],
        stay_in_career=raw.get('stay_in_career', False),
        defer_ejection=raw.get('defer_ejection', False),
        effects=effects,
    )


def _parse_muster_out(raw: dict) -> MusterOutData:
    from ceres.character.benefits import parse_benefit

    rows = {
        int(roll): MusterOutRow(
            cash=row['cash'],
            benefit=parse_benefit(row['benefit']),
            count=row.get('count', 1),
        )
        for roll, row in raw.items()
    }
    return MusterOutData(rows=rows)


def _parse_draft_assignments(data: dict, assignments: list[AssignmentData]) -> list[str]:
    draft = data.get('draft')
    if not draft:
        return []
    if draft is True:
        return [assignment.name for assignment in assignments]
    if isinstance(draft, list):
        return [str(assignment) for assignment in draft]
    if isinstance(draft, dict):
        if 'assignments' in draft:
            return list(draft['assignments'])
        if 'assignment' in draft:
            return [draft['assignment']]
    raise ValueError(f'Invalid draft data for {data["name"]!r}: {draft!r}')


def _load_career_file(path: Path) -> CareerData:
    data = yaml.safe_load(path.read_text())
    career_class = CareerData
    py_path = path.with_suffix('.py')
    if py_path.exists():
        mod = importlib.import_module(f'ceres.character.careers.{path.stem}')
        career_class = getattr(mod, 'CAREER_DATA_CLASS', CareerData)

    assignments = [
        AssignmentData(
            name=a['name'],
            description=a.get('description'),
            survival=CharCheck(**a['survival']),
            advancement=CharCheck(**a['advancement']),
        )
        for a in data['assignments']
    ]

    skill_tables: dict[str, SkillTable] = {}
    for table_name, table_raw in data['skill_tables'].items():
        skill_tables[table_name] = _parse_skill_table(dict(table_raw))

    ranks = {int(k): _parse_rank_entry(int(k), v) for k, v in data.get('ranks', {}).items()}

    ranks_by_assignment: dict[str, dict[int, RankEntry]] = {}
    for assignment_name, assignment_ranks_raw in data.get('ranks_by_assignment', {}).items():
        ranks_by_assignment[assignment_name] = {
            int(k): _parse_rank_entry(int(k), v) for k, v in assignment_ranks_raw.items()
        }

    events = {int(k): _parse_career_event(v) for k, v in data.get('events', {}).items()}
    mishaps = {int(k): _parse_mishap(v) for k, v in data.get('mishaps', {}).items()}

    muster_out_raw = data.get('muster_out')
    muster_out = _parse_muster_out(muster_out_raw)

    return career_class(
        name=data['name'],
        description=data.get('description'),
        source=data['source'],
        qualification=CharCheck(**data['qualification']),
        assignments=assignments,
        skill_tables=skill_tables,
        ranks=ranks,
        ranks_by_assignment=ranks_by_assignment,
        commission=CharCheck(**data['commission']) if data.get('commission') else None,
        officer_ranks={int(k): _parse_rank_entry(int(k), v) for k, v in data.get('officer_ranks', {}).items()},
        events=events,
        mishaps=mishaps,
        muster_out=muster_out,
        allows_assignment_change=data['allows_assignment_change'],
        selectable=data.get('selectable', True),
        draft_assignments=_parse_draft_assignments(data, assignments),
    )


@cache
def load_careers() -> dict[str, CareerData]:
    careers: dict[str, CareerData] = {}
    for path in sorted(_CAREERS_DIR.glob('*.yaml')):
        career = _load_career_file(path)
        careers[career.name] = career
        py_path = path.with_suffix('.py')
        if py_path.exists():
            mod = importlib.import_module(f'ceres.character.careers.{path.stem}')
            _effect_handlers[career.name] = getattr(mod, 'EFFECT_HANDLERS', {})
            _skill_roll_handlers[career.name] = getattr(mod, 'SKILL_ROLL_HANDLERS', {})
            _choice_handlers[career.name] = getattr(mod, 'CHOICE_HANDLERS', {})
    return careers


def selectable_careers(projection=None) -> dict[str, CareerData]:
    return {name: career for name, career in load_careers().items() if career.is_selectable(projection)}
