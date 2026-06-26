import pytest

from ceres.character.domain.career.career_data import CareerData
from ceres.character.domain.career.loader import (
    career_from_user_input_name,
    career_of_type,
    load_careers,
    selectable_careers,
)


def test_load_careers_returns_tuple_of_career_data():
    careers = load_careers()
    assert isinstance(careers, tuple)
    assert all(isinstance(c, CareerData) for c in careers)


def test_load_careers_includes_standard_careers():
    names = {c.name for c in load_careers()}
    assert 'Scout' in names
    assert 'Navy' in names
    assert 'Army' in names
    assert 'Merchant' in names


def test_load_careers_is_cached():
    assert load_careers() is load_careers()


def test_selectable_careers_returns_subset_of_all_careers():
    all_names = {c.name for c in load_careers()}
    selectable_names = {c.name for c in selectable_careers()}
    assert selectable_names.issubset(all_names)


def test_selectable_careers_excludes_prisoner():
    names = {c.name for c in selectable_careers()}
    assert 'Prisoner' not in names


def test_career_from_user_input_name_finds_scout():
    result = career_from_user_input_name('Scout')
    assert result is not None
    assert result.name == 'Scout'


def test_career_from_user_input_name_returns_none_for_unknown():
    assert career_from_user_input_name('Barbarian') is None


def test_career_from_user_input_name_is_case_sensitive():
    assert career_from_user_input_name('scout') is None


def test_career_of_type_returns_correct_instance():
    from ceres.character.domain.career.scout import Scout

    result = career_of_type(Scout)
    assert isinstance(result, Scout)


def test_career_of_type_raises_for_unloaded_type():
    class FakeCareer(CareerData):
        pass

    with pytest.raises(LookupError):
        career_of_type(FakeCareer)
