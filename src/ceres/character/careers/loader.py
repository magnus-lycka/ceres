from functools import cache
import importlib
from pathlib import Path

from ceres.character.careers.career_data import CareerData

_CAREERS_DIR = Path(__file__).parent

_NON_CAREER_STEMS = {'__init__', 'career_data', 'common', 'loader'}


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
    return careers


def selectable_careers(projection=None) -> dict[str, CareerData]:
    return {name: career for name, career in load_careers().items() if career.is_selectable(projection)}
