from collections.abc import Callable
from functools import cache
import importlib
from pathlib import Path

import yaml

from ceres.character.careers.career_data import (
    AssignmentData,
    CareerData,
    CareerEventEntry,
    CharCheck,
    EventEffect,
    MishapEntry,
    RankBonus,
    RankEntry,
    SkillTable,
    SkillTableEntry,
)

_CAREERS_DIR = Path(__file__).parent

# Populated when load_careers() runs; maps career_name → effect_type → handler
_effect_handlers: dict[str, dict[str, Callable]] = {}
# Maps career_name → context → handler
_skill_roll_handlers: dict[str, dict[str, Callable]] = {}


def get_effect_handler(career_name: str, effect_type: str) -> Callable | None:
    return _effect_handlers.get(career_name, {}).get(effect_type)


def get_skill_roll_handler(career_name: str, context: str) -> Callable | None:
    return _skill_roll_handlers.get(career_name, {}).get(context)


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
    effects = [EventEffect(**e) for e in raw.get('effects', [])]
    return CareerEventEntry(text=raw['text'], effects=effects)


def _parse_mishap(raw: dict) -> MishapEntry:
    effects = [EventEffect(**e) for e in raw.get('effects', [])]
    return MishapEntry(text=raw['text'], effects=effects)


def _load_career_file(path: Path) -> CareerData:
    data = yaml.safe_load(path.read_text())

    assignments = [
        AssignmentData(
            name=a['name'],
            survival=CharCheck(**a['survival']),
            advancement=CharCheck(**a['advancement']),
        )
        for a in data['assignments']
    ]

    skill_tables: dict[str, SkillTable] = {}
    for table_name, table_raw in data['skill_tables'].items():
        skill_tables[table_name] = _parse_skill_table(dict(table_raw))

    ranks = {int(k): _parse_rank_entry(int(k), v) for k, v in data.get('ranks', {}).items()}

    events = {int(k): _parse_career_event(v) for k, v in data.get('events', {}).items()}
    mishaps = {int(k): _parse_mishap(v) for k, v in data.get('mishaps', {}).items()}

    return CareerData(
        name=data['name'],
        source=data['source'],
        qualification=CharCheck(**data['qualification']),
        assignments=assignments,
        skill_tables=skill_tables,
        ranks=ranks,
        events=events,
        mishaps=mishaps,
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
    return careers
