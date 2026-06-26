"""Unit tests for health_events — injury table, aging, and characteristic choice mechanics."""

import pytest

from ceres.character.domain.career.career_events import SurviveHandler
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.health.health_events import (
    AgingCrisisHandler,
    AgingRollHandler,
    CharacteristicChoiceHandler,
    DoubleInjuryTableHandler,
    InjuryTableHandler,
    PendingAgingChoice,
    PendingAgingChoiceMental,
    PendingAgingCrisis,
    PendingAgingRoll,
    PendingCharacteristicChoice,
    PendingDoubleInjuryRoll,
    PendingInjuryTable,
    PendingNearlyKilled,
    PendingSeverelyInjured,
    check_aging_crisis,
    complete_aging,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


def _projection_with_terms(n: int, **kwargs) -> CharacterProjection:
    """Projection with n fake career terms (muster_out=None so current_career is None)."""
    from ceres.character.domain.career import ARMY
    from ceres.character.domain.career.career_data import CareerTerm

    proj = _projection(**kwargs)
    support = ARMY.assignment('Support')
    for _ in range(n):
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=support, muster_out=None))
    return proj


def _any_event() -> Event:
    return Event(handler=SurviveHandler(roll=5))


class TestCharacteristicChoiceHandler:
    def test_reduces_characteristic_by_amount(self):
        proj = _projection(characteristics={Chars.STR: 7})
        handler = CharacteristicChoiceHandler(characteristic=Chars.STR, amount=2)
        handler.apply(proj, _any_event())
        assert proj.summary.characteristics[Chars.STR] == 5

    def test_does_not_reduce_below_zero(self):
        proj = _projection(characteristics={Chars.STR: 1})
        handler = CharacteristicChoiceHandler(characteristic=Chars.STR, amount=3)
        handler.apply(proj, _any_event())
        assert proj.summary.characteristics[Chars.STR] == 0

    def test_nearly_killed_reduces_other_physical_chars_by_2(self):
        proj = _projection(characteristics={Chars.STR: 8, Chars.DEX: 8, Chars.END: 8})
        pending = PendingNearlyKilled(pending_id=(1, 0), instruction='Nearly killed')
        handler = CharacteristicChoiceHandler(characteristic=Chars.STR, amount=3)
        handler.apply(proj, _any_event(), fulfilled_pending=pending)
        assert proj.summary.characteristics[Chars.STR] == 5  # reduced by amount
        assert proj.summary.characteristics[Chars.DEX] == 6  # reduced by 2
        assert proj.summary.characteristics[Chars.END] == 6  # reduced by 2

    def test_aging_choice_triggers_complete_aging_when_last(self):
        proj = _projection(characteristics={Chars.STR: 7})
        pending = PendingAgingChoice(pending_id=(1, 0), instruction='Choose', options=[Chars.STR, Chars.DEX, Chars.END])
        # replay.py calls fulfill_pending() before apply(), so pending is already removed
        proj.pending_inputs = []
        handler = CharacteristicChoiceHandler(characteristic=Chars.STR)
        handler.apply(proj, _any_event(), fulfilled_pending=pending)
        from ceres.character.domain.career.career_events import PendingReenlist

        assert any(isinstance(p, PendingReenlist) for p in proj.pending_inputs)

    def test_aging_choice_not_last_does_not_complete(self):
        proj = _projection(characteristics={Chars.STR: 7, Chars.DEX: 7})
        pending1 = PendingAgingChoice(
            pending_id=(1, 0), instruction='Choose', options=[Chars.STR, Chars.DEX, Chars.END]
        )
        pending2 = PendingAgingChoice(
            pending_id=(1, 1), instruction='Choose', options=[Chars.STR, Chars.DEX, Chars.END]
        )
        # pending1 already removed (fulfilled), pending2 still outstanding
        proj.pending_inputs = [pending2]
        handler = CharacteristicChoiceHandler(characteristic=Chars.STR)
        handler.apply(proj, _any_event(), fulfilled_pending=pending1)
        from ceres.character.domain.career.career_events import PendingReenlist

        assert not any(isinstance(p, PendingReenlist) for p in proj.pending_inputs)


