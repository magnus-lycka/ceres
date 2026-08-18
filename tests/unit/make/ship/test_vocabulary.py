"""The parts vocabulary: contract, base, and mixin host protocols.

See docs/plan-parts-modelling.md. `ShipPart` is the *contract* a ship may rely
on; `ShipPartBase` is only shared implementation. These tests pin the contract
from the consumer's side, and are checked twice over: pytest runs them, and
`ty` verifies the structural conformance in the annotations.
"""

from ceres.make.robot.options import VisualSpectrumSensor
from ceres.make.robot.parts import _RobotPartMixinHost
from ceres.make.ship.base import ShipBase
from ceres.make.ship.bridge import Cockpit
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.hull import Hull, standard_hull
from ceres.make.ship.parts import ShipPart, _ShipPartMixinHost
from ceres.make.ship.ship import Ship


def aggregate(part: ShipPart) -> float:
    """Stands in for Ship's aggregation code, typed against the contract.

    Reaching for every member of the contract is the point: `ty` checks this
    call site structurally, so a part that fails to satisfy `ShipPart` is a
    type error rather than an aggregation crash at runtime.
    """
    part.bind(ShipBase(tl=12, displacement=200))
    part.notes.infos  # noqa: B018 - contract member, exercised deliberately
    assert part.group_key
    return part.tons + part.power + part.cost


def test_a_part_built_on_the_shared_base_satisfies_the_contract():
    assert aggregate(Cockpit()) == 10_001.5


def test_a_part_that_reaches_a_ship_only_through_the_mixin_also_satisfies_it():
    """Computer5 is a gear part plus ShipPartMixin, outside the base's tree."""
    assert aggregate(Computer5()) == 30_000.0


def host(part: _ShipPartMixinHost) -> str:
    """Stands in for ShipPartMixin's own methods, typed against their host.

    Phase 3 strips the mixin's attribute annotations; this protocol is what
    keeps its method bodies type-checkable afterwards. Validated in phase 1
    against a fixture, and pinned here against the real classes.
    """
    part._store_armoured_bulkhead_part(None)
    return f'{part.tl}{part.tons}{part.armoured_bulkhead}{part.notes}{part.armoured_bulkhead_part}'


def test_a_real_ship_part_can_host_the_ship_mixin():
    assert host(Cockpit())


def test_a_real_robot_part_can_host_the_robot_mixin():
    def robot_host(part: _RobotPartMixinHost) -> int:
        return part.tl

    assert robot_host(VisualSpectrumSensor()) == 8


def test_a_mixin_only_part_reaches_ship_aggregation_without_a_cast():
    """The production path, not a stand-in.

    `ComputerSection._all_parts()` used to return `list[ShipPartBase]` and had
    to `cast()` its computers into it, because a computer is a gear part plus
    `ShipPartMixin` and never inherited the base. Typing the path against the
    contract removed both casts. This pins that: the computer must arrive in
    `Ship._base_parts()` and carry its cost into the aggregate.
    """
    vessel = Ship(
        ship_class='Vocabulary Test',
        tl=12,
        displacement=100,
        hull=Hull(configuration=standard_hull),
        computer=ComputerSection(hardware=Computer5()),
    )

    parts = vessel._base_parts()

    assert any(isinstance(part, Computer5) for part in parts)
    assert sum(part.cost for part in parts) >= 30_000.0
