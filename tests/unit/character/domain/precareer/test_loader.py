"""Unit tests for precareer loader.py."""

import pytest

from ceres.character.domain.precareer.loader import (
    load_precareers,
    precareer_from_user_input_name,
    precareer_of_type,
)
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.precareer.university import UniversityPreCareer


class TestLoadPrecareers:
    def test_returns_non_empty_tuple(self):
        pcs = load_precareers()
        assert len(pcs) > 0

    def test_all_are_precareer_data(self):
        for pc in load_precareers():
            assert isinstance(pc, PreCareerData)

    def test_university_present(self):
        names = [pc.name for pc in load_precareers()]
        assert 'University' in names

    def test_all_have_names(self):
        for pc in load_precareers():
            assert pc.name


class TestPrecareerFromUserInputName:
    def test_finds_university_by_name(self):
        pc = precareer_from_user_input_name('University')
        assert pc is not None
        assert pc.name == 'University'

    def test_returns_none_for_unknown_name(self):
        assert precareer_from_user_input_name('Unknown Pre-Career') is None

    def test_case_sensitive(self):
        assert precareer_from_user_input_name('university') is None


class TestPrecareerOfType:
    def test_returns_university_by_type(self):
        pc = precareer_of_type(UniversityPreCareer)
        assert isinstance(pc, UniversityPreCareer)

    def test_raises_for_unknown_type(self):
        class _FakePreCareer(PreCareerData):
            name = 'Fake'
            source = 'Test'

        with pytest.raises(LookupError):
            precareer_of_type(_FakePreCareer)