class TestInjuryTableHandler:
    def test_roll_6_causes_no_pending(self):
        proj = _projection()
        InjuryTableHandler(roll=6).apply(proj, _any_event())
        assert proj.pending_inputs == []

    def test_roll_5_queues_char_choice(self):
        proj = _projection()
        InjuryTableHandler(roll=5).apply(proj, _any_event())
        assert any(isinstance(p, PendingCharacteristicChoice) for p in proj.pending_inputs)

    def test_roll_4_queues_char_choice_amount_2(self):
        proj = _projection()
        InjuryTableHandler(roll=4).apply(proj, _any_event())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingCharacteristicChoice))
        assert pending.amount == 2

    def test_roll_3_queues_char_choice_str_or_dex(self):
        proj = _projection()
        InjuryTableHandler(roll=3).apply(proj, _any_event())
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingCharacteristicChoice))
        assert pending.options == [Chars.STR, Chars.DEX]

    def test_roll_2_queues_severely_injured(self):
        proj = _projection()
        InjuryTableHandler(roll=2).apply(proj, _any_event())
        assert any(isinstance(p, PendingSeverelyInjured) for p in proj.pending_inputs)

    def test_roll_1_queues_nearly_killed(self):
        proj = _projection()
        InjuryTableHandler(roll=1).apply(proj, _any_event())
        assert any(isinstance(p, PendingNearlyKilled) for p in proj.pending_inputs)

    def test_invalid_roll_raises(self):
        proj = _projection()
        with pytest.raises(ReplayError):
            InjuryTableHandler(roll=7).apply(proj, _any_event())


class TestDoubleInjuryTableHandler:
    def test_applies_minimum_of_two_rolls(self):
        proj = _projection()
        DoubleInjuryTableHandler(roll1=5, roll2=3).apply(proj, _any_event())
        # min(5,3)=3 → STR or DEX choice
        pending = next((p for p in proj.pending_inputs if isinstance(p, PendingCharacteristicChoice)), None)
        assert pending is not None and pending.options == [Chars.STR, Chars.DEX]

    def test_invalid_roll_raises(self):
        proj = _projection()
        with pytest.raises(ReplayError):
            DoubleInjuryTableHandler(roll1=0, roll2=3).apply(proj, _any_event())


class TestAgingRollHandler:
    def test_roll_above_terms_completes_aging(self):
        proj = _projection()
        # 0 terms, roll=5 → effective=5 ≥ 1 → complete_aging → PendingReenlist
        from ceres.character.domain.career.career_events import PendingReenlist

        AgingRollHandler(roll=5).apply(proj, _any_event())
        assert any(isinstance(p, PendingReenlist) for p in proj.pending_inputs)

    def test_effective_zero_queues_one_aging_choice(self):
        # roll=5, terms=5 → effective=0 → 1 aging choice
        proj = _projection_with_terms(5)
        AgingRollHandler(roll=5).apply(proj, _any_event())
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(choices) == 1

    def test_effective_minus_one_queues_two_aging_choices(self):
        # roll=5, terms=6 → effective=-1 → 2 aging choices
        proj = _projection_with_terms(6)
        AgingRollHandler(roll=5).apply(proj, _any_event())
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(choices) == 2

    def test_effective_minus_two_reduces_all_physical_by_1(self):
        # roll=5, terms=7 → effective=-2 → all physical -1
        proj = _projection_with_terms(7, characteristics={Chars.STR: 8, Chars.DEX: 8, Chars.END: 8})
        AgingRollHandler(roll=5).apply(proj, _any_event())
        assert proj.summary.characteristics[Chars.STR] == 7
        assert proj.summary.characteristics[Chars.DEX] == 7
        assert proj.summary.characteristics[Chars.END] == 7

    def test_effective_minus_three_queues_three_choices(self):
        # roll=5, terms=8 → effective=-3 → 3 aging choices
        proj = _projection_with_terms(8)
        AgingRollHandler(roll=5).apply(proj, _any_event())
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(choices) == 3

    def test_effective_minus_four_queues_three_choices(self):
        # roll=5, terms=9 → effective=-4 → 3 aging choices (2×reduce-by-2, 1×reduce-by-1)
        proj = _projection_with_terms(9)
        AgingRollHandler(roll=5).apply(proj, _any_event())
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(choices) == 3

    def test_effective_minus_five_reduces_all_physical_by_2(self):
        # roll=5, terms=10 → effective=-5 → all physical -2
        proj = _projection_with_terms(10, characteristics={Chars.STR: 8, Chars.DEX: 8, Chars.END: 8})
        AgingRollHandler(roll=5).apply(proj, _any_event())
        assert proj.summary.characteristics[Chars.STR] == 6
        assert proj.summary.characteristics[Chars.DEX] == 6
        assert proj.summary.characteristics[Chars.END] == 6

    def test_effective_minus_six_or_less_queues_mental_choice(self):
        # roll=5, terms=11 → effective=-6 → mental aging choice
        proj = _projection_with_terms(11, characteristics={Chars.STR: 8, Chars.DEX: 8, Chars.END: 8})
        AgingRollHandler(roll=5).apply(proj, _any_event())
        assert any(isinstance(p, PendingAgingChoiceMental) for p in proj.pending_inputs)

    def test_invalid_roll_raises(self):
        proj = _projection()
        with pytest.raises(ReplayError):
            AgingRollHandler(roll=13).apply(proj, _any_event())

    def test_aging_crisis_interrupts_normal_flow(self):
        # All physical characteristics at 0 → effective=-2 reduction triggers aging crisis
        proj = _projection_with_terms(7, characteristics={Chars.STR: 0, Chars.DEX: 0, Chars.END: 0})
        AgingRollHandler(roll=5).apply(proj, _any_event())
        assert any(isinstance(p, PendingAgingCrisis) for p in proj.pending_inputs)


