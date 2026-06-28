"""Unit tests for systems/acceleration.py — AccelerationSeat, AccelerationBench."""

from ceres.make.ship.systems.acceleration import AccelerationBench, AccelerationSeat


class TestAccelerationBench:
    def test_has_four_seats(self):
        assert AccelerationBench().seats == 4

    def test_computed_not_serialized(self):
        bench = AccelerationBench.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        assert bench.tons == 1.0
        assert bench.cost == 10_000.0
        assert bench.power == 0.0
        dump = bench.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestAccelerationSeat:
    def test_half_ton_thirty_kcr(self):
        seat = AccelerationSeat()
        assert seat.tons == 0.5
        assert seat.cost == 30_000.0
