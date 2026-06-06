from functools import cache
import importlib
from pathlib import Path

from ceres.character.domain.career.career_data import CareerData

_CAREERS_DIR = Path(__file__).parent

_NON_CAREER_STEMS = {'__init__', 'career_data', 'common', 'common_pending', 'loader'}


@cache
def load_careers() -> dict[str, CareerData]:
    for path in sorted(_CAREERS_DIR.glob('*.py')):
        if path.stem in _NON_CAREER_STEMS:
            continue
        importlib.import_module(f'ceres.character.domain.career.{path.stem}')
    return {career_cls().name: career_cls() for career_cls in CareerData._registry.values()}


def selectable_careers(projection=None) -> dict[str, CareerData]:
    return {name: career for name, career in load_careers().items() if career.is_selectable(projection)}
