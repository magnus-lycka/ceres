"""Round flow: initiative steps and the green/grey turn state machine.

Derived from refs/core/03_combat.md:

- :30, 36  initiative is the Effect of a DEX or INT check, individually or one
           check for all the forces the referee controls
- :62      actors act in initiative order, ties broken by DEX, then simultaneous
- :32      an actor may freely delay their action until later in the turn
- :81      a round ends once everyone has had a chance to act
"""

import pytest

from ceres.character.domain.characteristics import Chars
from ceres.rounds.domain.actions import AttackKind, ReactionKind
from ceres.rounds.domain.actor import Actor, ActorCondition, TurnState
from ceres.rounds.domain.roster import Roster
from ceres.rounds.domain.situation import Situation
from ceres.rounds.domain.tracks import CharacteristicTrack, HitsTrack


def character(name: str, *, dexterity: int = 8) -> CharacteristicTrack:
    return CharacteristicTrack(strength=8, dexterity=dexterity, endurance=8)


@pytest.fixture
def situation() -> Situation:
    return Situation(name='Cargo bay')


class TestRoster:
    def test_roster_membership_is_independent_of_situation_participation(self):
        roster = Roster()
        crew = roster.add_party('Crew')
        rin = roster.add_actor(Actor(name='Rin', party=crew, track=character('Rin')))
        situation = Situation(roster=roster)

        assert rin in roster.actors
        assert not situation.is_participating(rin)

        situation.include(rin)
        assert situation.is_participating(rin)

        situation.withdraw(rin)
        assert rin in roster.actors
        assert not situation.is_participating(rin)

    def test_removing_an_actor_from_the_roster_also_withdraws_them(self, situation):
        crew = situation.add_party('Crew')
        rin = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin')))

        situation.remove_from_roster(rin)

        assert rin not in situation.actors
        assert rin not in situation.roster.actors

    def test_actors_belong_to_a_party(self, situation):
        crew = situation.add_party('Crew')

        actor = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin')))

        assert actor.party is crew
        assert situation.actors == [actor]

    def test_actors_may_join_mid_situation(self, situation):
        crew = situation.add_party('Crew')
        situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=3))
        situation.new_round()

        raiders = situation.add_party('Raiders')
        latecomer = situation.add_actor(Actor(name='Beast', party=raiders, track=HitsTrack(hits=20), initiative=9))

        assert latecomer in situation.actors

    def test_a_withdrawn_actor_leaves_the_turn_order(self, situation):
        crew = situation.add_party('Crew')
        rin = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=5))
        situation.add_actor(Actor(name='Sana', party=crew, track=character('Sana'), initiative=2))

        situation.withdraw(rin)

        assert [a.name for a in situation.turn_order()] == ['Sana']


class TestInitiative:
    def test_turn_order_runs_from_highest_initiative_down(self, situation):
        crew = situation.add_party('Crew')
        situation.add_actor(Actor(name='Slow', party=crew, track=character('Slow'), initiative=1))
        situation.add_actor(Actor(name='Fast', party=crew, track=character('Fast'), initiative=7))

        assert [a.name for a in situation.turn_order()] == ['Fast', 'Slow']

    def test_ties_are_broken_by_dexterity(self, situation):
        crew = situation.add_party('Crew')
        situation.add_actor(Actor(name='Nimble', party=crew, track=character('N', dexterity=11), initiative=4))
        situation.add_actor(Actor(name='Clumsy', party=crew, track=character('C', dexterity=5), initiative=4))

        assert [a.name for a in situation.turn_order()] == ['Nimble', 'Clumsy']

    def test_a_party_initiative_is_inherited_by_its_members(self, situation):
        raiders = situation.add_party('Raiders')
        situation.set_party_initiative(raiders, 6)
        thug = situation.add_actor(Actor(name='Thug', party=raiders, track=character('Thug')))

        assert thug.initiative_value == 6

    def test_an_individual_initiative_overrides_the_party(self, situation):
        raiders = situation.add_party('Raiders')
        situation.set_party_initiative(raiders, 6)
        boss = situation.add_actor(Actor(name='Boss', party=raiders, track=character('Boss'), initiative=10))

        assert boss.initiative_value == 10

    def test_initiative_is_kept_across_rounds_by_default(self, situation):
        crew = situation.add_party('Crew')
        rin = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=5))

        situation.new_round()
        situation.new_round()

        assert rin.initiative_value == 5