class TestAgingCrisisHandler:
    def test_paid_sets_zeroed_characteristics_to_1(self):
        proj = _projection(characteristics={Chars.STR: 0, Chars.DEX: 5, Chars.END: 0})
        AgingCrisisHandler(paid=True, medical_roll=0).apply(proj, _any_event())
        assert proj.summary.characteristics[Chars.STR] == 1
        assert proj.summary.characteristics[Chars.DEX] == 5
        assert proj.summary.characteristics[Chars.END] == 1

    def test_not_paid_marks_character_dead(self):
        proj = _projection()
        AgingCrisisHandler(paid=False, medical_roll=0).apply(proj, _any_event())
        assert proj.summary.dead is True


class TestCheckAgingCrisis:
    def test_returns_true_when_any_char_is_zero(self):
        proj = _projection(characteristics={Chars.STR: 0, Chars.DEX: 5, Chars.END: 5})
        result = check_aging_crisis(proj, source_event_id=1)
        assert result is True

    def test_queues_aging_crisis_when_triggered(self):
        proj = _projection(characteristics={Chars.STR: 0, Chars.DEX: 5, Chars.END: 5})
        check_aging_crisis(proj, source_event_id=1)
        assert any(isinstance(p, PendingAgingCrisis) for p in proj.pending_inputs)

    def test_returns_false_when_all_chars_positive(self):
        proj = _projection(characteristics={Chars.STR: 5, Chars.DEX: 5, Chars.END: 5})
        result = check_aging_crisis(proj, source_event_id=1)
        assert result is False

    def test_clears_existing_aging_choices_on_crisis(self):
        proj = _projection(characteristics={Chars.STR: 0})
        proj.pending_inputs = [
            PendingAgingChoice(pending_id=(1, 0), instruction='Choose', options=[Chars.STR, Chars.DEX, Chars.END])
        ]
        check_aging_crisis(proj, source_event_id=2)
        assert not any(isinstance(p, PendingAgingChoice) for p in proj.pending_inputs)


class TestCompleteAging:
    def test_queues_reenlist_when_no_current_career(self):
        from ceres.character.domain.career.career_events import PendingReenlist

        proj = _projection()
        complete_aging(proj, source_event_id=1)
        assert any(isinstance(p, PendingReenlist) for p in proj.pending_inputs)


class TestPendingCharacteristicChoice:
    def test_event_from_form_parses_characteristic(self):
        pending = PendingCharacteristicChoice(pending_id=(1, 0), instruction='Choose', options=[Chars.STR, Chars.DEX])
        event = pending.event_from_form({'characteristic': 'STR'})
        assert isinstance(event.handler, CharacteristicChoiceHandler)
        assert event.handler.characteristic == Chars.STR

    def test_input_specs_returns_select(self):
        specs = PendingCharacteristicChoice(
            pending_id=(1, 0), instruction='Choose', options=[Chars.STR, Chars.DEX]
        ).input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'characteristic' for s in specs)


class TestPendingSeverelyInjured:
    def test_event_from_form_parses_char_and_roll(self):
        pending = PendingSeverelyInjured(pending_id=(1, 0), instruction='Severely injured')
        event = pending.event_from_form({'characteristic': 'DEX', 'roll': '3'})
        assert isinstance(event.handler, CharacteristicChoiceHandler)
        assert event.handler.characteristic == Chars.DEX
        assert event.handler.amount == 3

    def test_input_specs_returns_select_and_roll(self):
        specs = PendingSeverelyInjured(pending_id=(1, 0), instruction='Severely injured').input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'characteristic' for s in specs)
        assert any(isinstance(s, NumberEntry) and s.name == 'roll' for s in specs)


