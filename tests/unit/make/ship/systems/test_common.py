"""Unit tests for systems/common.py — _ZeroPowerSystemPart and _ExplicitTonsSystemPart base classes."""

from ceres.make.ship.systems.common import _ExplicitTonsSystemPart, _ZeroPowerSystemPart


class _ZeroPowerConcrete(_ZeroPowerSystemPart):
    system_type: str = 'zero_power_test'
    tons: float = 5.0
    cost: float = 100_000.0


class _ExplicitTonsConcrete(_ExplicitTonsSystemPart):
    system_type: str = 'explicit_tons_test'
    cost: float = 50_000.0


class TestZeroPowerSystemPart:
    def test_power_is_zero(self):
        part = _ZeroPowerConcrete()
        assert part.power == 0.0

    def test_power_not_serialized(self):
        dump = _ZeroPowerConcrete().model_dump()
        assert 'power' not in dump


class TestExplicitTonsSystemPart:
    def test_tons_is_serialized_as_alias(self):
        part = _ExplicitTonsConcrete(tons=12.0)
        assert part.tons == 12.0

    def test_tons_serializes_under_tons_key(self):
        part = _ExplicitTonsConcrete(tons=7.0)
        dump = part.model_dump()
        assert dump['tons'] == 7.0

    def test_stale_tons_not_used_on_revalidate(self):
        part = _ExplicitTonsConcrete.model_validate({'tons': 3.0})
        dumped = part.model_dump()
        revalidated = _ExplicitTonsConcrete.model_validate(dumped)
        assert revalidated.tons == 3.0
