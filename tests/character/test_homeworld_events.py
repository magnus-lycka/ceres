"""Tests for homeworld change events, pending inputs, and triggers."""

from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerEvent,
    CharacterStartedEvent,
    HomeworldChangedEvent,
    HomeworldChangeOfferedEvent,
    HomeworldChangeRequiredEvent,
    LifeEventEvent,
    MishapEvent,
    PendingHomeworldChangeOffered,
    PendingHomeworldChangeRequired,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, Streetwise
from ceres.character.sophonts import VILANI
from tests.character.helpers import MOCK_WORLD, MOCK_WORLD_2


def _started(id: int = 1) -> CharacterStartedEvent:
    return CharacterStartedEvent(id=id, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')


def _ucp_no_edu(id: int = 2) -> UcpEvent:
    return UcpEvent(id=id, fulfills=(1, 0), ucp='786000')


def _ucp(id: int = 2) -> UcpEvent:
    return UcpEvent(id=id, fulfills=(1, 0), ucp='7869A5')


def _bg_skills(id: int = 3) -> BackgroundSkillsEvent:
    return BackgroundSkillsEvent(id=id, fulfills=(2, 0), skills=[Admin(), Athletics(), Carouse(), Drive()])


# ── HomeworldChangeRequiredEvent ──────────────────────────────────────────────


class TestHomeworldChangeRequiredEvent:
    def _events_with_required(self) -> tuple[list, int]:
        """Return (events, next_id) with HomeworldChangeRequiredEvent at id=4."""
        events = [
            _started(1),
            _ucp_no_edu(2),
            HomeworldChangeRequiredEvent(
                id=3,
                reason='You must leave your world.',
                source_kind='life_event_move',
            ),
        ]
        return events, 4

    def test_apply_adds_blocking_pending(self):
        events, _ = self._events_with_required()
        projection = replay(1, events)

        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired)), None)
        assert pending is not None
        assert pending.blocking is True

    def test_apply_does_not_mutate_homeworld(self):
        events, _ = self._events_with_required()
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD

    def test_apply_does_not_mutate_birthworld(self):
        events, _ = self._events_with_required()
        projection = replay(1, events)

        assert projection.summary.birthworld == MOCK_WORLD

    def test_pending_carries_reason(self):
        events, _ = self._events_with_required()
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert 'must leave' in pending.reason

    def test_pending_carries_source_kind(self):
        events, _ = self._events_with_required()
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert pending.source_kind == 'life_event_move'

    def test_pending_id_derived_from_event_id(self):
        events, _ = self._events_with_required()
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert pending.id == '3.0'

    def test_target_constraints_can_be_set(self):
        events = [
            _started(1),
            _ucp_no_edu(2),
            HomeworldChangeRequiredEvent(
                id=3,
                reason='Scout relocation.',
                source_kind='career_entry',
                source_career='Scout',
                target_constraints='world_with_scout_base',
            ),
        ]
        projection = replay(1, events)

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        assert pending.target_constraints == 'world_with_scout_base'


# ── HomeworldChangeOfferedEvent ───────────────────────────────────────────────


class TestHomeworldChangeOfferedEvent:
    def _events_with_offered(self) -> list:
        return [
            _started(1),
            _ucp_no_edu(2),
            HomeworldChangeOfferedEvent(
                id=3,
                reason='You may relocate to a Merchant hub.',
                source_kind='career_term_end',
            ),
        ]

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
        return [
            _started(1),
            _ucp_no_edu(2),
            HomeworldChangeRequiredEvent(
                id=3,
                reason='You move to another world.',
                source_kind='life_event_move',
            ),
            HomeworldChangedEvent(id=4, fulfills=(3, 0), new_homeworld=MOCK_WORLD_2),
        ]

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
        events = [
            _started(1),
            _ucp_no_edu(2),
            HomeworldChangeOfferedEvent(
                id=3,
                reason='You may relocate.',
                source_kind='career_term_end',
            ),
            HomeworldChangedEvent(id=4, fulfills=(3, 0), new_homeworld=MOCK_WORLD_2),
        ]
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD_2
        assert not any(isinstance(p, PendingHomeworldChangeOffered) for p in projection.pending_inputs)

    def test_birthworld_unchanged_after_multiple_homeworld_changes(self):
        events = [
            _started(1),
            _ucp_no_edu(2),
            HomeworldChangeRequiredEvent(id=3, reason='First move.', source_kind='life_event_move'),
            HomeworldChangedEvent(id=4, fulfills=(3, 0), new_homeworld=MOCK_WORLD_2),
            HomeworldChangeRequiredEvent(id=5, reason='Second move.', source_kind='life_event_move'),
            HomeworldChangedEvent(id=6, fulfills=(5, 0), new_homeworld=MOCK_WORLD),
        ]
        projection = replay(1, events)

        assert projection.summary.birthworld == MOCK_WORLD
        assert projection.summary.homeworld == MOCK_WORLD


