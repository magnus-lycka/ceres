from ceres.base import ShipBase
from ceres.sensors import BasicSensors, CivilianSensors, MilitarySensors


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_basic_sensors_have_zero_tons_cost_and_power():
    s = BasicSensors()
    s.bind(DummyOwner(12, 100))
    assert s.tons == 0
    assert s.cost == 0
    assert s.power == 0


def test_basic_sensors_notes_describe_suite_and_dm():
    s = BasicSensors()
    s.bind(DummyOwner(12, 100))
    assert [(note.category.value, note.message) for note in s.notes] == [
        ('item', 'Basic'),
        ('info', 'Radar, Lidar; DM -4'),
    ]


def test_civilian_grade_tons():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    assert s.minimum_tl == 9
    assert s.ship_tl == 12
    assert s.effective_tl == 12
    assert float(s.tons) == 1.0


def test_civilian_grade_cost():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    assert float(s.cost) == 3_000_000


def test_civilian_grade_power():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    assert s.power == 1


def test_civilian_grade_notes_describe_suite_and_dm():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    assert [(note.category.value, note.message) for note in s.notes] == [
        ('item', 'Civilian Grade'),
        ('info', 'Radar, Lidar; DM -2'),
    ]


def test_military_grade_notes_describe_suite_and_dm():
    s = MilitarySensors()
    s.bind(DummyOwner(12, 100))
    assert [(note.category.value, note.message) for note in s.notes] == [
        ('item', 'Military Grade'),
        ('info', 'Jammers, Radar, Lidar; DM +0'),
    ]


def test_civilian_grade_recomputes_tons_from_input():
    s = CivilianSensors.model_validate({'tons': 999})
    s.bind(DummyOwner(12, 6))
    assert s.tons == 1


def test_civilian_grade_recomputes_cost_from_input():
    s = CivilianSensors.model_validate({'cost': 999})
    s.bind(DummyOwner(12, 6))
    assert s.cost == 3_000_000


def test_civilian_grade_tl_too_low():
    s = CivilianSensors()
    s.bind(DummyOwner(8, 100))
    assert ('error', 'Requires TL9, ship is TL8') in [
        (note.category.value, note.message) for note in s.notes
    ]
