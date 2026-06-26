"""Tests for homeworld change events, pending inputs, and triggers."""

import pytest

from ceres.character.domain.career import CITIZEN, DRIFTER
from ceres.character.domain.career.career_events import (
    CareerEntryHandler,
    LifeEventHandler,
    MishapHandler,
    SkillChoiceHandler,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.homeworld.homeworld_events import (
    HomeworldChangedHandler,
    HomeworldChangeKeptHandler,
    HomeworldChangeOfferedHandler,
    HomeworldChangeRequiredHandler,
    PendingHomeworldChangeOffered,
    PendingHomeworldChangeRequired,
)
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, LifeScience, Streetwise, WorkerProfession
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD, MOCK_WORLD_2


def _projection() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )


def _started() -> Event:
    return Event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'))


def _ucp_no_edu(started: Event) -> Event:
    return Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='786000'))


def _ucp(started: Event) -> Event:
    return Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='7869A5'))


def _bg_skills(ucp: Event) -> Event:
    return Event(
        fulfills=(ucp.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )


# ── HomeworldChangeRequiredEvent ──────────────────────────────────────────────


class TestHomeworldChangeRequiredEvent:
    def _events_with_required(self) -> list:
        started = _started()
        ucp = _ucp_no_edu(started)
        required = Event(
            handler=HomeworldChangeRequiredHandler(reason='You must leave your world.', source_kind='life_event_move')
        )
        return [started, ucp, required]

    def test_apply_adds_blocking_pending(self):
        events = self._events_with_required()
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired)), None)
        assert pending is not None
        assert pending.blocking is True

    def test_apply_does_not_mutate_homeworld(self):
        events = self._events_with_required()
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD

    def test_apply_does_not_mutate_birthworld(self):
        events = self._events_with_required()
        projection = replay(1, events)

        assert projection.summary.birthworld == MOCK_WORLD

    def test_pending_carries_reason(self):
        events = self._events_with_required()
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert 'must leave' in pending.reason

    def test_pending_carries_source_kind(self):
        events = self._events_with_required()
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert pending.source_kind == 'life_event_move'

    def test_pending_id_derived_from_event_id(self):
        events = self._events_with_required()
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert pending.id == f'{events[-1].id}.0'

    def test_target_constraints_can_be_set(self):
        started = _started()
        ucp = _ucp_no_edu(started)
        events = [
            started,
            ucp,
            Event(
                handler=HomeworldChangeRequiredHandler(
                    reason='Scout relocation.',
                    source_kind='career_entry',
                    source_career='Scout',
                    target_constraints='world_with_scout_base',
                ),
            ),
        ]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert pending.target_constraints == 'world_with_scout_base'


# ── HomeworldChangeOfferedEvent ───────────────────────────────────────────────


class TestHomeworldChangeOfferedEvent:
    def _events_with_offered(self) -> list:
        started = _started()
        ucp = _ucp_no_edu(started)
        offered = Event(
            handler=HomeworldChangeOfferedHandler(
                reason='You may relocate to a Merchant hub.', source_kind='career_term_end'
            ),
        )
        return [started, ucp, offered]

    def test_apply_adds_non_blocking_pending(self):
        projection = replay(1, self._events_with_offered())

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeOffered)), None)
        assert pending is not None
        assert pending.blocking is False

    def test_apply_does_not_mutate_homeworld(self):
        projection = replay(1, self._events_with_offered())

        assert projection.summary.homeworld == MOCK_WORLD

    def test_non_blocking_does_not_prevent_progression(self):
        projection = replay(1, self._events_with_offered())

        assert projection.has_blocking_pending() is False


# ── HomeworldChangedEvent ─────────────────────────────────────────────────────