class TestTurnStates:
    """Highest initiative goes green; acting greys them out; waiting keeps green."""

    def setup_situation(self, situation) -> tuple[Actor, Actor, Actor]:
        crew = situation.add_party('Crew')
        fast = situation.add_actor(Actor(name='Fast', party=crew, track=character('Fast'), initiative=8))
        middle = situation.add_actor(Actor(name='Middle', party=crew, track=character('Middle'), initiative=5))
        slow = situation.add_actor(Actor(name='Slow', party=crew, track=character('Slow'), initiative=2))
        situation.new_round()
        return fast, middle, slow

    def test_only_the_highest_initiative_starts_ready(self, situation):
        fast, middle, slow = self.setup_situation(situation)

        assert fast.turn_state is TurnState.READY
        assert middle.turn_state is TurnState.PENDING
        assert slow.turn_state is TurnState.PENDING

    def test_acting_greys_an_actor_out_and_opens_the_next_step(self, situation):
        fast, middle, slow = self.setup_situation(situation)

        situation.finish_turn(fast)

        assert fast.turn_state is TurnState.ACTED
        assert middle.turn_state is TurnState.READY
        assert slow.turn_state is TurnState.PENDING

    def test_waiting_keeps_an_actor_ready_while_the_next_step_opens(self, situation):
        fast, middle, _slow = self.setup_situation(situation)

        situation.wait(fast)

        assert fast.turn_state is TurnState.READY
        assert middle.turn_state is TurnState.READY

    def test_an_actor_who_waited_may_still_act_later(self, situation):
        fast, middle, slow = self.setup_situation(situation)
        situation.wait(fast)
        situation.finish_turn(middle)

        situation.finish_turn(fast)

        assert fast.turn_state is TurnState.ACTED
        assert slow.turn_state is TurnState.READY

    def test_a_step_holding_several_actors_opens_them_together(self, situation):
        crew = situation.add_party('Crew')
        first = situation.add_actor(Actor(name='A', party=crew, track=character('A'), initiative=4))
        second = situation.add_actor(Actor(name='B', party=crew, track=character('B'), initiative=4))
        situation.new_round()

        assert first.turn_state is TurnState.READY
        assert second.turn_state is TurnState.READY

    def test_a_new_round_makes_everyone_pending_again(self, situation):
        fast, middle, _slow = self.setup_situation(situation)
        situation.finish_turn(fast)

        situation.new_round()

        assert fast.turn_state is TurnState.READY
        assert middle.turn_state is TurnState.PENDING

    def test_the_round_counter_and_elapsed_time_advance(self, situation):
        situation.new_round()
        assert situation.round_number == 1

        situation.new_round()

        assert situation.round_number == 2
        assert situation.elapsed_seconds == 12


class TestWhoMayAct:
    def actor_in(self, situation: Situation) -> Actor:
        crew = situation.add_party('Crew')
        return situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=5))

    def test_a_ready_actor_may_act(self, situation):
        rin = self.actor_in(situation)
        situation.new_round()

        assert rin.can_act(situation.round_number)

    def test_an_unconscious_actor_may_not_act(self, situation):
        rin = self.actor_in(situation)
        situation.new_round()

        situation.attack(None, rin, lethal=20)

        assert not rin.can_act(situation.round_number)

    def test_a_stunned_actor_may_not_act(self, situation):
        rin = self.actor_in(situation)
        situation.new_round()

        situation.attack(None, rin, stun=12)

        assert not rin.can_act(situation.round_number)

    def test_incapacitation_lasts_until_the_round_it_ends(self, situation):
        """END 8 hit by 10 stun is out for the two rounds of overflow (:366)."""
        rin = self.actor_in(situation)
        situation.new_round()

        situation.attack(None, rin, stun=10)

        assert rin.incapacitated_until == 3
        situation.new_round()
        assert not rin.can_act(situation.round_number)
        situation.new_round()
        assert rin.can_act(situation.round_number)

    def test_a_second_stun_extends_the_incapacitation_without_stacking_it(self, situation):
        rin = self.actor_in(situation)
        situation.new_round()
        situation.attack(None, rin, stun=10)

        situation.new_round()
        situation.attack(None, rin, stun=3)

        assert rin.incapacitated_until == 5


