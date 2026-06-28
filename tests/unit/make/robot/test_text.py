"""Unit tests for text.py — format_traits and format_credits."""

from ceres.make.robot.chassis import Trait
from ceres.make.robot.text import format_credits, format_traits


class TestFormatTraits:
    def test_empty_list_returns_dash(self):
        assert format_traits([]) == '—'

    def test_single_trait(self):
        assert format_traits([Trait('ATV')]) == 'ATV'

    def test_multiple_traits(self):
        result = format_traits([Trait('Armour', '+2'), Trait('Small', -2)])
        assert result == 'Armour (+2), Small (-2)'


class TestFormatCredits:
    def test_hundreds(self):
        assert format_credits(400.0) == 'Cr400'

    def test_thousands(self):
        assert format_credits(12_000.0) == 'Cr12,000'

    def test_millions(self):
        assert format_credits(1_000_000.0) == 'MCr1'

    def test_fractional_millions(self):
        assert format_credits(2_500_000.0) == 'MCr2.5'
