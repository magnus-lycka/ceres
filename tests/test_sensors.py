import pytest
from pydantic import ValidationError
from ceres.sensors import CivilianGradeSensors


class DummyOwner:
    def __init__(self, tl, displacement):
        self.tl = tl
        self.displacement = displacement


def test_civilian_grade_tons():
    s = CivilianGradeSensors()
    s.bind(DummyOwner(12, 6))
    assert s.minimum_tl == 9
    assert s.ship_tl == 12
    assert s.effective_tl == 12
    assert float(s.tons) == 1.0


def test_civilian_grade_cost():
    s = CivilianGradeSensors()
    s.bind(DummyOwner(12, 6))
    assert float(s.cost) == 3_000_000


def test_civilian_grade_power():
    s = CivilianGradeSensors()
    s.bind(DummyOwner(12, 6))
    assert float(s.power) == 1


def test_civilian_grade_cannot_set_tons():
    with pytest.raises(ValidationError):
        CivilianGradeSensors(tons=999)


def test_civilian_grade_cannot_set_cost():
    with pytest.raises(ValidationError):
        CivilianGradeSensors(cost=999)


def test_civilian_grade_tl_too_low():
    # Civilian Grade needs TL9; TL8 ship should fail
    with pytest.raises(ValueError):
        s = CivilianGradeSensors()
        s.bind(DummyOwner(8, 100))