class TestInjuriesOutliveTheSituation:
    """Injuries belong to the actor; anything counted in rounds does not."""

    def actor_in(self, situation: Situation) -> tuple[Actor, CharacteristicTrack]:
        crew = situation.add_party('Crew')
        track = character('Rin')
        return situation.add_actor(Actor(name='Rin', party=crew, track=track, initiative=5)), track

    def test_damage_records_the_round_it_landed_in(self, situation):
        rin, track = self.actor_in(situation)
        situation.new_round()
        situation.new_round()

        situation.attack(None, rin, lethal=3)

        (injury,) = track.injuries
        assert injury.when == 2
        assert injury.rounds_ago(situation.round_number) == 0

    def test_ending_the_situation_keeps_the_wounds_and_drops_the_rounds(self, situation):
        rin, track = self.actor_in(situation)
        situation.new_round()
        situation.attack(None, rin, lethal=3, stun=10)
        assert rin.incapacitated_until == 6  # END was 5 when the 10 stun landed

        situation.end()

        assert track.current(Chars.END) == 0  # 3 lethal and 5 stun still stand
        assert track.stun_points == 5
        assert all(injury.is_earlier for injury in track.injuries)
        assert rin.incapacitated_until is None

    def test_only_clearing_stun_gives_the_suppressed_points_back(self, situation):
        """An hour of rest is the referee's to apply, not the app's to infer."""
        rin, track = self.actor_in(situation)
        situation.new_round()
        situation.attack(None, rin, lethal=3, stun=10)
        situation.end()

        rin.clear_stun()

        assert track.current(Chars.END) == 5
        assert track.stun_points == 0


class TestCombatActions:
    def setup_actor(self, situation: Situation) -> Actor:
        crew = situation.add_party('Crew')
        actor = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=5))
        situation.new_round()
        return actor

    def test_a_reaction_before_done_penalises_the_current_turn(self, situation):
        actor = self.setup_actor(situation)

        situation.react(actor, ReactionKind.DODGE)

        assert actor.reaction_dm == -1
        situation.finish_turn(actor)
        assert actor.reaction_dm == 0

    def test_a_reaction_after_acting_penalises_the_next_round(self, situation):
        actor = self.setup_actor(situation)
        situation.finish_turn(actor)

        situation.react(actor, ReactionKind.PARRY)
        situation.new_round()

        assert actor.reaction_dm == -1
        situation.finish_turn(actor)
        assert actor.reaction_dm == 0

    def test_reactions_on_both_sides_of_a_turn_attach_to_different_sets(self, situation):
        actor = self.setup_actor(situation)
        situation.react(actor, ReactionKind.DODGE)
        situation.finish_turn(actor)

        situation.react(actor, ReactionKind.PARRY)

        assert actor.reaction_dm == -1
        situation.new_round()
        assert actor.reaction_dm == -1

    def test_diving_before_done_forfeits_the_current_turn(self, situation):
        actor = self.setup_actor(situation)

        situation.react(actor, ReactionKind.DIVE)

        assert actor.turn_state is TurnState.ACTED
        assert ActorCondition.PRONE in actor.conditions

    def test_diving_after_done_forfeits_the_next_turn(self, situation):
        actor = self.setup_actor(situation)
        situation.finish_turn(actor)

        situation.react(actor, ReactionKind.DIVE)
        assert ActorCondition.PRONE in actor.conditions
        situation.new_round()

        assert actor.turn_state is TurnState.ACTED
        assert not actor.can_act(situation.round_number)

    def test_prone_persists_across_rounds_until_explicitly_cleared(self, situation):
        actor = self.setup_actor(situation)
        situation.react(actor, ReactionKind.DIVE)

        situation.new_round()

        assert ActorCondition.PRONE in actor.conditions
        situation.clear_condition(actor, ActorCondition.PRONE)
        assert ActorCondition.PRONE not in actor.conditions

    def test_actor_round_state_can_be_corrected(self, situation):
        actor = self.setup_actor(situation)
        raiders = situation.add_party('Raiders')

        situation.correct_actor(
            actor,
            name='Corrected Rin',
            party=raiders,
            initiative=None,
            turn_state=TurnState.ACTED,
            reaction_dm=-2,
            last_action='Ranged Thug',
            conditions={ActorCondition.PRONE},
            forfeit_next_turn=True,
            waited=False,
        )

        assert actor.name == 'Corrected Rin'
        assert actor.party is raiders
        assert actor.initiative is None
        assert actor.turn_state is TurnState.ACTED
        assert actor.reaction_dm == -2
        assert actor.last_action == 'Ranged Thug'
        assert actor.conditions == {ActorCondition.PRONE}
        assert actor.forfeits_next_turn

    @pytest.mark.parametrize(
        ('kind', 'description'),
        [
            (AttackKind.MELEE, 'Melee Beast'),
            (AttackKind.RANGED, 'Ranged Beast'),
        ],
    )
    def test_recording_an_attack_finishes_the_attackers_turn(self, situation, kind, description):
        attacker = self.setup_actor(situation)
        beast = situation.add_actor(Actor(name='Beast', party=attacker.party, track=HitsTrack(hits=20), initiative=2))

        situation.attack(attacker, beast, kind)

        assert attacker.last_action == description
        assert attacker.turn_state is TurnState.ACTED

    def test_done_finishes_a_turn_without_recording_an_attack(self, situation):
        actor = self.setup_actor(situation)

        situation.finish_turn(actor)

        assert actor.last_action == ''
        assert actor.turn_state is TurnState.ACTED

    def test_other_damage_does_not_finish_the_targets_turn(self, situation):
        target = self.setup_actor(situation)

        situation.attack(None, target, lethal=3)

        assert isinstance(target.track, CharacteristicTrack)
        assert target.track.current(Chars.END) == 5
        assert target.turn_state is TurnState.READY


