"""Unit tests for systems/facilities.py — Workshop, Laboratory, LibraryFacility, ConstructionDeck, TrainingFacility."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.facilities import (
    ConstructionDeck,
    Laboratory,
    LibraryFacility,
    TrainingFacility,
    Workshop,
)


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


class TestWorkshop:
    def test_six_tons_900k(self):
        part = _bind(Workshop())
        assert part.tons == 6.0
        assert part.cost == 900_000.0
        assert part.power == 0.0

    def test_computed_not_serialized(self):
        part = Workshop.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        _bind(part)
        dump = part.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestLaboratory:
    def test_four_tons_one_mcredit(self):
        part = _bind(Laboratory())
        assert part.tons == 4.0
        assert part.cost == 1_000_000.0
        assert part.power == 0.0


class TestLibraryFacility:
    def test_four_tons_four_mcredits_at_tl8(self):
        part = _bind(LibraryFacility())
        assert part.tl == 8
        assert part.tons == 4.0
        assert part.cost == 4_000_000.0
        assert part.power == 0.0


class TestConstructionDeck:
    def test_half_ton_displacement_constructible(self):
        deck = _bind(ConstructionDeck(tons=100))
        assert deck.maximum_constructible_tons == pytest.approx(50.0)

    def test_note_includes_constructible_tons_and_tl(self):
        deck = _bind(ConstructionDeck(tons=100))
        assert 'Can build or repair ships up to 50 tons at TL12' in deck.notes.infos

    def test_power_equals_tonnage(self):
        deck = _bind(ConstructionDeck(tons=100))
        assert deck.cost == 50_000_000.0
        assert deck.power == pytest.approx(100.0)

    def test_tons_is_serialized_design_field(self):
        deck = ConstructionDeck.model_validate({'tons': 100, 'cost': 999, 'power': 999})
        assert deck.tons == 100.0
        dump = deck.model_dump()
        assert dump['tons'] == 100.0
        assert 'cost' not in dump
        assert 'power' not in dump


class TestTrainingFacility:
    def test_two_tons_per_trainee(self):
        facility = _bind(TrainingFacility(trainees=2))
        assert facility.tons == 4.0
        assert facility.cost == 800_000.0

    def test_description_includes_capacity(self):
        facility = _bind(TrainingFacility(trainees=12))
        assert facility.item_description() == 'Training Facility: 12-person capacity'
        assert facility.power == 0.0
