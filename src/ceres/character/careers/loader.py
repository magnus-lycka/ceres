from collections.abc import Callable
from functools import cache
import importlib
from pathlib import Path

from ceres.character.careers.career_data import CareerData

_CAREERS_DIR = Path(__file__).parent

_NON_CAREER_STEMS = {'__init__', 'career_data', 'common', 'loader'}

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


@cache
def load_careers() -> dict[str, CareerData]:
    careers: dict[str, CareerData] = {}
    for path in sorted(_CAREERS_DIR.glob('*.py')):
        if path.stem in _NON_CAREER_STEMS:
            continue
        mod = importlib.import_module(f'ceres.character.careers.{path.stem}')
        if not hasattr(mod, 'CAREER_DATA'):
            continue
        career: CareerData = mod.CAREER_DATA
        careers[career.name] = career
        _effect_handlers[career.name] = getattr(mod, 'EFFECT_HANDLERS', {})
        _skill_roll_handlers[career.name] = getattr(mod, 'SKILL_ROLL_HANDLERS', {})
        _choice_handlers[career.name] = getattr(mod, 'CHOICE_HANDLERS', {})
    return careers


def selectable_careers(projection=None) -> dict[str, CareerData]:
    return {name: career for name, career in load_careers().items() if career.is_selectable(projection)}
