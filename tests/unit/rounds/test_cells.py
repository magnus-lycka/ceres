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
    injury_headings,
    injury_list_headings,
    injury_list_rows,
    injury_rows,
    round_time_text,
    row_style,
    stun_cell,
    vitality_cells,
)


def hurt_in_a_fight(track: CharacteristicTrack | HitsTrack, *, lethal: int = 0, stun: int = 0) -> tuple[Actor, int]:
    """An actor damaged in round 1, with the round the table would render at."""
    situation = Situation()
    party = situation.add_party('Actors')
    actor = situation.add_actor(Actor(name='Target', party=party, track=track, initiative=4))
    situation.new_round()
    situation.attack(None, actor, lethal=lethal, stun=stun)
    return actor, situation.round_number


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

    actor, current_round = hurt_in_a_fight(track, lethal=4, stun=15)

    assert vitality_cells(track) == ('8/8:0', '8/8:0', '0/8:-3')
    assert stun_cell(actor, current_round) == '4(11)'


def test_the_stun_cell_counts_down_as_the_rounds_pass():
    actor, _ = hurt_in_a_fight(CharacteristicTrack(strength=8, dexterity=8, endurance=8), lethal=4, stun=15)

    assert stun_cell(actor, 5) == '4(7)'


def test_an_unstunned_actor_has_an_empty_stun_cell():
    actor, current_round = hurt_in_a_fight(CharacteristicTrack(strength=8, dexterity=8, endurance=8))

    assert stun_cell(actor, current_round) == ''


def test_an_animal_shows_hits_in_the_endurance_column():
    track = HitsTrack(hits=20)

    track.apply(5, DamageKind.LETHAL)

    assert vitality_cells(track) == ('—', '—', '15/20')


def test_animal_stun_uses_the_same_points_and_rounds_format():
    track = HitsTrack(hits=20)

    actor, current_round = hurt_in_a_fight(track, stun=14)

    assert vitality_cells(track) == ('—', '—', '10/20')
    assert stun_cell(actor, current_round) == '10(4)'


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
    assert not thug.can_act(situation.round_number)
    assert row_style(thug, situation.round_number) == 'background-color: #e5e7eb'
    assert row_style(beast, situation.round_number) == 'background-color: #dcfce7'

    situation.new_round()
    situation.new_round()
    situation.finish_turn(attacker)

    assert thug.can_act(situation.round_number)
    assert row_style(thug, situation.round_number) == 'background-color: #dcfce7'


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


class TestInjuryHistoryView:
    """The first-aid view: what each hit did and how long ago it landed.

    First aid must be applied within one minute — ten rounds — so the referee
    needs to see which wounds are still treatable, which are past saving, and
    which is the urgent one.
    """

    def test_each_hit_is_a_line_showing_its_age_and_its_cost(self):
        situation = Situation()
        party = situation.add_party('Actors')
        track = CharacteristicTrack(strength=8, dexterity=8, endurance=9, excess_to=Chars.STR)
        actor = situation.add_actor(Actor(name='Rin', party=party, track=track, initiative=4))
        for _ in range(13):
            situation.new_round()
            if situation.round_number == 1:
                situation.attack(None, actor, lethal=6)
            if situation.round_number == 8:
                situation.attack(None, actor, lethal=7)  # END is down to 3, so 4 spills to STR

        assert injury_headings(track) == ('Rounds ago', 'Kind', 'STR', 'DEX', 'END')
        assert injury_rows(actor, situation.round_number) == (
            ('12', 'lethal', '—', '—', '-6'),
            ('5', 'lethal', '-4', '—', '-3'),
        )

    def test_wounds_from_an_earlier_fight_have_no_age(self):
        situation = Situation()
        party = situation.add_party('Actors')
        track = CharacteristicTrack(strength=8, dexterity=8, endurance=8)
        actor = situation.add_actor(Actor(name='Rin', party=party, track=track, initiative=4))
        situation.new_round()
        situation.attack(None, actor, lethal=3)

        situation.end()

        assert injury_rows(actor, situation.round_number) == (('earlier', 'lethal', '—', '—', '-3'),)

    def test_an_animal_shows_one_hits_column(self):
        situation = Situation()
        party = situation.add_party('Actors')
        track = HitsTrack(hits=20)
        actor = situation.add_actor(Actor(name='Beast', party=party, track=track, initiative=4))
        situation.new_round()
        situation.attack(None, actor, lethal=5, stun=14)

        assert injury_headings(track) == ('Rounds ago', 'Kind', 'Hits')
        assert injury_rows(actor, situation.round_number) == (
            ('0', 'lethal', '-5'),
            ('0', 'stun', '-5'),  # stun may only suppress Hits to half of 20
        )

    def test_an_unhurt_actor_has_no_lines(self):
        situation = Situation()
        party = situation.add_party('Actors')
        actor = situation.add_actor(
            Actor(name='Rin', party=party, track=CharacteristicTrack(strength=8, dexterity=8, endurance=8))
        )

        assert injury_rows(actor, situation.round_number) == ()


class TestInjuryList:
    """Everyone's injuries at once: the view for deciding whom to treat first.

    Reading who is hurt worst is a job across the whole fight, so it is a list
    beside the round table rather than something reached one actor at a time
    through an editor.
    """

    def situation_with_wounded(self) -> Situation:
        situation = Situation()
        crew = situation.add_party('Crew')
        raiders = situation.add_party('Raiders')
        rin = situation.add_actor(
            Actor(name='Rin', party=crew, track=CharacteristicTrack(strength=8, dexterity=8, endurance=8), initiative=7)
        )
        beast = situation.add_actor(Actor(name='Beast', party=raiders, track=HitsTrack(hits=20), initiative=2))
        situation.new_round()
        situation.attack(None, rin, lethal=4)
        situation.new_round()
        situation.attack(None, rin, stun=3)
        situation.attack(None, beast, lethal=5)
        return situation

    def test_each_wound_is_a_line_under_the_actor_who_took_it(self):
        situation = self.situation_with_wounded()

        assert injury_list_headings() == ('Name', 'Party', 'Rounds ago', 'Kind', 'STR', 'DEX', 'END')
        assert injury_list_rows(situation) == (
            ('Rin', 'Crew', '1', 'lethal', '—', '—', '-4'),
            ('', '', '0', 'stun', '—', '—', '-3'),
            ('Beast', 'Raiders', '0', 'lethal', '—', '—', '-5'),
        )

    def test_an_unhurt_actor_keeps_a_row_of_their_own(self):
        situation = self.situation_with_wounded()
        crew = situation.parties[0]
        situation.add_actor(
            Actor(name='Kes', party=crew, track=CharacteristicTrack(strength=7, dexterity=7, endurance=7), initiative=5)
        )

        assert injury_list_rows(situation)[2] == ('Kes', 'Crew', '—', 'unhurt', '—', '—', '—')

    def test_wounds_carried_from_an_earlier_fight_read_earlier(self):
        situation = self.situation_with_wounded()

        situation.end()

        assert [row[2] for row in injury_list_rows(situation)] == ['earlier', 'earlier', 'earlier']