class TestHomeworldChangedEvent:
    def _events_required_then_changed(self) -> list:
        started = _started()
        ucp = _ucp_no_edu(started)
        required = Event(
            handler=HomeworldChangeRequiredHandler(reason='You move to another world.', source_kind='life_event_move')
        )
        changed = Event(fulfills=(required.id, 0), handler=HomeworldChangedHandler(new_homeworld=MOCK_WORLD_2))
        return [started, ucp, required, changed]

    def test_apply_updates_homeworld(self):
        projection = replay(1, self._events_required_then_changed())

        assert projection.summary.homeworld == MOCK_WORLD_2

    def test_apply_does_not_change_birthworld(self):
        projection = replay(1, self._events_required_then_changed())

        assert projection.summary.birthworld == MOCK_WORLD

    def test_apply_removes_required_pending(self):
        projection = replay(1, self._events_required_then_changed())

        assert not any(isinstance(p, PendingHomeworldChangeRequired) for p in projection.pending_inputs)

    def test_fulfills_offered_pending_too(self):
        started = _started()
        ucp = _ucp_no_edu(started)
        offered = Event(
            handler=HomeworldChangeOfferedHandler(reason='You may relocate.', source_kind='career_term_end')
        )
        events = [
            started,
            ucp,
            offered,
            Event(fulfills=(offered.id, 0), handler=HomeworldChangedHandler(new_homeworld=MOCK_WORLD_2)),
        ]
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD_2
        assert not any(isinstance(p, PendingHomeworldChangeOffered) for p in projection.pending_inputs)

    def test_birthworld_unchanged_after_multiple_homeworld_changes(self):
        started = _started()
        ucp = _ucp_no_edu(started)
        first_required = Event(
            handler=HomeworldChangeRequiredHandler(reason='First move.', source_kind='life_event_move')
        )
        first_changed = Event(
            fulfills=(first_required.id, 0), handler=HomeworldChangedHandler(new_homeworld=MOCK_WORLD_2)
        )
        second_required = Event(
            handler=HomeworldChangeRequiredHandler(reason='Second move.', source_kind='life_event_move')
        )
        events = [
            started,
            ucp,
            first_required,
            first_changed,
            second_required,
            Event(fulfills=(second_required.id, 0), handler=HomeworldChangedHandler(new_homeworld=MOCK_WORLD)),
        ]
        projection = replay(1, events)

        assert projection.summary.birthworld == MOCK_WORLD
        assert projection.summary.homeworld == MOCK_WORLD


# ── Life Event 9 trigger ──────────────────────────────────────────────────────


def _drifter_at_life_event_9() -> list:
    """Events up to and including Event(handler=LifeEventHandler(roll=9)) for a Drifter/Wanderer.

    UCP '786000' → EDU=0, no background skill pending. Drifter qualifies (END 0).
    """
    started = _started()
    ucp = _ucp_no_edu(started)
    career = Event(
        handler=CareerEntryHandler(career=DRIFTER, assignment=DRIFTER.assignment('Wanderer'), qualification_roll=10)
    )
    survive = Event(fulfills=(career.id, 0), handler=SurviveHandler(roll=10))
    term_event = Event(fulfills=(survive.id, 0), handler=TermEventHandler(roll=7))  # life event
    life_event = Event(fulfills=(term_event.id, 0), handler=LifeEventHandler(roll=9))  # You move to another world.
    return [started, ucp, career, survive, term_event, life_event]


class TestLifeEvent9HomeworldTrigger:
    def test_roll_9_creates_homeworld_change_required_pending(self):
        projection = replay(1, _drifter_at_life_event_9())

        assert any(isinstance(p, PendingHomeworldChangeRequired) for p in projection.pending_inputs)

    def test_roll_9_pending_is_blocking(self):
        projection = replay(1, _drifter_at_life_event_9())

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert pending.blocking is True

    def test_roll_9_pending_source_kind_is_life_event(self):
        projection = replay(1, _drifter_at_life_event_9())

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert pending.source_kind == 'life_event_move'

    def test_roll_9_homeworld_unchanged_until_resolved(self):
        projection = replay(1, _drifter_at_life_event_9())

        assert projection.summary.homeworld == MOCK_WORLD

    def test_roll_9_homeworld_changes_after_HomeworldChangedEvent(self):
        base = _drifter_at_life_event_9()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=HomeworldChangedHandler(new_homeworld=MOCK_WORLD_2)),
        ]
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD_2
        assert projection.summary.birthworld == MOCK_WORLD

    def test_roll_9_advancement_pending_still_created_when_in_career(self):
        from ceres.character.domain.career.career_events import PendingAdvancement

        projection = replay(1, _drifter_at_life_event_9())

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── Citizen mishap 5 trigger ──────────────────────────────────────────────────


def _citizen_worker_to_survive() -> list:
    """Events through Citizen/Worker initial training choices, ready for survival roll.

    Citizen/Worker creates two initial training choices after CareerEvent:
    (3,0) Profession choices and (3,1) Science choices. Both must be resolved
    before PendingSurvive is created (pending_id=(5,0) after SkillChoiceEvent id=5).
    """
    started = _started()
    ucp = _ucp_no_edu(started)
    career = Event(
        handler=CareerEntryHandler(career=CITIZEN, assignment=CITIZEN.assignment('Worker'), qualification_roll=10)
    )
    profession = Event(fulfills=(career.id, 0), handler=SkillChoiceHandler(skill=WorkerProfession()))
    science = Event(fulfills=(career.id, 1), handler=SkillChoiceHandler(skill=LifeScience()))
    return [started, ucp, career, profession, science]


