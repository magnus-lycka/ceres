"""Damage track rules.

Derived from refs/core/03_combat.md:

- :259-268  lethal damage: END first, excess to STR or DEX (target's choice),
            unconscious when STR or DEX hits 0, dead when all three are 0
- :366      Stun trait: deducted from END only, incapacitated for the number of
            rounds by which the damage exceeded END, healed by an hour of rest
- :604      animal Hits: dead at 0, unconscious at 10%, stun at half, cumulative
- :652-660  driven off at half Hits, body destroyed at -(starting Hits)

and from docs/RULE_INTERPRETATIONS.md on stun sharing the END score.
"""

from ceres.character.domain.characteristics import Chars
from ceres.rounds.domain.damage import DamageKind
from ceres.rounds.domain.tracks import CharacteristicTrack, HitsTrack


def track_888(excess_to: Chars = Chars.DEX) -> CharacteristicTrack:
    return CharacteristicTrack(strength=8, dexterity=8, endurance=8, excess_to=excess_to)


class TestLethalDamage:
    def test_damage_is_applied_to_end_first(self):
        track = track_888()

        track.apply(5, DamageKind.LETHAL)

        assert track.current(Chars.END) == 3
        assert track.current(Chars.STR) == 8
        assert track.current(Chars.DEX) == 8
        assert not track.is_unconscious
        assert not track.is_dead

    def test_zero_end_alone_does_not_cause_unconsciousness(self):
        track = track_888()

        track.apply(8, DamageKind.LETHAL)

        assert track.current(Chars.END) == 0
        assert not track.is_unconscious

    def test_excess_damage_goes_to_the_chosen_characteristic(self):
        track = track_888(excess_to=Chars.DEX)

        track.apply(10, DamageKind.LETHAL)

        assert track.current(Chars.END) == 0
        assert track.current(Chars.DEX) == 6
        assert track.current(Chars.STR) == 8

    def test_excess_can_be_taken_from_strength_instead(self):
        track = track_888(excess_to=Chars.STR)

        track.apply(10, DamageKind.LETHAL)

        assert track.current(Chars.STR) == 6
        assert track.current(Chars.DEX) == 8

    def test_unconscious_when_the_second_characteristic_reaches_zero(self):
        track = track_888(excess_to=Chars.DEX)

        track.apply(16, DamageKind.LETHAL)

        assert track.current(Chars.END) == 0
        assert track.current(Chars.DEX) == 0
        assert track.current(Chars.STR) == 8
        assert track.is_unconscious
        assert not track.is_dead

    def test_further_damage_falls_through_to_the_remaining_characteristic(self):
        track = track_888(excess_to=Chars.DEX)

        track.apply(20, DamageKind.LETHAL)

        assert track.current(Chars.DEX) == 0
        assert track.current(Chars.STR) == 4
        assert track.is_unconscious
        assert not track.is_dead

    def test_dead_when_all_three_physical_characteristics_are_zero(self):
        track = track_888()

        track.apply(24, DamageKind.LETHAL)

        assert track.current(Chars.STR) == 0
        assert track.current(Chars.DEX) == 0
        assert track.current(Chars.END) == 0
        assert track.is_dead

    def test_damage_beyond_death_does_not_go_negative(self):
        track = track_888()

        track.apply(99, DamageKind.LETHAL)

        assert track.current(Chars.STR) == 0
        assert track.is_dead


class TestCharacteristicDms:
    """Impaired DMs are recalculated from current values (03_combat.md:268)."""

    def test_dm_follows_the_current_value(self):
        track = track_888()

        track.apply(3, DamageKind.LETHAL)

        assert track.current(Chars.END) == 5
        assert track.dm(Chars.END) == -1

    def test_dm_at_zero_is_minus_three(self):
        track = CharacteristicTrack(strength=6, dexterity=6, endurance=6)

        track.apply(6, DamageKind.LETHAL)

        assert track.dm(Chars.END) == -3

    def test_undamaged_characteristics_keep_their_own_dm(self):
        track = CharacteristicTrack(strength=9, dexterity=9, endurance=9)

        assert track.dm(Chars.STR) == 1
        assert track.maximum(Chars.STR) == 9


def test_character_track_can_be_corrected_from_its_visible_values():
    track = track_888()

    track.correct_state(
        maximum={Chars.STR: 9, Chars.DEX: 8, Chars.END: 7},
        current={Chars.STR: 6, Chars.DEX: 4, Chars.END: 2},
        stun_points=3,
        incapacitated_rounds=5,
    )

    assert track.maximum(Chars.STR) == 9
    assert track.current(Chars.STR) == 6
    assert track.current(Chars.DEX) == 4
    assert track.current(Chars.END) == 2
    assert track.stun_points == 3
    assert track.incapacitated_rounds == 5


