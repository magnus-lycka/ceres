"""The serialisation invariant that the parts migration must not break.

See docs/plan-parts-modelling.md:

    Derived values must never serialise. Only supplied design inputs appear in
    model_dump(), under their public name.

`test_bridge.py` already asserts this for `Cockpit`. These tests widen it to a
sample spanning several modules, including `Computer5` — which reaches a ship
through `ShipPartMixin` rather than through the shared part base — and
`FuelProcessor`, which supplies its tonnage through the rename-and-alias
mechanism. They are the safety net for every later phase of the migration, so
they assert current, correct behaviour rather than driving new behaviour.
"""

import pytest

from ceres.make.ship.armour import Armour
from ceres.make.ship.base import ShipBase
from ceres.make.ship.bridge import Cockpit
from ceres.make.ship.computer import Computer5
from ceres.make.ship.habitation import Stateroom
from ceres.make.ship.screens import BlackGlobeCapacitorBank
from ceres.make.ship.sensors import DeepPenetrationScanners, SensorPackage
from ceres.make.ship.storage import FuelProcessor

# Parts whose tonnage is computed from the ship they are bound to.
DERIVED_TONNAGE = {
    'Cockpit': Cockpit,
    'Armour': lambda: Armour(description='Crystaliron', protection=4),
    'Stateroom': Stateroom,
    'SensorPackage': SensorPackage,
    'Computer5': Computer5,
}

# Parts whose tonnage is a design input the referee supplies.
SUPPLIED_TONNAGE = {
    'DeepPenetrationScanners': lambda: DeepPenetrationScanners(tons=2.0),
    'FuelProcessor': FuelProcessor,
    'BlackGlobeCapacitorBank': lambda: BlackGlobeCapacitorBank(tons=5.0),
}

# Power is classified independently of tonnage: BlackGlobeCapacitorBank supplies
# both, while DeepPenetrationScanners supplies tonnage but derives its power.
SUPPLIED_POWER = {
    'BlackGlobeCapacitorBank': lambda: BlackGlobeCapacitorBank(tons=5.0),
}
DERIVED_POWER = {
    name: factory for name, factory in {**DERIVED_TONNAGE, **SUPPLIED_TONNAGE}.items() if name not in SUPPLIED_POWER
}


def bound(factory):
    part = factory()
    part.bind(ShipBase(tl=12, displacement=200))
    return part


@pytest.mark.parametrize('factory', DERIVED_TONNAGE.values(), ids=DERIVED_TONNAGE)
def test_derived_tonnage_is_never_serialised(factory):
    part = bound(factory)

    assert 'tons' not in part.model_dump()


@pytest.mark.parametrize('factory', DERIVED_TONNAGE.values(), ids=DERIVED_TONNAGE)
def test_a_derived_tonnage_offered_as_input_is_discarded(factory):
    """Supplying a value must not override, nor quietly persist, a derived one."""
    part = bound(factory)
    expected = part.tons

    supplied = type(part).model_validate({**part.model_dump(), 'tons': 999})
    supplied.bind(ShipBase(tl=12, displacement=200))

    assert supplied.tons == expected
    assert 'tons' not in supplied.model_dump()


@pytest.mark.parametrize('factory', SUPPLIED_TONNAGE.values(), ids=SUPPLIED_TONNAGE)
def test_supplied_tonnage_is_serialised_under_its_public_name(factory):
    part = bound(factory)

    dumped = part.model_dump()

    assert 'tons' in dumped
    assert dumped['tons'] == part.tons


@pytest.mark.parametrize('factory', DERIVED_POWER.values(), ids=DERIVED_POWER)
def test_derived_power_is_never_serialised(factory):
    part = bound(factory)

    assert 'power' not in part.model_dump()


@pytest.mark.parametrize('factory', SUPPLIED_POWER.values(), ids=SUPPLIED_POWER)
def test_supplied_power_is_serialised_under_its_public_name(factory):
    part = bound(factory)

    dumped = part.model_dump()

    assert 'power' in dumped
    assert dumped['power'] == part.power
