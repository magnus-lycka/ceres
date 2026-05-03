import pytest

from ceres.shared import CeresPart, Equipment


def test_equipment_empty_defaults():
    e = Equipment()
    assert e.tl == 0
    assert e.cost == 0.0
    assert e.mass_kg == 0.0
    assert e.parts == []


def test_equipment_with_explicit_fields():
    part = CeresPart(tl=12, cost=1000.0)
    e = Equipment(parts=[part], tl=12, cost=1000.0, mass_kg=0.5)
    assert e.tl == 12
    assert e.cost == 1000.0
    assert e.mass_kg == 0.5
    assert e.parts == [part]


def test_equipment_is_frozen():
    e = Equipment()
    with pytest.raises(Exception):
        e.tl = 5  # type: ignore[misc]


def test_equipment_serialises_and_roundtrips():
    part = CeresPart(tl=10, cost=500.0)
    e = Equipment(parts=[part], tl=10, cost=500.0, mass_kg=0.25)
    json_str = e.model_dump_json()
    e2 = Equipment.model_validate_json(json_str)
    assert e2.tl == 10
    assert e2.cost == 500.0
    assert e2.mass_kg == 0.25
    assert e2.parts[0].tl == 10
