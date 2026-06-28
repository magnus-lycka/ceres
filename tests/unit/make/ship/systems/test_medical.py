"""Unit tests for systems/medical.py — BasicAutodoc, MedicalBay, Biosphere."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.medical import BasicAutodoc, Biosphere, MedicalBay


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


class TestMedicalBay:
    def test_four_tons_two_mcr_one_power(self):
        bay = _bind(MedicalBay())
        assert bay.tons == 4.0
        assert bay.cost == 2_000_000.0
        assert bay.power == 1.0

    def test_autodoc_adds_to_cost(self):
        bay_with_doc = _bind(MedicalBay(autodoc=BasicAutodoc()))
        bay_plain = _bind(MedicalBay())
        assert bay_with_doc.cost == bay_plain.cost + BasicAutodoc().cost

    def test_autodoc_does_not_change_tonnage(self):
        assert _bind(MedicalBay(autodoc=BasicAutodoc())).tons == _bind(MedicalBay()).tons


class TestBiosphere:
    def test_power_equals_tonnage(self):
        bio = _bind(Biosphere(tons=4.0))
        assert bio.power == pytest.approx(4.0)

    def test_cost_per_ton(self):
        bio = _bind(Biosphere(tons=4.0))
        assert bio.cost == pytest.approx(800_000.0)
