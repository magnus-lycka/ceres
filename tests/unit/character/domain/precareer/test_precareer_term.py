from ceres.character.domain.precareer.precareer_data import PreCareerTerm
from ceres.character.domain.precareer.precareer_term import (
    _PRECAREER_TERM_REGISTRY,
    _all_precareer_term_classes,
)
from ceres.character.domain.precareer.university import UniversityTerm


def test_registry_contains_every_precareer_term_class() -> None:
    assert set(_PRECAREER_TERM_REGISTRY.values()) == set(_all_precareer_term_classes)


def test_registry_keys_are_term_discriminator_defaults() -> None:
    for term_cls in _all_precareer_term_classes:
        assert _PRECAREER_TERM_REGISTRY[term_cls.model_fields['kind'].default] is term_cls


def test_registry_values_are_precareer_term_subclasses() -> None:
    assert all(issubclass(term_cls, PreCareerTerm) for term_cls in _PRECAREER_TERM_REGISTRY.values())


def test_known_term_is_registered_by_kind() -> None:
    assert _PRECAREER_TERM_REGISTRY[UniversityTerm.model_fields['kind'].default] is UniversityTerm
