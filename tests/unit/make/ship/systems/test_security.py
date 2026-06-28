"""Unit tests for systems/security.py — Armoury, PsionicShielding, Vault, BoobyTrap*."""

import pytest

from ceres.make.ship.systems.security import (
    Armoury,
    BoobyTrapTL6,
    BoobyTrapTL8,
    BoobyTrapTL10,
    BoobyTrapTL12,
    Vault,
)


class TestArmoury:
    def test_computed_not_serialized(self):
        part = Armoury.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        assert part.tons == 1.0
        assert part.cost == 250_000.0
        assert part.power == 0.0
        dump = part.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestVault:
    def test_content_armour_scales_with_tons(self):
        assert Vault(tons=8).content_armour == 8

    def test_content_armour_capped_at_10(self):
        assert Vault(tons=40).content_armour == 10

    def test_content_hull_points_small(self):
        assert Vault(tons=8).content_hull_points == 1

    def test_content_hull_points_large(self):
        assert Vault(tons=40).content_hull_points == 8

    def test_cost_is_500k_per_ton(self):
        assert Vault(tons=8).cost == pytest.approx(4_000_000.0)

    def test_size_below_minimum_is_an_error(self):
        assert 'Vault size must be between 4 and 40 tons' in Vault(tons=3.99).notes.errors

    def test_size_above_maximum_is_an_error(self):
        assert 'Vault size must be between 4 and 40 tons' in Vault(tons=40.01).notes.errors

    def test_valid_size_has_no_errors(self):
        assert not Vault(tons=20).notes.errors

    def test_computed_cost_and_power_not_serialized(self):
        vault = Vault.model_validate({'tons': 8, 'cost': 999, 'power': 999})
        assert vault.cost == pytest.approx(4_000_000.0)
        assert vault.power == 0.0
        dump = vault.model_dump()
        assert 'cost' not in dump
        assert 'power' not in dump


class TestBoobyTrap:
    def test_tl6_values(self):
        assert BoobyTrapTL6().tl == 6
        assert BoobyTrapTL6().cost == pytest.approx(100_000.0)
        assert BoobyTrapTL6().damage_per_round == '3D'

    def test_tl8_values(self):
        assert BoobyTrapTL8().tl == 8
        assert BoobyTrapTL8().cost == pytest.approx(300_000.0)
        assert BoobyTrapTL8().damage_per_round == '5D'

    def test_tl10_values(self):
        assert BoobyTrapTL10().tl == 10
        assert BoobyTrapTL10().cost == pytest.approx(500_000.0)
        assert BoobyTrapTL10().damage_per_round == '6D'

    def test_tl12_values(self):
        assert BoobyTrapTL12().tl == 12
        assert BoobyTrapTL12().cost == pytest.approx(1_000_000.0)
        assert BoobyTrapTL12().damage_per_round == '8D'