class TestStunDamage:
    def test_stun_reduces_end_without_incapacitating_while_end_remains(self):
        track = track_888()

        track.apply(5, DamageKind.STUN)

        assert track.current(Chars.END) == 3
        assert track.stun_points == 5
        assert track.incapacitated_rounds == 0

    def test_stun_never_spills_into_str_or_dex_and_cannot_kill(self):
        track = track_888()

        track.apply(20, DamageKind.STUN)

        assert track.current(Chars.END) == 0
        assert track.current(Chars.STR) == 8
        assert track.current(Chars.DEX) == 8
        assert track.stun_points == 8
        assert not track.is_dead

    def test_incapacitated_for_the_rounds_by_which_damage_exceeded_end(self):
        """The referee's worked example: 888, 4 lethal, then 15 stun."""
        track = track_888()

        track.apply(4, DamageKind.LETHAL)
        track.apply(15, DamageKind.STUN)

        assert track.current(Chars.END) == 0
        assert track.stun_points == 4
        assert track.incapacitated_rounds == 11

    def test_exactly_reducing_end_to_zero_causes_zero_incapacitated_rounds(self):
        track = track_888()

        track.apply(8, DamageKind.STUN)

        assert track.current(Chars.END) == 0
        assert track.incapacitated_rounds == 0
        assert not track.is_incapacitated

    def test_a_later_stun_extends_but_does_not_stack_the_countdown(self):
        track = track_888()

        track.apply(14, DamageKind.STUN)
        assert track.incapacitated_rounds == 6
        track.apply(3, DamageKind.STUN)

        assert track.incapacitated_rounds == 6

    def test_countdown_expires_as_rounds_pass(self):
        track = track_888()
        track.apply(11, DamageKind.STUN)
        assert track.incapacitated_rounds == 3

        for _ in range(3):
            track.round_passed()

        assert track.incapacitated_rounds == 0
        assert track.current(Chars.END) == 0

    def test_new_stun_after_countdown_expires_incapacitates_from_zero_end(self):
        track = track_888()
        track.apply(11, DamageKind.STUN)
        for _ in range(3):
            track.round_passed()

        track.apply(2, DamageKind.STUN)

        assert track.stun_points == 8
        assert track.incapacitated_rounds == 2
        assert track.is_incapacitated

    def test_an_hour_of_rest_heals_stun_but_not_lethal_damage(self):
        track = track_888()
        track.apply(4, DamageKind.LETHAL)
        track.apply(15, DamageKind.STUN)

        track.rest_one_hour()

        assert track.current(Chars.END) == 4
        assert track.stun_points == 0
        assert track.incapacitated_rounds == 0


class TestStunAndLethalShareOneEndScore:
    """See docs/RULE_INTERPRETATIONS.md: one END score, two buckets for healing."""

    def test_prior_stun_makes_lethal_unconsciousness_come_sooner(self):
        """END 7 with 5 stun taken needs 9 more lethal points, not 14."""
        track = CharacteristicTrack(strength=7, dexterity=7, endurance=7, excess_to=Chars.DEX)
        track.apply(5, DamageKind.STUN)

        track.apply(8, DamageKind.LETHAL)
        assert not track.is_unconscious
        track.apply(1, DamageKind.LETHAL)

        assert track.is_unconscious

    def test_prior_lethal_damage_makes_a_target_easier_to_stun(self):
        """END 6 with 4 lethal taken is stunned by 5 further stun points."""
        track = CharacteristicTrack(strength=6, dexterity=6, endurance=6)
        track.apply(4, DamageKind.LETHAL)
        assert track.current(Chars.END) == 2

        track.apply(5, DamageKind.STUN)

        assert track.current(Chars.END) == 0
        assert track.incapacitated_rounds == 3

    def test_stun_cannot_complete_a_kill(self):
        """All three at zero is only death when the END loss is lethal."""
        track = CharacteristicTrack(strength=4, dexterity=4, endurance=4, excess_to=Chars.DEX)
        track.apply(2, DamageKind.STUN)

        track.apply(10, DamageKind.LETHAL)

        assert track.current(Chars.STR) == 0
        assert track.current(Chars.DEX) == 0
        assert track.current(Chars.END) == 0
        assert track.is_unconscious
        assert not track.is_dead

    def test_further_lethal_damage_claims_the_end_that_stun_was_occupying(self):
        """Everything reads zero, so the last lethal points displace the stun."""
        track = CharacteristicTrack(strength=4, dexterity=4, endurance=4, excess_to=Chars.DEX)
        track.apply(2, DamageKind.STUN)
        track.apply(10, DamageKind.LETHAL)

        track.apply(2, DamageKind.LETHAL)

        assert track.stun_points == 0
        assert track.is_dead

    def test_stun_does_not_change_how_much_lethal_damage_it_takes_to_kill(self):
        """Stun moves unconsciousness earlier; it must not move death at all."""
        stunned = CharacteristicTrack(strength=4, dexterity=4, endurance=4)
        stunned.apply(2, DamageKind.STUN)
        unstunned = CharacteristicTrack(strength=4, dexterity=4, endurance=4)

        stunned.apply(11, DamageKind.LETHAL)
        unstunned.apply(11, DamageKind.LETHAL)

        assert not stunned.is_dead
        assert not unstunned.is_dead

        stunned.apply(1, DamageKind.LETHAL)
        unstunned.apply(1, DamageKind.LETHAL)

        assert stunned.is_dead
        assert unstunned.is_dead


