"""Tests for the TermData base class that unifies CareerData and PreCareerData."""

from pydantic import BaseModel

from ceres.character.domain.career.career_data import CareerData, TermData
from ceres.character.domain.career.loader import load_careers
from ceres.character.domain.precareer.loader import load_precareers
from ceres.character.domain.precareer.precareer_data import PreCareerData


class TestTermDataStructure:
    def test_term_data_is_pydantic_base_model(self):
        assert issubclass(TermData, BaseModel)

    def test_career_data_is_subclass_of_term_data(self):
        assert issubclass(CareerData, TermData)

    def test_precareer_data_is_subclass_of_term_data(self):
        assert issubclass(PreCareerData, TermData)

    def test_career_data_declares_events(self):
        assert 'events' in CareerData.__annotations__

    def test_precareer_data_declares_events(self):
        assert 'events' in PreCareerData.__annotations__

    def test_career_data_instances_have_events(self):
        careers = load_careers()
        for career in careers.values():
            assert isinstance(career.events, dict)
            assert len(career.events) > 0

    def test_precareer_data_instances_have_events(self):
        precareers = load_precareers()
        for precareer in precareers.values():
            assert isinstance(precareer.events, dict)
            assert len(precareer.events) > 0

    def test_career_data_is_instance_of_term_data(self):
        careers = load_careers()
        for career in careers.values():
            assert isinstance(career, TermData)

    def test_precareer_data_is_instance_of_term_data(self):
        precareers = load_precareers()
        for precareer in precareers.values():
            assert isinstance(precareer, TermData)


class TestTermDataInterface:
    def test_career_data_name_accessible(self):
        careers = load_careers()
        for career in careers.values():
            assert isinstance(career.name, str)
            assert career.name != ''

    def test_precareer_data_name_accessible(self):
        precareers = load_precareers()
        for precareer in precareers.values():
            assert isinstance(precareer.name, str)
            assert precareer.name != ''

    def test_career_data_source_accessible(self):
        careers = load_careers()
        for career in careers.values():
            assert isinstance(career.source, str)
            assert career.source != ''

    def test_precareer_data_source_accessible(self):
        precareers = load_precareers()
        for precareer in precareers.values():
            assert isinstance(precareer.source, str)
            assert precareer.source != ''


class TestCareerDataSubclassPattern:
    def test_all_loaded_careers_are_specific_subclasses(self):
        """Every career must be an instance of a named CareerData subclass, not CareerData directly."""
        careers = load_careers()
        for name, career in careers.items():
            assert type(career) is not CareerData, (
                f'{name!r} career uses CareerData directly; convert it to a named subclass'
            )

    def test_career_subclass_names_do_not_include_career_data(self):
        """Career class names should be clean career names, not XxxCareerData."""
        careers = load_careers()
        for name, career in careers.items():
            cls_name = type(career).__name__
            assert 'CareerData' not in cls_name, (
                f'{name!r} career class {cls_name!r} still uses the old XxxCareerData naming; rename to {name!r}'
            )

    def test_all_precareer_data_are_subclasses_of_precareer_data(self):
        """Precareer instances should be PreCareerData subclasses (existing pattern)."""
        precareers = load_precareers()
        for precareer in precareers.values():
            assert isinstance(precareer, PreCareerData)
