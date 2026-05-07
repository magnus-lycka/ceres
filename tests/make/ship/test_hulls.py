from ceres.make.ship import hull
from ceres.make.ship.base import ShipBase


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
    assert 'Armoured Bulkhead for M-Drive' in bulkhead.notes.items
    assert 'Critical hit severity reduced by 1 if critical hit severity >1' in bulkhead.notes.infos
    assert (
        'Prefer armoured_bulkhead=True on the protected ShipPart over manual ArmouredBulkhead'
        in bulkhead.notes.warnings
    )


def test_armoured_bulkhead_values_are_computed_properties_not_serialized_fields():
    bulkhead = hull.ArmouredBulkhead.model_validate(
        {'protected_tonnage': 30.0, 'protected_item': 'M-Drive', 'tons': 999, 'cost': 999, 'power': 999}
    )
    bulkhead.bind(DummyOwner(12, 100))
    dump = bulkhead.model_dump()

    assert bulkhead.tons == 3.0
    assert bulkhead.cost == 600_000
    assert bulkhead.power == 0.0
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_stealth_values_are_computed_properties_not_serialized_fields():
    stealth = hull.BasicStealth.model_validate({'tons': 999, 'cost': 999, 'power': 999})
    stealth.bind(DummyOwner(12, 100))
    dump = stealth.model_dump()

    assert stealth.tons == 2.0
    assert stealth.cost == 4_000_000
    assert stealth.power == 0.0
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_radiation_shielding_cost():
    ship_hull = hull.Hull(configuration=hull.standard_hull, radiation_shielding=True)
    assert ship_hull.radiation_shielding_cost(400) == 10_000_000