# ── Life Event 9 trigger ──────────────────────────────────────────────────────


def _drifter_at_life_event_9() -> list:
    """Events up to and including LifeEventEvent(roll=9) for a Drifter/Wanderer.

    UCP '786000' → EDU=0, no background skill pending. Drifter qualifies (END 0).
    """
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills=(1, 0), ucp='786000'),
        CareerEvent(id=3, career='Drifter', assignment='Wanderer', qualification_roll=10),
        SurviveEvent(id=4, fulfills=(3, 0), roll=10),
        TermEventEvent(id=5, fulfills=(4, 0), roll=7),  # life event
        LifeEventEvent(id=6, fulfills=(5, 0), roll=9),  # You move to another world.
    ]


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
        events = [
            *_drifter_at_life_event_9(),
            HomeworldChangedEvent(id=7, fulfills=(6, 0), new_homeworld=MOCK_WORLD_2),
        ]
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD_2
        assert projection.summary.birthworld == MOCK_WORLD

    def test_roll_9_advancement_pending_still_created_when_in_career(self):
        from ceres.character.events import PendingAdvancement

        projection = replay(1, _drifter_at_life_event_9())

        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── Citizen mishap 5 trigger ──────────────────────────────────────────────────


def _citizen_to_mishap5_skill_roll() -> list:
    """Events up to PendingCitizenMishap5SkillRoll for a Citizen/Worker."""
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills=(1, 0), ucp='786000'),
        CareerEvent(id=3, career='Citizen', assignment='Worker', qualification_roll=10),
        SurviveEvent(id=4, fulfills=(3, 0), roll=6),  # triggers mishap (survive target=5, roll=6<target→mishap... wait)
        MishapEvent(id=5, fulfills=(4, 0), roll=5),
    ]


class TestCitizenMishap5HomeworldTrigger:
    def _events_to_streetwise_roll(self) -> list:
        return [
            CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
            UcpEvent(id=2, fulfills=(1, 0), ucp='786000'),
            CareerEvent(id=3, career='Citizen', assignment='Worker', qualification_roll=10),
            SurviveEvent(id=4, fulfills=(3, 0), roll=2),  # roll=2 → mishap
            MishapEvent(id=5, fulfills=(4, 0), roll=5),
        ]

    def test_mishap5_success_adds_homeworld_change_required(self):
        events = [
            *self._events_to_streetwise_roll(),
            SkillRollEvent(id=6, fulfills=(5, 0), skill=Streetwise(), modified_roll=9),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingHomeworldChangeRequired) for p in projection.pending_inputs)

    def test_mishap5_failure_adds_homeworld_change_required(self):
        events = [
            *self._events_to_streetwise_roll(),
            SkillRollEvent(id=6, fulfills=(5, 0), skill=Streetwise(), modified_roll=5),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingHomeworldChangeRequired) for p in projection.pending_inputs)

    def test_mishap5_homeworld_unchanged_until_resolved(self):
        events = [
            *self._events_to_streetwise_roll(),
            SkillRollEvent(id=6, fulfills=(5, 0), skill=Streetwise(), modified_roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD

    def test_mishap5_success_homeworld_changes_after_HomeworldChangedEvent(self):

        events = [
            *self._events_to_streetwise_roll(),
            SkillRollEvent(id=6, fulfills=(5, 0), skill=Streetwise(), modified_roll=9),
        ]
        projection = replay(1, events)
        hw_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldChangeRequired))
        events.append(HomeworldChangedEvent(id=7, fulfills=hw_pending.pending_id, new_homeworld=MOCK_WORLD_2))
        projection = replay(1, events)

        assert projection.summary.homeworld == MOCK_WORLD_2
        assert projection.summary.birthworld == MOCK_WORLD