class TestUnconsciousness:
    """An unconscious Traveller may attempt an END check every minute (:539).

    The app does not roll and does not record the outcome. It says when a check
    is due, and the referee clicks the marker away when the Traveller comes to.
    A minute is ten rounds, and the cumulative DM+1 per failed check needs no
    bookkeeping: a check that was due while the marker still stands was failed.
    """

    def knocked_out(self, situation: Situation) -> tuple[Actor, CharacteristicTrack]:
        crew = situation.add_party('Crew')
        track = character('Rin')
        rin = situation.add_actor(Actor(name='Rin', party=crew, track=track, initiative=5))
        situation.new_round()
        situation.attack(None, rin, lethal=16)  # END and DEX to zero
        return rin, track

    def advance_to(self, situation: Situation, round_number: int) -> None:
        while situation.round_number < round_number:
            situation.new_round()

    def test_no_check_is_due_until_a_minute_has_passed(self, situation):
        rin, _track = self.knocked_out(situation)

        self.advance_to(situation, 10)

        assert rin.is_unconscious
        assert not rin.recovery_check_due(situation.round_number)

    def test_a_check_falls_due_a_minute_after_going_down(self, situation):
        rin, _track = self.knocked_out(situation)

        self.advance_to(situation, 11)

        assert rin.recovery_check_due(situation.round_number)
        assert rin.recovery_check_dm(situation.round_number) == 0

    def test_a_check_left_standing_was_failed_so_the_next_one_carries_dm_plus_one(self, situation):
        rin, _track = self.knocked_out(situation)

        self.advance_to(situation, 21)

        assert rin.recovery_check_due(situation.round_number)
        assert rin.recovery_check_dm(situation.round_number) == 1

    def test_the_dm_grows_by_one_for_every_minute_they_stay_down(self, situation):
        rin, _track = self.knocked_out(situation)

        self.advance_to(situation, 41)

        assert rin.recovery_check_dm(situation.round_number) == 3

    def test_waking_them_clears_the_marker_without_healing_anything(self, situation):
        rin, track = self.knocked_out(situation)
        self.advance_to(situation, 11)

        rin.wake()

        assert not rin.is_unconscious
        assert rin.track.is_unconscious  # the damage that felled them is untouched
        assert track.current(Chars.DEX) == 0
        assert not rin.recovery_check_due(situation.round_number)

    def test_an_animal_gets_no_end_check(self, situation):
        """The rule is a Traveller\'s END check; Hits do not offer one."""
        raiders = situation.add_party('Raiders')
        beast = situation.add_actor(Actor(name='Beast', party=raiders, track=HitsTrack(hits=20), initiative=2))
        situation.new_round()
        situation.attack(None, beast, lethal=19)
        assert beast.is_unconscious

        self.advance_to(situation, 30)

        assert not beast.recovery_check_due(situation.round_number)

    def test_a_new_fight_starts_the_clock_for_someone_already_out(self, situation):
        """The wound crosses the boundary; the minute it is counted in does not."""
        rin, _track = self.knocked_out(situation)
        self.advance_to(situation, 11)
        situation.end()

        next_fight = Situation(name='Corridor', roster=situation.roster)
        next_fight.include(rin)
        next_fight.new_round()

        assert rin.is_unconscious
        assert not rin.recovery_check_due(next_fight.round_number)
        self.advance_to(next_fight, 11)
        assert rin.recovery_check_due(next_fight.round_number)
