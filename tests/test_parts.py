from ceres import parts


def test_base_part():
    part = parts.ShipPart(cost=1, tl=9, power=3.14, tons=4.44)
    assert part.cost == 1
    assert part.tl == 9
    assert part.power == 3.14
    assert part.tons == 4.44
