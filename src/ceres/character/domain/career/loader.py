from collections.abc import Iterable
from functools import cache
import importlib
from pathlib import Path

from ceres.character.domain.career.career_data import CareerData


@cache
def load_careers() -> tuple[CareerData, ...]:
    careers_dir = Path(__file__).parent
    non_career_stem = {'__init__', 'career_data', 'common', 'common_pending', 'loader'}
    for path in sorted(careers_dir.glob('*.py')):
        if path.stem in non_career_stem:
            continue
        importlib.import_module(f'ceres.character.domain.career.{path.stem}')
    return tuple(career_cls() for career_cls in CareerData._registry.values())


def selectable_careers(projection=None) -> tuple[CareerData, ...]:
    return tuple(career for career in load_careers() if career.is_selectable(projection))


def career_from_user_input_name(name: str, careers: Iterable[CareerData] | None = None) -> CareerData | None:
    """Resolve a career name received from a UI/form boundary."""
    return next((career for career in careers or load_careers() if career.name == name), None)


def career_of_type[CareerT: CareerData](career_type: type[CareerT]) -> CareerT:
    """Return the loaded career instance for a concrete CareerData subclass."""
    career = next((career for career in load_careers() if isinstance(career, career_type)), None)
    if career is None:
        raise LookupError(f'Career type is not loaded: {career_type!r}')
    return career
