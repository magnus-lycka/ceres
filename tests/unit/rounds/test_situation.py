"""Round flow: initiative steps and the green/grey turn state machine.

Derived from refs/core/03_combat.md:

- :30, 36  initiative is the Effect of a DEX or INT check, individually or one
           check for all the forces the referee controls
- :62      actors act in initiative order, ties broken by DEX, then simultaneous
- :32      an actor may freely delay their action until later in the turn
- :81      a round ends once everyone has had a chance to act
"""

import pytest

from ceres.rounds.domain.actor import Actor, TurnState
from ceres.rounds.domain.situation import Situation
from ceres.rounds.domain.tracks import CharacteristicTrack, HitsTrack


def character(name: str, *, dexterity: int = 8) -> CharacteristicTrack:
    return CharacteristicTrack(strength=8, dexterity=dexterity, endurance=8)


@pytest.fixture
def situation() -> Situation:
    return Situation(name='Cargo bay')


class TestRoster:
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

        situation.act(fast)

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
        situation.act(middle)

        situation.act(fast)

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
        situation.act(fast)

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
    def test_a_ready_actor_may_act(self, situation):
        crew = situation.add_party('Crew')
        rin = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=5))
        situation.new_round()

        assert rin.can_act

    def test_an_unconscious_actor_may_not_act(self, situation):
        from ceres.rounds.domain.damage import DamageKind

        crew = situation.add_party('Crew')
        rin = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=5))
        situation.new_round()

        rin.track.apply(20, DamageKind.LETHAL)

        assert not rin.can_act

    def test_a_stunned_actor_may_not_act(self, situation):
        from ceres.rounds.domain.damage import DamageKind

        crew = situation.add_party('Crew')
        rin = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=5))
        situation.new_round()

        rin.track.apply(12, DamageKind.STUN)

        assert not rin.can_act

    def test_stun_countdown_runs_down_with_each_new_round(self, situation):
        from ceres.rounds.domain.damage import DamageKind

        crew = situation.add_party('Crew')
        rin = situation.add_actor(Actor(name='Rin', party=crew, track=character('Rin'), initiative=5))
        situation.new_round()
        rin.track.apply(10, DamageKind.STUN)
        assert rin.track.incapacitated_rounds == 2

        situation.new_round()
        situation.new_round()

        assert rin.track.incapacitated_rounds == 0
        assert rin.can_act
