"""Cell formats for the table, as specified by the referee.

Characteristics read `current/max:DM` — 5/8:-1, 0/6:-3, 9/9:+1.
Stun reads `points(rounds)` for every actor — 4(11).
"""

from ceres.character.domain.characteristics import Chars
from ceres.rounds.domain.actions import AttackKind, ReactionKind
from ceres.rounds.domain.actor import Actor, ActorCondition, TurnState
from ceres.rounds.domain.damage import DamageKind
from ceres.rounds.domain.situation import Situation
from ceres.rounds.domain.tracks import CharacteristicTrack, HitsTrack
from ceres.rounds.ui.table import (
    characteristic_cell,
    condition_tags,
    round_time_text,
    row_style,
    stun_cell,
    vitality_cells,
)


def test_round_time_is_shown_as_the_interval_in_progress():
    assert round_time_text(1) == 'Round 1: 0–6s'
    assert round_time_text(2) == 'Round 2: 6–12s'


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


def test_animal_stun_uses_the_same_points_and_rounds_format():
    track = HitsTrack(hits=20)

    track.apply(14, DamageKind.STUN)

    assert vitality_cells(track) == ('—', '—', '10/20')
    assert stun_cell(track) == '10(4)'


def test_a_stunned_actor_is_grey_while_the_next_actor_is_green():
    situation = Situation()
    party = situation.add_party('Actors')
    attacker = situation.add_actor(
        Actor(
            name='Attacker',
            party=party,
            track=CharacteristicTrack(strength=8, dexterity=8, endurance=8),
            initiative=6,
        )
    )
    thug = situation.add_actor(
        Actor(
            name='Thug',
            party=party,
            track=CharacteristicTrack(strength=7, dexterity=7, endurance=7),
            initiative=4,
        )
    )
    beast = situation.add_actor(Actor(name='Beast', party=party, track=HitsTrack(hits=20), initiative=2))
    situation.new_round()

    situation.attack(attacker, thug, AttackKind.RANGED, stun=9)

    assert thug.turn_state is TurnState.READY
    assert not thug.can_act
    assert row_style(thug) == 'background-color: #e5e7eb'
    assert row_style(beast) == 'background-color: #dcfce7'

    situation.new_round()
    situation.new_round()
    situation.finish_turn(attacker)

    assert thug.can_act
    assert row_style(thug) == 'background-color: #dcfce7'


def test_prone_is_a_visible_condition_tag_until_cleared():
    situation = Situation()
    party = situation.add_party('Actors')
    actor = situation.add_actor(
        Actor(
            name='Rin',
            party=party,
            track=CharacteristicTrack(strength=8, dexterity=8, endurance=8),
            initiative=6,
        )
    )
    situation.new_round()
    situation.react(actor, ReactionKind.DIVE)

    assert condition_tags(actor) == ('Prone',)

    situation.clear_condition(actor, ActorCondition.PRONE)

    assert condition_tags(actor) == ()
