"""Marking classes that implement ShipPartMixin without being installable parts.

See docs/plan-parts-modelling.md. Some classes implement the mixin as bases for
real parts rather than as parts themselves: the shared part base, and the
intermediate helpers whose descendants supply the values. The architecture
conformance test must skip those, and it must know which they are from an
explicit statement rather than by guessing at the inheritance shape.
"""

import pytest

from ceres.make.ship.crafts import _ZeroPowerCraftPart
from ceres.make.ship.habitation import _ExplicitCostHabitationPart, _ExplicitTonsHabitationPart
from ceres.make.ship.installable import is_installable, not_installable
from ceres.make.ship.parts import CustomisableShipPart, ShipPartBase
from ceres.make.ship.power import _SolarPowerSource
from ceres.make.ship.storage import _ExplicitTonsStoragePart, _LoadingBelt, _ZeroPowerStoragePart
from ceres.make.ship.systems.common import _ExplicitTonsSystemPart, _ZeroPowerSystemPart
from ceres.make.ship.systems.reentry import _ReEntrySystem

# Classes that implement ShipPartMixin but are bases for parts, not parts. Each
# either supplies no values of its own (its descendants do) or is the shared
# base itself. The conformance test added in phase 5 skips exactly these.
BASES = [
    ShipPartBase,
    CustomisableShipPart,
    _ZeroPowerSystemPart,
    _ZeroPowerStoragePart,
    _ZeroPowerCraftPart,
    _ExplicitTonsSystemPart,
    _ExplicitTonsStoragePart,
    _ExplicitTonsHabitationPart,
    _ExplicitCostHabitationPart,
    _LoadingBelt,
    _ReEntrySystem,
    _SolarPowerSource,
]


def descendants(cls: type) -> set[type]:
    found: set[type] = set()
    for sub in cls.__subclasses__():
        found.add(sub)
        found |= descendants(sub)
    return found


def test_a_marked_class_is_not_installable():
    @not_installable
    class HelperBase:
        """Stands in for _ZeroPowerSystemPart and friends."""

    assert not is_installable(HelperBase)


def test_marking_does_not_reach_subclasses():
    """The whole point: descendants of a marked helper *are* installable.

    _ZeroPowerSystemPart has 25 descendants and they are all real parts. A
    marker that were inherited would excuse exactly the classes the conformance
    test exists to check.
    """

    @not_installable
    class HelperBase:
        pass

    class RealPart(HelperBase):
        pass

    assert is_installable(RealPart)


@pytest.mark.parametrize('cls', BASES, ids=lambda c: c.__name__)
def test_a_base_for_parts_is_marked_not_installable(cls):
    assert not is_installable(cls)


@pytest.mark.parametrize('cls', [c for c in BASES if c is not ShipPartBase], ids=lambda c: c.__name__)
def test_the_real_parts_built_on_those_bases_remain_installable(cls):
    """The marker must not reach the parts themselves.

    Bases nest — `_ReEntrySystem` extends `_ZeroPowerSystemPart` — so a
    descendant that is itself a declared base is excluded rather than treated
    as a failure.
    """
    parts = descendants(cls) - set(BASES)

    assert parts, f'{cls.__name__} has no parts built on it; it may not be a base at all'
    assert all(is_installable(part) for part in parts)
