"""Speed Bands: the named ladder a vehicle's speed is expressed on.

Rules: refs/vehicle/02_new_rules.md — Speed Bands
"""

import pytest

from ceres.make.vehicle.speed import SpeedBand


class TestTheLadder:
    """Eleven named bands, numbered 0 to 11."""

    @pytest.mark.parametrize(
        ('band', 'number'),
        [
            (SpeedBand.STOPPED, 0),
            (SpeedBand.IDLE, 1),
            (SpeedBand.VERY_SLOW, 2),
            (SpeedBand.SLOW, 3),
            (SpeedBand.MEDIUM, 4),
            (SpeedBand.HIGH, 5),
            (SpeedBand.FAST, 6),
            (SpeedBand.VERY_FAST, 7),
            (SpeedBand.SUBSONIC, 8),
            (SpeedBand.SUPERSONIC, 9),
            (SpeedBand.HYPERSONIC, 10),
            (SpeedBand.ORBITAL, 11),
        ],
    )
    def test_band_numbers(self, band, number):
        assert band.number == number

    def test_bands_are_ordered_by_number(self):
        assert SpeedBand.SLOW < SpeedBand.MEDIUM
        assert SpeedBand.HYPERSONIC > SpeedBand.SUBSONIC


class TestShifting:
    """Size and features move a vehicle up and down the ladder."""

    def test_a_penalty_moves_down_one_band(self):
        assert SpeedBand.HIGH.shifted(-1) is SpeedBand.MEDIUM

    def test_a_bonus_moves_up_one_band(self):
        assert SpeedBand.HIGH.shifted(+1) is SpeedBand.FAST

    def test_shifting_by_nothing_stays_put(self):
        assert SpeedBand.MEDIUM.shifted(0) is SpeedBand.MEDIUM

    def test_a_vehicle_cannot_be_slower_than_stopped(self):
        assert SpeedBand.IDLE.shifted(-3) is SpeedBand.STOPPED

    def test_a_vehicle_cannot_exceed_the_top_of_the_ladder(self):
        assert SpeedBand.HYPERSONIC.shifted(+5) is SpeedBand.ORBITAL


class TestLabel:
    """A design states a maximum band and the cruising band below it."""

    def test_cruise_is_one_band_slower(self):
        assert SpeedBand.HIGH.cruise is SpeedBand.MEDIUM

    def test_a_stopped_vehicle_cruises_stopped(self):
        assert SpeedBand.STOPPED.cruise is SpeedBand.STOPPED
