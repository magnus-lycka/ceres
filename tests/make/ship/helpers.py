from ceres.make.ship.occupants import BasicPassage, HighPassage, LowPassage, MiddlePassage


def passengers(*, high: int = 0, middle: int = 0, basic: int = 0, low: int = 0):
    return (
        [HighPassage() for _ in range(high)]
        + [MiddlePassage() for _ in range(middle)]
        + [BasicPassage() for _ in range(basic)]
        + [LowPassage() for _ in range(low)]
    )
