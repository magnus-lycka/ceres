"""Behaviour of the shared system-part bases.

`_ExplicitTonsSystemPart` no longer exists: with the base declaring nothing,
"tonnage is a supplied design input" is expressed as an ordinary field. These
tests keep asserting that behaviour, now against the plain form.
"""

from ceres.make.ship.parts import ShipPartBase, UnpoweredShipPart


class _ZeroPowerConcrete(UnpoweredShipPart):
    system_type: str = 'zero_power_test'
    tons: float = 5.0
    cost: float = 100_000.0


class _SuppliedTonsConcrete(ShipPartBase):
    system_type: str = 'supplied_tons_test'
    tons: float = 0.0
    cost: float = 50_000.0

    @property
    def power(self) -> float:
        return 0.0


class TestUnpoweredShipPart:
    def test_power_is_zero(self):
        assert _ZeroPowerConcrete().power == 0.0

    def test_derived_power_is_not_serialised(self):
        assert 'power' not in _ZeroPowerConcrete().model_dump()


class TestSuppliedTonnage:
    def test_supplied_value_is_kept(self):
        assert _SuppliedTonsConcrete(tons=12.0).tons == 12.0

    def test_supplied_value_serialises_under_its_own_name(self):
        assert _SuppliedTonsConcrete(tons=7.0).model_dump()['tons'] == 7.0

    def test_defaults_to_zero(self):
        assert _SuppliedTonsConcrete().tons == 0.0

    def test_survives_a_round_trip(self):
        part = _SuppliedTonsConcrete.model_validate({'tons': 3.0})

        revalidated = _SuppliedTonsConcrete.model_validate(part.model_dump())

        assert revalidated.tons == 3.0
