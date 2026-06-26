import ceres.character.domain.career as career_pkg
from ceres.character.domain.career.career_data import CareerData


def test_army_loads_lazily():
    army = career_pkg.ARMY
    assert army is not None
    assert army.name == 'Army'


def test_scout_loads_lazily():
    scout = career_pkg.SCOUT
    assert scout is not None
    assert scout.name == 'Scout'


def test_career_constants_are_career_data():
    for name in (
        'AGENT',
        'ARMY',
        'CITIZEN',
        'DRIFTER',
        'ENTERTAINER',
        'MARINES',
        'MERCHANT',
        'NAVY',
        'NOBLE',
        'ROGUE',
        'SCHOLAR',
        'SCOUT',
    ):
        career = getattr(career_pkg, name)
        assert isinstance(career, CareerData), f'{name} is not a CareerData'


def test_load_careers_accessible_via_package():
    load_careers = career_pkg.load_careers
    assert callable(load_careers)


def test_selectable_careers_accessible_via_package():
    selectable = career_pkg.selectable_careers
    assert callable(selectable)


def test_unknown_attribute_raises():
    import pytest

    with pytest.raises(AttributeError):
        _ = career_pkg.TOTALLY_UNKNOWN
