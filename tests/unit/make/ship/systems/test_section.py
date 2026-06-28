"""Unit tests for systems/section.py — SystemsSection."""

from ceres.make.ship.systems.access import BreachingTube
from ceres.make.ship.systems.facilities import Workshop
from ceres.make.ship.systems.section import SystemsSection


class TestSystemsSection:
    def test_empty_section_has_no_parts(self):
        section = SystemsSection()
        assert section.internal_systems == []

    def test_section_holds_heterogeneous_parts(self):
        section = SystemsSection(internal_systems=[Workshop(), BreachingTube()])
        assert len(section.internal_systems) == 2
