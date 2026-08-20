"""Architecture guard: every installable ship part declares its own values.

See docs/plan-parts-modelling.md. `ShipPartBase` deliberately declares neither
`tons` nor `power`: the contract is `ShipPart`, and the base is only shared
implementation. Nothing in the class hierarchy therefore guarantees that a part
can answer them — *this test does*.

A part must provide each value in exactly one of two forms, and which one it
picks is a statement about the domain:

- a **Pydantic field** — the value is a supplied design input, and persists;
- a **property** — the value is derived, and must never persist.

Without this, an incomplete part surfaces as an `AttributeError` during
aggregation, far from the class that caused it.
"""

import importlib
import inspect
import pkgutil

import pytest

import ceres.make.ship
from ceres.make.ship.installable import is_installable
from ceres.make.ship.parts import ShipPartMixin

VALUES = ('tons', 'power')


def installable_parts() -> list[type]:
    """Every non-abstract, installable implementation of `ShipPartMixin`.

    Imports the whole package first: `__subclasses__()` only sees classes whose
    modules have been imported, so discovery that relies on incidental imports
    could be evaded simply by adding a file.
    """
    for module in pkgutil.walk_packages(ceres.make.ship.__path__, f'{ceres.make.ship.__name__}.'):
        importlib.import_module(module.name)

    def descendants(cls: type) -> set[type]:
        found: set[type] = set()
        for sub in cls.__subclasses__():
            found.add(sub)
            found |= descendants(sub)
        return found

    return sorted(
        (
            c
            for c in descendants(ShipPartMixin)
            if not inspect.isabstract(c)
            and is_installable(c)
            # Only the shipped package. Test modules define their own doubles,
            # and whether those are loaded depends on test ordering — a guard
            # that policed them would be order-dependent.
            and c.__module__.startswith('ceres.')
        ),
        key=lambda c: f'{c.__module__}.{c.__name__}',
    )


def provider(cls: type, name: str) -> str:
    """How this class supplies `name`: as a field, a property, or not at all."""
    if name in getattr(cls, 'model_fields', {}):
        return 'field'
    for klass in cls.__mro__:
        if isinstance(klass.__dict__.get(name), property):
            return 'property'
    return 'missing'


class TestDiscovery:
    """The guard is only worth as much as the population it walks."""

    def test_finds_parts_from_many_modules(self):
        modules = {cls.__module__ for cls in installable_parts()}

        assert len(modules) > 10

    def test_includes_parts_that_never_inherit_the_shared_base(self):
        """Computers reach a ship through the mixin alone."""
        names = {cls.__name__ for cls in installable_parts()}

        assert 'Computer5' in names

    def test_excludes_the_bases_that_parts_are_built_from(self):
        names = {cls.__name__ for cls in installable_parts()}

        assert 'ShipPartBase' not in names
        assert 'CustomisableShipPart' not in names

    def test_excludes_classes_defined_in_tests(self):
        """Otherwise the guard would depend on which test modules were imported."""
        assert all(cls.__module__.startswith('ceres.') for cls in installable_parts())

    def test_population_has_not_collapsed(self):
        """A floor, so a discovery bug cannot quietly empty the guard."""
        assert len(installable_parts()) > 250


@pytest.mark.parametrize('value', VALUES)
def test_every_installable_part_declares_its_values(value):
    offenders = {cls.__name__: provider(cls, value) for cls in installable_parts()}
    missing = sorted(name for name, how in offenders.items() if how == 'missing')

    assert not missing, (
        f'{len(missing)} part(s) provide no {value}: {missing[:10]}. '
        f'Declare it as a Pydantic field if it is a supplied design input, '
        f'or as a property if it is derived. If the class is a base rather than '
        f'a part, mark it @not_installable.'
    )
