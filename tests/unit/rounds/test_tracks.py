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

import pytest

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
    )

    assert track.maximum(Chars.STR) == 9
    assert track.current(Chars.STR) == 6
    assert track.current(Chars.DEX) == 4
    assert track.current(Chars.END) == 2
    assert track.stun_points == 3


class TestStunDamage:
    """How long the incapacitation lasts is returned, not stored.

    The rounds belong to the fight that counts them, so the track reports what
    the hit caused and the situation membership remembers when it wears off.
    """

    def test_stun_reduces_end_without_incapacitating_while_end_remains(self):
        track = track_888()

        rounds = track.apply(5, DamageKind.STUN)

        assert track.current(Chars.END) == 3
        assert track.stun_points == 5
        assert rounds == 0

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

        rounds = track.apply(15, DamageKind.STUN)

        assert track.current(Chars.END) == 0
        assert track.stun_points == 4
        assert rounds == 11

    def test_exactly_reducing_end_to_zero_causes_zero_incapacitated_rounds(self):
        track = track_888()

        rounds = track.apply(8, DamageKind.STUN)

        assert track.current(Chars.END) == 0
        assert rounds == 0

    def test_stun_against_exhausted_end_is_all_overflow(self):
        """Every point of a later hit is excess once END is already zero."""
        track = track_888()
        track.apply(11, DamageKind.STUN)

        rounds = track.apply(2, DamageKind.STUN)

        assert track.stun_points == 8
        assert rounds == 2

    def test_an_hour_of_rest_heals_stun_but_not_lethal_damage(self):
        track = track_888()
        track.apply(4, DamageKind.LETHAL)
        track.apply(15, DamageKind.STUN)

        track.clear_stun()

        assert track.current(Chars.END) == 4
        assert track.stun_points == 0


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

        rounds = track.apply(5, DamageKind.STUN)

        assert track.current(Chars.END) == 0
        assert rounds == 3

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

    def test_stun_suppresses_hits_to_half_and_excess_becomes_rounds(self):
        track = HitsTrack(hits=20)

        assert track.apply(10, DamageKind.STUN) == 0
        assert track.current == 10
        assert track.stun_points == 10

        rounds = track.apply(4, DamageKind.STUN)

        assert track.current == 10
        assert track.stun_points == 10
        assert rounds == 4

    def test_stun_capacity_rounds_half_hits_up(self):
        track = HitsTrack(hits=21)

        rounds = track.apply(11, DamageKind.STUN)

        assert track.current == 10
        assert track.stun_points == 11
        assert rounds == 0

    def test_stun_on_an_animal_already_below_half_hits_is_all_overflow(self):
        track = HitsTrack(hits=20)
        track.apply(19, DamageKind.LETHAL)

        rounds = track.apply(4, DamageKind.STUN)

        assert track.current == 1
        assert track.stun_points == 0
        assert rounds == 4
        assert track.is_unconscious

    def test_an_hour_of_rest_clears_the_stun_it_took(self):
        track = HitsTrack(hits=20)
        track.apply(14, DamageKind.STUN)

        track.clear_stun()

        assert track.current == 20
        assert track.stun_points == 0

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

        track.correct_state(maximum=24, current=9, stun_points=0)

        assert track.maximum == 24
        assert track.current == 9
        assert track.stun_points == 0


