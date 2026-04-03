from ceres import ship


def test_standard_hull():
    hull = ship.standard_hull
    assert hull.streamlined == ship.Streamlined.PARTIAL
    assert hull.armour_volume_modifier == 1
    assert hull.cost(100) == 5_000_000
    assert hull.points(100) == 40


def test_streamlined_hull():
    hull = ship.streamlined_hull
    assert hull.streamlined == ship.Streamlined.YES
    assert hull.armour_volume_modifier == 1.2
    assert hull.cost(100) == 6_000_000
    assert hull.points(100) == 40


def test_sphere_hull():
    hull = ship.sphere
    assert hull.streamlined == ship.Streamlined.PARTIAL
    assert hull.armour_volume_modifier == 0.9
    assert hull.cost(100) == 5_500_000
    assert hull.points(100) == 40


def test_close_hull():
    hull = ship.close_structure
    assert hull.streamlined == ship.Streamlined.PARTIAL
    assert hull.armour_volume_modifier == 1.5
    assert hull.cost(100) == 4_000_000
    assert hull.points(100) == 40


def test_light_streamlined_hull():
    hull = ship.streamlined_hull.model_copy(update={'light': True})
    assert hull.cost(6) == 270_000
    assert hull.points(100) == 36
