from ceres import hull


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
