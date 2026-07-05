from ceres.character.domain.career.agent import AgentTerm
from ceres.character.domain.career.army import ArmyTerm
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.career.career_term import _CAREER_TERM_REGISTRY, _all_career_term_classes


def test_registry_contains_every_career_term_class() -> None:
    assert set(_CAREER_TERM_REGISTRY.values()) == set(_all_career_term_classes)


def test_registry_keys_are_term_discriminator_defaults() -> None:
    for term_cls in _all_career_term_classes:
        assert _CAREER_TERM_REGISTRY[term_cls.model_fields['kind'].default] is term_cls


def test_registry_values_are_career_term_subclasses() -> None:
    assert all(issubclass(term_cls, CareerTerm) for term_cls in _CAREER_TERM_REGISTRY.values())


def test_known_terms_are_registered_by_kind() -> None:
    assert _CAREER_TERM_REGISTRY[AgentTerm.model_fields['kind'].default] is AgentTerm
    assert _CAREER_TERM_REGISTRY[ArmyTerm.model_fields['kind'].default] is ArmyTerm
