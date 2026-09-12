"""Speed Bands: the named ladder vehicle speed is expressed on.

Rules: refs/vehicle/02_new_rules.md — Speed Bands
"""

from enum import IntEnum


class SpeedBand(IntEnum):
    """One rung of the Speed Band ladder.

    The member's value is the Speed Band Number the rules use directly in
    collision damage and acceleration, so a band is an int: `SpeedBand.SLOW == 3`.
    """

    STOPPED = 0
    IDLE = 1
    VERY_SLOW = 2
    SLOW = 3
    MEDIUM = 4
    HIGH = 5
    FAST = 6
    VERY_FAST = 7
    SUBSONIC = 8
    SUPERSONIC = 9
    HYPERSONIC = 10
    ORBITAL = 11

    def shifted(self, bands: int) -> SpeedBand:
        """Move along the ladder, stopping at either end rather than falling off."""
        return SpeedBand(min(max(self.value + bands, SpeedBand.STOPPED), SpeedBand.ORBITAL))

    @property
    def cruise(self) -> SpeedBand:
        """The band a vehicle sustains, one below its maximum."""
        return self.shifted(-1)

    def __str__(self) -> str:
        return self.name.replace('_', ' ').title()