class TestHitsTrack:
    def test_damage_reduces_hits(self):
        track = HitsTrack(hits=20)

        track.apply(5, DamageKind.LETHAL)

        assert track.current == 15
        assert not track.is_dead

    def test_dead_at_zero_hits(self):
        track = HitsTrack(hits=20)

        track.apply(20, DamageKind.LETHAL)

        assert track.current == 0
        assert track.is_dead

    def test_unconscious_at_a_tenth_of_starting_hits(self):
        track = HitsTrack(hits=20)

        track.apply(18, DamageKind.LETHAL)

        assert track.current == 2
        assert track.is_unconscious
        assert not track.is_dead

    def test_may_be_driven_off_at_half_hits(self):
        track = HitsTrack(hits=20)

        track.apply(10, DamageKind.LETHAL)

        assert track.may_be_driven_off
        assert not track.is_unconscious

    def test_body_destroyed_at_negative_starting_hits(self):
        track = HitsTrack(hits=20)

        track.apply(40, DamageKind.LETHAL)

        assert track.is_dead
        assert track.is_destroyed

    def test_stun_suppresses_hits_to_half_and_excess_sets_the_countdown(self):
        track = HitsTrack(hits=20)

        track.apply(10, DamageKind.STUN)
        assert track.current == 10
        assert track.stun_points == 10
        assert track.incapacitated_rounds == 0
        assert not track.is_incapacitated
        track.apply(4, DamageKind.STUN)

        assert track.current == 10
        assert track.stun_points == 10
        assert track.incapacitated_rounds == 4
        assert track.is_incapacitated

    def test_stun_capacity_rounds_half_hits_up(self):
        track = HitsTrack(hits=21)

        track.apply(11, DamageKind.STUN)

        assert track.current == 10
        assert track.stun_points == 11
        assert track.incapacitated_rounds == 0

    def test_new_stun_after_the_countdown_expires_incapacitates_again(self):
        track = HitsTrack(hits=20)
        track.apply(12, DamageKind.STUN)
        track.round_passed()
        track.round_passed()

        track.apply(3, DamageKind.STUN)

        assert track.current == 10
        assert track.stun_points == 10
        assert track.incapacitated_rounds == 3
        assert track.is_incapacitated

    def test_stun_on_an_animal_already_below_half_hits_is_all_overflow(self):
        track = HitsTrack(hits=20)
        track.apply(19, DamageKind.LETHAL)

        track.apply(4, DamageKind.STUN)

        assert track.current == 1
        assert track.stun_points == 0
        assert track.incapacitated_rounds == 4
        assert track.is_unconscious
        assert track.is_incapacitated

    def test_an_hour_of_rest_clears_stun_points_and_countdown(self):
        track = HitsTrack(hits=20)
        track.apply(14, DamageKind.STUN)

        track.rest_one_hour()

        assert track.current == 20
        assert track.stun_points == 0
        assert track.incapacitated_rounds == 0
        assert not track.is_incapacitated

    def test_lethal_damage_displaces_stun_and_stun_cannot_cause_death(self):
        track = HitsTrack(hits=20)
        track.apply(10, DamageKind.STUN)

        track.apply(19, DamageKind.LETHAL)

        assert track.current == 1
        assert track.stun_points == 0
        assert not track.is_dead

        track.apply(1, DamageKind.LETHAL)

        assert track.current == 0
        assert track.is_dead

    def test_track_can_be_corrected_from_its_visible_values(self):
        track = HitsTrack(hits=20)

        track.correct_state(maximum=24, current=9, stun_points=0, incapacitated_rounds=3)

        assert track.maximum == 24
        assert track.current == 9
        assert track.stun_points == 0
        assert track.incapacitated_rounds == 3
