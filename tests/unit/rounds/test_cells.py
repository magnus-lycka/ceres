"""Cell formats for the table, as specified by the referee.

Characteristics read `current/max:DM` — 5/8:-1, 0/6:-3, 9/9:+1.
Stun reads `points(rounds)` — 4(11).
"""

from ceres.character.domain.characteristics import Chars
from ceres.rounds.domain.damage import DamageKind
from ceres.rounds.domain.tracks import CharacteristicTrack, HitsTrack
from ceres.rounds.ui.table import characteristic_cell, stun_cell, vitality_cells


def test_undamaged_characteristic_shows_a_bare_zero_dm():
    track = CharacteristicTrack(strength=8, dexterity=8, endurance=8)

    assert characteristic_cell(track, Chars.STR) == '8/8:0'


def test_a_positive_dm_is_signed():
    track = CharacteristicTrack(strength=9, dexterity=9, endurance=9)

    assert characteristic_cell(track, Chars.STR) == '9/9:+1'


def test_a_damaged_characteristic_shows_its_impaired_dm():
    track = CharacteristicTrack(strength=8, dexterity=8, endurance=8)

    track.apply(3, DamageKind.LETHAL)

    assert characteristic_cell(track, Chars.END) == '5/8:-1'


def test_an_exhausted_characteristic_reads_minus_three():
    track = CharacteristicTrack(strength=6, dexterity=6, endurance=6)

    track.apply(6, DamageKind.LETHAL)

    assert characteristic_cell(track, Chars.END) == '0/6:-3'


def test_the_referees_worked_example_renders_as_specified():
    """888, then 4 lethal and 15 stun: 8/8:0 | 8/8:0 | 0/8:-3 | 4(11)."""
    track = CharacteristicTrack(strength=8, dexterity=8, endurance=8)

    track.apply(4, DamageKind.LETHAL)
    track.apply(15, DamageKind.STUN)

    assert vitality_cells(track) == ('8/8:0', '8/8:0', '0/8:-3')
    assert stun_cell(track) == '4(11)'


def test_an_unstunned_actor_has_an_empty_stun_cell():
    track = CharacteristicTrack(strength=8, dexterity=8, endurance=8)

    assert stun_cell(track) == ''


def test_an_animal_shows_hits_in_the_endurance_column():
    track = HitsTrack(hits=20)

    track.apply(5, DamageKind.LETHAL)

    assert vitality_cells(track) == ('—', '—', '15/20')
