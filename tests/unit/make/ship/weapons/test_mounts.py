"""Unit tests for weapons/mounts.py — FixedMount and Turret types."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.parts import Advanced, EnergyEfficient, HighTechnology
from ceres.make.ship.weapons.common import PulseLaser, Sandcaster, VeryHighYield
from ceres.make.ship.weapons.mounts import (
    DoubleTurret,
    FixedMount,
    SingleTurret,
    TripleTurret,
)


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=100):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=100):
    part.bind(_Ship(tl, displacement))
    return part


class TestFixedMount:
    def test_firmpoint_reduces_power_by_25pct(self):
        fp = _bind(FixedMount(weapons=[PulseLaser()]), displacement=6)
        # Pulse laser base_power 4; firmpoint: floor(4 * 0.75) = 3
        assert float(fp.power) == 3.0

    def test_firmpoint_power_with_energy_efficient(self):
        # HighTechnology(VHY + EE): floor(4 * 0.75 * 0.75) = floor(2.25) = 2
        laser = PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))
        fp = _bind(FixedMount(weapons=[laser]), displacement=6)
        assert float(fp.power) == 2.0

    def test_firmpoint_has_no_tonnage(self):
        fp = _bind(FixedMount(weapons=[PulseLaser()]), displacement=6)
        assert float(fp.tons) == 0.0

    def test_cost_is_mount_plus_weapon(self):
        fp = _bind(FixedMount(weapons=[PulseLaser()]), displacement=6)
        # mount MCr0.1 + weapon MCr1.0 = 1,100,000
        assert float(fp.cost) == pytest.approx(1_100_000.0)

    def test_computed_not_serialized(self):
        raw = {'weapons': [{'weapon_type': 'pulse_laser'}], 'tons': 999, 'cost': 999, 'power': 999}
        fp = FixedMount.model_validate(raw)
        _bind(fp, displacement=6)
        dump = fp.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump

    def test_pop_up_adds_one_ton_and_doubles_mount_cost(self):
        mount = _bind(FixedMount(pop_up=True, weapons=[PulseLaser()]))
        assert mount.tons == pytest.approx(1.0)
        assert mount.cost == pytest.approx(2_100_000.0)
        assert 'Pop-up mounting: concealed until deployed' in mount.notes.infos

    def test_pop_up_requires_tl10(self):
        mount = _bind(FixedMount(pop_up=True, weapons=[PulseLaser()]), tl=9)
        assert 'Requires TL10, ship is TL9' in mount.notes.errors

    def test_single_weapon_notes_show_weapon_name_as_item(self):
        fp = _bind(FixedMount(weapons=[PulseLaser()]), displacement=6)
        assert fp.notes.items == ['Pulse Laser']

    def test_multiple_weapons_shows_fixed_mount_as_item(self):
        fp = _bind(FixedMount(weapons=[PulseLaser(), PulseLaser()]))
        assert fp.notes.items == ['Fixed Mount']
        assert 'Pulse Laser × 2' in fp.notes.contents


class TestTurret:
    def test_single_turret_power_includes_mount(self):
        # Single turret base power 1 + weapon 4 = 5
        t = _bind(SingleTurret(weapons=[PulseLaser()]))
        assert float(t.power) == pytest.approx(5.0)

    def test_triple_turret_groups_identical_weapons_in_notes(self):
        turret = TripleTurret(weapons=[PulseLaser(), PulseLaser(), PulseLaser()])
        _bind(turret)
        assert turret.notes.contents == ['Pulse Laser × 3']

    def test_triple_turret_customisation_note_not_duplicated(self):
        turret = TripleTurret(
            weapons=[
                PulseLaser(customisation=Advanced(modifications=[EnergyEfficient])),
                PulseLaser(customisation=Advanced(modifications=[EnergyEfficient])),
                PulseLaser(customisation=Advanced(modifications=[EnergyEfficient])),
            ]
        )
        _bind(turret)
        infos = turret.notes.infos
        assert infos.count('Advanced: Energy Efficient') == 1

    def test_double_turret_cost_includes_both_weapons(self):
        turret = DoubleTurret(weapons=[PulseLaser(), Sandcaster()])
        _bind(turret)
        # 500,000 (mount) + 1,000,000 (pulse) + 250,000 (sandcaster) = 1,750,000
        assert turret.cost == pytest.approx(1_750_000.0)