class TestCharacteristicInjuryHistory:
    """Each hit is stored as what it actually did, so nothing is replayed.

    Which characteristic absorbed how much is decided when the damage lands
    (:259-268), so that is the fact worth keeping: it is what the first-aid
    view reads, and what the referee corrects when a number was wrong.
    """

    def test_a_hit_records_the_round_and_what_it_reduced(self):
        track = track_888()

        track.apply(10, DamageKind.LETHAL, at=3)

        (injury,) = track.injuries
        assert injury.kind is DamageKind.LETHAL
        assert injury.when == 3
        assert injury.reductions == {Chars.END: 8, Chars.DEX: 2}

    def test_the_choice_of_str_or_dex_is_resolved_when_the_damage_lands(self):
        track = track_888(excess_to=Chars.STR)

        track.apply(10, DamageKind.LETHAL, at=1)

        (injury,) = track.injuries
        assert injury.reductions == {Chars.END: 8, Chars.STR: 2}

    def test_every_hit_is_its_own_line_in_order(self):
        track = track_888()

        track.apply(6, DamageKind.LETHAL, at=1)
        track.apply(3, DamageKind.LETHAL, at=4)

        first, second = track.injuries
        assert (first.when, first.reductions) == (1, {Chars.END: 6})
        assert (second.when, second.reductions) == (4, {Chars.END: 2, Chars.DEX: 1})

    def test_a_hit_that_reduces_nothing_is_not_recorded(self):
        track = track_888()
        track.apply(24, DamageKind.LETHAL, at=1)

        track.apply(5, DamageKind.LETHAL, at=2)

        assert len(track.injuries) == 1

    def test_stun_records_only_what_it_suppressed(self):
        """The overflow becomes rounds of incapacitation, not stored damage."""
        track = track_888()

        overflow = track.apply(15, DamageKind.STUN, at=2)

        (injury,) = track.injuries
        assert injury.kind is DamageKind.STUN
        assert overflow == 7
        assert injury.reductions == {Chars.END: 8}

    def test_current_values_are_the_maximum_less_the_recorded_reductions(self):
        track = track_888()

        track.apply(4, DamageKind.LETHAL, at=1)
        track.apply(3, DamageKind.STUN, at=2)

        assert track.current(Chars.END) == 1
        assert track.stun_points == 3

    def test_lethal_damage_erases_the_stun_line_it_displaces(self):
        """Stun must never stand between an actor and death (RIC-012)."""
        track = CharacteristicTrack(strength=4, dexterity=4, endurance=4)
        track.apply(2, DamageKind.STUN, at=1)
        track.apply(10, DamageKind.LETHAL, at=2)

        track.apply(2, DamageKind.LETHAL, at=3)

        assert [injury.kind for injury in track.injuries] == [DamageKind.LETHAL, DamageKind.LETHAL]
        assert track.is_dead

    def test_displacement_takes_the_oldest_stun_first(self):
        """Lethal damage reaches END again once STR and DEX are exhausted."""
        track = CharacteristicTrack(strength=2, dexterity=2, endurance=8)
        track.apply(2, DamageKind.STUN, at=1)
        track.apply(3, DamageKind.STUN, at=2)

        track.apply(10, DamageKind.LETHAL, at=3)

        stun = [injury for injury in track.injuries if injury.kind is DamageKind.STUN]
        assert [(injury.when, injury.reductions) for injury in stun] == [(2, {Chars.END: 2})]
        assert not track.is_dead

    def test_clearing_stun_leaves_the_lethal_lines_alone(self):
        track = track_888()
        track.apply(4, DamageKind.LETHAL, at=1)
        track.apply(15, DamageKind.STUN, at=2)

        track.clear_stun()

        assert [injury.kind for injury in track.injuries] == [DamageKind.LETHAL]
        assert track.current(Chars.END) == 4

    def test_carrying_over_stamps_surviving_injuries_as_earlier(self):
        """A new fight counts from round 1, and old wounds are past first aid."""
        track = track_888()
        track.apply(4, DamageKind.LETHAL, at=3)

        track.carry_over()

        (injury,) = track.injuries
        assert injury.when is None
        assert injury.is_earlier
        assert track.current(Chars.END) == 4

    def test_a_hit_with_no_round_is_already_earlier(self):
        track = track_888()

        track.apply(4, DamageKind.LETHAL)

        (injury,) = track.injuries
        assert injury.is_earlier


class TestHitsInjuryHistory:
    def test_a_hit_records_the_round_and_the_hits_it_cost(self):
        track = HitsTrack(hits=20)

        track.apply(5, DamageKind.LETHAL, at=2)

        (injury,) = track.injuries
        assert (injury.kind, injury.when, injury.reduction) == (DamageKind.LETHAL, 2, 5)

    def test_stun_records_only_the_hits_it_suppressed(self):
        track = HitsTrack(hits=20)

        overflow = track.apply(14, DamageKind.STUN, at=1)

        (injury,) = track.injuries
        assert injury.reduction == 10
        assert overflow == 4

    def test_lethal_damage_erases_the_stun_line_it_displaces(self):
        track = HitsTrack(hits=20)
        track.apply(10, DamageKind.STUN, at=1)

        track.apply(19, DamageKind.LETHAL, at=2)

        assert [injury.kind for injury in track.injuries] == [DamageKind.LETHAL]
        assert track.current == 1

    def test_clearing_stun_leaves_the_lethal_lines_alone(self):
        track = HitsTrack(hits=20)
        track.apply(5, DamageKind.LETHAL, at=1)
        track.apply(14, DamageKind.STUN, at=2)

        track.clear_stun()

        assert [injury.reduction for injury in track.injuries] == [5]
        assert track.current == 15

    def test_carrying_over_stamps_surviving_injuries_as_earlier(self):
        track = HitsTrack(hits=20)
        track.apply(5, DamageKind.LETHAL, at=2)

        track.carry_over()

        (injury,) = track.injuries
        assert injury.is_earlier


class TestInjuriesAreReportedNotMutated:
    def test_the_history_cannot_be_edited_by_its_reader(self):
        track = track_888()
        track.apply(4, DamageKind.LETHAL, at=1)

        with pytest.raises((AttributeError, TypeError)):
            track.injuries[0].when = 7  # ty: ignore[invalid-assignment]