class TestPendingNearlyKilled:
    def test_event_from_form_parses_char_and_roll(self):
        pending = PendingNearlyKilled(pending_id=(1, 0), instruction='Nearly killed')
        event = pending.event_from_form({'characteristic': 'END', 'roll': '4'})
        assert isinstance(event.handler, CharacteristicChoiceHandler)
        assert event.handler.characteristic == Chars.END
        assert event.handler.amount == 4

    def test_input_specs_returns_select_and_roll(self):
        specs = PendingNearlyKilled(pending_id=(1, 0), instruction='Nearly killed').input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'characteristic' for s in specs)
        assert any(isinstance(s, NumberEntry) and s.name == 'roll' for s in specs)


class TestPendingInjuryTable:
    def test_event_from_form_parses_roll(self):
        pending = PendingInjuryTable(pending_id=(1, 0), instruction='Roll injury table')
        event = pending.event_from_form({'roll': '4'})
        assert isinstance(event.handler, InjuryTableHandler)
        assert event.handler.roll == 4

    def test_input_specs_returns_roll_entry(self):
        specs = PendingInjuryTable(pending_id=(1, 0), instruction='Roll injury table').input_specs(_projection())
        assert any(isinstance(s, NumberEntry) and s.name == 'roll' for s in specs)


class TestPendingDoubleInjuryRoll:
    def test_event_from_form_parses_two_rolls(self):
        pending = PendingDoubleInjuryRoll(pending_id=(1, 0), instruction='Roll twice')
        event = pending.event_from_form({'roll1': '5', 'roll2': '3'})
        assert isinstance(event.handler, DoubleInjuryTableHandler)
        assert event.handler.roll1 == 5
        assert event.handler.roll2 == 3

    def test_input_specs_returns_two_rolls(self):
        specs = PendingDoubleInjuryRoll(pending_id=(1, 0), instruction='Roll twice').input_specs(_projection())
        assert any(isinstance(s, NumberEntry) and s.name == 'roll1' for s in specs)
        assert any(isinstance(s, NumberEntry) and s.name == 'roll2' for s in specs)


class TestPendingAgingRoll:
    def test_event_from_form_parses_roll(self):
        pending = PendingAgingRoll(pending_id=(1, 0), instruction='Aging roll 2D')
        event = pending.event_from_form({'roll': '8'})
        assert isinstance(event.handler, AgingRollHandler)
        assert event.handler.roll == 8

    def test_input_specs_returns_roll_entry(self):
        specs = PendingAgingRoll(pending_id=(1, 0), instruction='Aging roll 2D').input_specs(_projection())
        assert any(isinstance(s, NumberEntry) and s.name == 'roll' for s in specs)


class TestPendingAgingChoice:
    def test_event_from_form_parses_characteristic(self):
        pending = PendingAgingChoice(pending_id=(1, 0), instruction='Choose', options=[Chars.STR, Chars.DEX, Chars.END])
        event = pending.event_from_form({'characteristic': 'DEX'})
        assert isinstance(event.handler, CharacteristicChoiceHandler)
        assert event.handler.characteristic == Chars.DEX

    def test_input_specs_returns_select(self):
        specs = PendingAgingChoice(
            pending_id=(1, 0), instruction='Choose', options=[Chars.STR, Chars.DEX, Chars.END]
        ).input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'characteristic' for s in specs)


class TestPendingAgingChoiceMental:
    def test_event_from_form_parses_characteristic(self):
        pending = PendingAgingChoiceMental(
            pending_id=(1, 0), instruction='Choose mental', options=[Chars.INT, Chars.SOC]
        )
        event = pending.event_from_form({'characteristic': 'INT'})
        assert isinstance(event.handler, CharacteristicChoiceHandler)
        assert event.handler.characteristic == Chars.INT

    def test_input_specs_returns_select(self):
        specs = PendingAgingChoiceMental(
            pending_id=(1, 0), instruction='Choose mental', options=[Chars.INT, Chars.SOC]
        ).input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'characteristic' for s in specs)


class TestPendingAgingCrisis:
    def test_event_from_form_paid_true(self):
        pending = PendingAgingCrisis(pending_id=(1, 0), instruction='Aging crisis')
        event = pending.event_from_form({'paid': 'true', 'medical_roll': '4'})
        assert isinstance(event.handler, AgingCrisisHandler)
        assert event.handler.paid is True
        assert event.handler.medical_roll == 4

    def test_event_from_form_paid_false(self):
        pending = PendingAgingCrisis(pending_id=(1, 0), instruction='Aging crisis')
        event = pending.event_from_form({'paid': 'false'})
        assert isinstance(event.handler, AgingCrisisHandler)
        assert event.handler.paid is False

    def test_input_specs_returns_select_and_roll(self):
        specs = PendingAgingCrisis(pending_id=(1, 0), instruction='Aging crisis').input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'paid' for s in specs)
        assert any(isinstance(s, NumberEntry) and s.name == 'medical_roll' for s in specs)
