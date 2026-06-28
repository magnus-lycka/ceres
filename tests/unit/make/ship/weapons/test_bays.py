"""Unit tests for weapons/bays.py — bay TL validation, customisation rules, carronades."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.parts import Advanced, HighTechnology, SizeReduction
from ceres.make.ship.weapons.bays import (
    FusionCarronade,
    GeneralPurposeMassDriverBay,
    MediumMissileBay,
    MediumParticleBeamBay,
    PlasmaCarronade,
    SmallMissileBay,
)
from ceres.make.ship.weapons.common import HighYield


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=1_000):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=1_000):
    part.bind(_Ship(tl, displacement))
    return part


class TestBayCustomisation:
    def test_small_missile_bay_size_reduction_reduces_tons(self):
        base = _bind(SmallMissileBay())
        reduced = _bind(SmallMissileBay(customisation=Advanced(modifications=[SizeReduction])), tl=13)
        assert reduced.tons < base.tons

    def test_high_yield_allowed_for_particle_beam_bay(self):
        mods = [HighYield, SizeReduction, SizeReduction]
        bay = _bind(MediumParticleBeamBay(customisation=HighTechnology(modifications=mods)), tl=15)
        assert 'Modification not allowed for Bay: High Yield' not in bay.notes.errors

    def test_high_yield_not_applicable_for_missile_bay(self):
        bay = _bind(MediumMissileBay(customisation=Advanced(modifications=[HighYield])), tl=10)
        assert 'High Yield is not applicable for' in '\n'.join(bay.notes.errors)

    def test_high_technology_bay_tl_requirement_is_base_tl_plus_3(self):
        mods = [SizeReduction, SizeReduction, SizeReduction]
        bay = _bind(MediumParticleBeamBay(customisation=HighTechnology(modifications=mods)), tl=15)
        assert bay.tl == 12
        assert 'Requires TL18' not in '\n'.join(bay.notes.errors)

    def test_high_technology_bay_errors_below_required_tl(self):
        mods = [SizeReduction, SizeReduction, SizeReduction]
        bay = _bind(MediumParticleBeamBay(customisation=HighTechnology(modifications=mods)), tl=14)
        assert 'Requires TL15, ship is TL14' in bay.notes.errors


class TestCarronade:
    def test_plasma_carronade_uses_four_hardpoints(self):
        carronade = _bind(PlasmaCarronade(), tl=10)
        assert carronade.hardpoints_required == 4

    def test_fusion_carronade_values(self):
        carronade = _bind(FusionCarronade())
        assert carronade.tons == pytest.approx(4.0)
        assert carronade.cost == pytest.approx(12_000_000.0)
        assert carronade.power == pytest.approx(45.0)

    def test_fusion_carronade_radiation_in_notes(self):
        carronade = _bind(FusionCarronade())
        assert any('Radiation' in info for info in carronade.notes.infos)


class TestGeneralPurposeMassDriverBay:
    def test_base_launch_capacity_fifty_tons(self):
        bay = _bind(GeneralPurposeMassDriverBay(), tl=8)
        assert bay.launch_capacity == pytest.approx(50.0)

    def test_extra_capacity_increases_launch_capacity(self):
        bay = _bind(GeneralPurposeMassDriverBay(extra_launch_capacity=3), tl=8)
        assert bay.launch_capacity == pytest.approx(53.0)

    def test_inaccuracy_note_present(self):
        bay = _bind(GeneralPurposeMassDriverBay(), tl=8)
        assert any('DM-4' in info for info in bay.notes.infos)
