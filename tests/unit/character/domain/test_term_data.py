"""Tests for the TermData base class that unifies CareerData and PreCareerData."""

from pydantic import BaseModel

from ceres.character.domain.career.career_data import CareerData
from ceres.character.domain.career.loader import load_careers
from ceres.character.domain.precareer.loader import load_precareers
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.term_data import TermData


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
        for career in load_careers():
            assert isinstance(career.events, dict)
            assert len(career.events) > 0

    def test_precareer_data_instances_have_events(self):
        for precareer in load_precareers():
            assert isinstance(precareer.events, dict)
            assert len(precareer.events) > 0

    def test_career_data_is_instance_of_term_data(self):
        for career in load_careers():
            assert isinstance(career, TermData)

    def test_precareer_data_is_instance_of_term_data(self):
        for precareer in load_precareers():
            assert isinstance(precareer, TermData)


class TestTermDataInterface:
    def test_career_data_name_accessible(self):
        for career in load_careers():
            assert isinstance(career.name, str)
            assert career.name != ''

    def test_precareer_data_name_accessible(self):
        for precareer in load_precareers():
            assert isinstance(precareer.name, str)
            assert precareer.name != ''

    def test_career_data_source_accessible(self):
        for career in load_careers():
            assert isinstance(career.source, str)
            assert career.source != ''

    def test_precareer_data_source_accessible(self):
        for precareer in load_precareers():
            assert isinstance(precareer.source, str)
            assert precareer.source != ''


class TestTermNotes:
    def _term(self, **kwargs):
        from ceres.character.domain.career.army import ARMY
        from ceres.character.domain.career.career_data import CareerTerm

        support = ARMY.assignment('Support')
        assert support is not None
        return CareerTerm(career=ARMY, assignment=support, **kwargs)

    def test_empty_notes_when_no_fields(self):
        term = self._term()
        assert len(term.notes) == 0

    def test_event_becomes_content_note(self):
        term = self._term(event='You are promoted.')
        notes = term.notes
        assert len(notes.contents) == 1
        assert notes.contents[0] == 'You are promoted.'

    def test_mishap_becomes_warning_note(self):
        term = self._term(mishap='Injured in battle.')
        notes = term.notes
        assert len(notes.warnings) == 1
        assert notes.warnings[0] == 'Injured in battle.'

    def test_prison_becomes_error_note(self):
        term = self._term(prison='Crime: Theft')
        notes = term.notes
        assert len(notes.errors) == 1
        assert notes.errors[0] == 'Crime: Theft'

    def test_all_three_fields_together(self):
        term = self._term(event='Survived.', mishap='Wounded.', prison='Caught.')
        notes = term.notes
        assert len(notes.contents) == 1
        assert len(notes.warnings) == 1
        assert len(notes.errors) == 1


class TestCareerDataSubclassPattern:
    def test_all_loaded_careers_are_specific_subclasses(self):
        """Every career must be an instance of a named CareerData subclass, not CareerData directly."""
        for career in load_careers():
            assert type(career) is not CareerData, (
                f'{career.name!r} career uses CareerData directly; convert it to a named subclass'
            )

    def test_career_subclass_names_do_not_include_career_data(self):
        """Career class names should be clean career names, not XxxCareerData."""
        for career in load_careers():
            cls_name = type(career).__name__
            assert 'CareerData' not in cls_name, (
                f'{career.name!r} career class {cls_name!r} still uses the old XxxCareerData naming; rename it'
            )

    def test_all_precareer_data_are_subclasses_of_precareer_data(self):
        """Precareer instances should be PreCareerData subclasses (existing pattern)."""
        for precareer in load_precareers():
            assert isinstance(precareer, PreCareerData)

    def test_all_loaded_precareers_are_specific_subclasses(self):
        """Every named pre-career should have its own concrete PreCareerData subclass."""
        precareers = load_precareers()
        concrete_types = {type(precareer) for precareer in precareers}

        assert len(concrete_types) == len(precareers)
        for precareer in precareers:
            assert type(precareer) is not PreCareerData, (
                f'{precareer.name!r} pre-career uses PreCareerData directly; convert it to a named subclass'
            )

    def test_all_loaded_precareers_have_class_owned_rule_data(self):
        """Pre-career rule data should live on concrete classes, matching CareerData."""
        for precareer in load_precareers():
            assert not precareer.model_fields_set, (
                f'{precareer.name!r} pre-career still receives rule data through constructor fields; '
                'move the rule data onto its concrete class'
            )
