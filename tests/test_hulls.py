from ceres import hull
from ceres.base import ShipBase


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_standard_hull():
    hull_config = hull.standard_hull
    assert hull_config.streamlined == hull.Streamlined.PARTIAL
    assert hull_config.armour_volume_modifier == 1
    assert hull_config.cost(100) == 5_000_000
    assert hull_config.points(100) == 40


def test_streamlined_hull():
    hull_config = hull.streamlined_hull
    assert hull_config.streamlined == hull.Streamlined.YES
    assert hull_config.armour_volume_modifier == 1.2
    assert hull_config.cost(100) == 6_000_000
    assert hull_config.points(100) == 40


def test_sphere_hull():
    hull_config = hull.sphere
    assert hull_config.streamlined == hull.Streamlined.PARTIAL
    assert hull_config.armour_volume_modifier == 0.9
    assert hull_config.cost(100) == 5_500_000
    assert hull_config.points(100) == 40


def test_close_hull():
    hull_config = hull.close_structure
    assert hull_config.streamlined == hull.Streamlined.PARTIAL
    assert hull_config.armour_volume_modifier == 1.5
    assert hull_config.cost(100) == 4_000_000
    assert hull_config.points(100) == 40


def test_light_streamlined_hull():
    hull_config = hull.streamlined_hull.model_copy(update={'light': True})
    assert hull_config.cost(6) == 270_000
    assert hull_config.points(100) == 36


def test_armoured_bulkhead_values():
    bulkhead = hull.ArmouredBulkhead(protected_tonnage=30.0, protected_item='M-Drive')
    owner = DummyOwner(12, 100)
    bulkhead.bind(owner)
    assert bulkhead.tons == 3.0
    assert bulkhead.cost == 600_000
    assert ('item', 'Armoured Bulkhead for M-Drive') in [(note.category.value, note.message) for note in bulkhead.notes]
    assert ('info', 'Critical hit severity reduced by 1 if >1') in [
        (note.category.value, note.message) for note in bulkhead.notes
    ]