def _citizen_to_mishap5_skill_roll() -> list:
    """Events up to PendingCitizenMishap5SkillRoll for a Citizen/Worker."""
    base = _citizen_worker_to_survive()
    survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=2))  # roll=2 → mishap
    mishap = Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=5))
    return [
        *base,
        survive,
        mishap,
    ]


class TestCitizenMishap5HomeworldTrigger:
    def _events_to_streetwise_roll(self) -> list:
        base = _citizen_worker_to_survive()
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=2))  # roll=2 → mishap
        mishap = Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=5))
        return [
            *base,
            survive,
            mishap,
        ]

    def test_mishap5_success_adds_homeworld_change_required(self):
        base = self._events_to_streetwise_roll()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingHomeworldChangeRequired) for p in projection.pending_inputs)

    def test_mishap5_failure_adds_homeworld_change_required(self):
        base = self._events_to_streetwise_roll()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=5)),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingHomeworldChangeRequired) for p in projection.pending_inputs)

    def test_mishap5_homeworld_unchanged_until_resolved(self):
        base = self._events_to_streetwise_roll()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=5)),
        ]
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD

    def test_mishap5_success_homeworld_changes_after_HomeworldChangedEvent(self):
        base = self._events_to_streetwise_roll()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        hw_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        events.append(
            Event(fulfills=hw_pending.pending_id, handler=HomeworldChangedHandler(new_homeworld=MOCK_WORLD_2))
        )
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD_2
        assert projection.summary.birthworld == MOCK_WORLD


# ── HomeworldChangeKeptHandler ────────────────────────────────────────────────


class TestHomeworldChangeKeptHandler:
    def test_apply_is_a_no_op_that_does_not_raise(self):
        projection = _projection()
        Event(handler=HomeworldChangeKeptHandler()).apply(projection)
        assert projection.summary.homeworld == MOCK_WORLD


# ── PendingHomeworldChangeRequired: event_from_form edge cases ────────────────


class TestPendingHomeworldChangeRequiredEventFromForm:
    def _pending(self) -> PendingHomeworldChangeRequired:
        return PendingHomeworldChangeRequired(
            pending_id='hw_1',
            reason='You must relocate.',
            instruction='You must relocate.',
        )

    def test_raises_when_sector_is_empty(self):
        pending = self._pending()
        with pytest.raises(ValueError, match='Sector and hex code are required'):
            pending.event_from_form({'sector': '', 'hex_code': '0101'})

    def test_raises_when_hex_code_is_empty(self):
        pending = self._pending()
        with pytest.raises(ValueError, match='Sector and hex code are required'):
            pending.event_from_form({'sector': 'Spinward Marches', 'hex_code': ''})

    def test_input_specs_returns_info_text(self):
        from ceres.character.input_specs import InfoText

        pending = self._pending()
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], InfoText)


# ── PendingHomeworldChangeOffered: form handling ──────────────────────────────


class TestPendingHomeworldChangeOfferedFormHandling:
    def _pending(self) -> PendingHomeworldChangeOffered:
        return PendingHomeworldChangeOffered(
            pending_id='hw_offer_1',
            reason='You may relocate.',
            instruction='You may relocate.',
        )

    def test_template_fragment_is_homeworld_change(self):
        assert self._pending().template_fragment == 'homeworld_change'

    def test_event_from_form_keep_returns_kept_handler(self):
        pending = self._pending()
        event = pending.event_from_form({'keep': '1'})
        assert isinstance(event.handler, HomeworldChangeKeptHandler)

    def test_event_from_form_raises_when_sector_is_empty(self):
        pending = self._pending()
        with pytest.raises(ValueError, match='Sector and hex code are required'):
            pending.event_from_form({'keep': '', 'sector': '', 'hex_code': '0101'})

    def test_event_from_form_raises_when_hex_code_is_empty(self):
        pending = self._pending()
        with pytest.raises(ValueError, match='Sector and hex code are required'):
            pending.event_from_form({'keep': '', 'sector': 'Spinward Marches', 'hex_code': ''})

    def test_input_specs_returns_info_text(self):
        from ceres.character.input_specs import InfoText

        pending = self._pending()
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], InfoText)
