from random import Random

import pytest

from ceres.character.events import (
    BackgroundSkillsEvent,
    CharacterStartedEvent,
    UcpEvent,
)
from ceres.character.projection import (
    PendingBackgroundSkills,
    PendingCareerChoice,
    PendingUcp,
)
from ceres.character.replay import BACKGROUND_SKILLS, ReplayError, replay
from ceres.character.skills import Admin, Advocate, Athletics, Carouse, Drive, skill_list
from ceres.character.sophonts import VILANI, Sophont
from ceres.character.store import SqliteCharacterBackend
from ceres.character.web.bulk import CohortParams, generate_npc
from tests.character.helpers import MOCK_WORLD


def _started(id: int = 1, sophont: Sophont = VILANI) -> CharacterStartedEvent:
    return CharacterStartedEvent(id=id, sophont=sophont, homeworld=MOCK_WORLD, player='NPC', name='Boss')


def _ucp(id: int = 2, ucp: str = '7869A5') -> UcpEvent:
    return UcpEvent(id=id, fulfills='1.0', ucp=ucp)


def _ucp_low_edu(id: int = 2) -> UcpEvent:
    """UCP with EDU=0 → 0 background skills, no pending created."""
    return UcpEvent(id=id, fulfills='1.0', ucp='786000')


def _bg_skills(id: int = 3, skills: list | None = None) -> BackgroundSkillsEvent:
    if skills is None:
        skills = [Admin(), Athletics(), Carouse(), Drive()]  # 4 skills for EDU=10
    return BackgroundSkillsEvent(id=id, fulfills='2.0', skills=skills)


class TestCharacterStarted:
    def test_creates_ucp_pending_input(self):
        projection = replay(1, [_started()])

        assert len(projection.pending_inputs) == 1
        assert projection.pending_inputs[0].id == '1.0'
        assert isinstance(projection.pending_inputs[0], PendingUcp)

    def test_ucp_pending_is_blocking(self):
        projection = replay(1, [_started()])

        assert projection.pending_inputs[0].blocking is True

    def test_sets_character_id(self):
        projection = replay(42, [_started()])

        assert projection.character_id == 42

    def test_sets_name_sophont_and_homeworld_in_summary(self):
        projection = replay(1, [_started()])

        assert projection.summary.name == 'Boss'
        assert projection.summary.sophont == VILANI
        assert projection.summary.homeworld == MOCK_WORLD

    def test_first_pending_input_is_ucp(self):
        projection = replay(1, [_started()])

        assert isinstance(projection.pending_inputs[0], PendingUcp)


class TestUcpEvent:
    def test_ucp_pending_removed_after_ucp_event(self):
        projection = replay(1, [_started(), _ucp_low_edu()])

        assert not any(isinstance(p, PendingUcp) for p in projection.pending_inputs)

    def test_creates_background_skills_pending_when_edu_has_positive_dm(self):
        # EDU=10 → DM+1 → 4 background skills
        projection = replay(1, [_started(), _ucp(ucp='7869A5')])

        assert len(projection.pending_inputs) == 1
        assert isinstance(projection.pending_inputs[0], PendingBackgroundSkills)
        assert projection.pending_inputs[0].blocking is True

    def test_background_skills_pending_id_derived_from_ucp_event_id(self):
        projection = replay(1, [_started(), _ucp(id=2, ucp='7869A5')])

        assert projection.pending_inputs[0].id == '2.0'

    def test_background_skills_pending_count_in_instruction(self):
        # EDU=10 → DM+1 → 4 skills
        projection = replay(1, [_started(), _ucp(ucp='7869A5')])

        assert '4' in projection.pending_inputs[0].instruction

    def test_background_skills_pending_has_options_list(self):
        projection = replay(1, [_started(), _ucp(ucp='7869A5')])

        options = projection.pending_inputs[0].options
        assert 'Admin' in options
        assert 'Vacc Suit' in options
        assert options == sorted(options)

    def test_no_background_skills_pending_when_edu_zero(self):
        # EDU=0 → DM-3 → max(0, -3+3)=0 background skills
        projection = replay(1, [_started(), _ucp(ucp='786000')])

        assert projection.pending_inputs == []

    def test_background_skill_count_for_edu_6_to_8(self):
        # UCP: STR=7 DEX=8 END=6 INT=0 EDU=7 SOC=0 → EDU=7, DM+0 → 3 background skills
        projection = replay(1, [_started(), _ucp(ucp='786070')])

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingBackgroundSkills))
        assert '3' in pending.instruction

    def test_background_skill_count_for_edu_9_to_11(self):
        # UCP: STR=7 DEX=8 END=6 INT=0 EDU=9 SOC=0 → EDU=9, DM+1 → 4 background skills
        projection = replay(1, [_started(), _ucp(ucp='786090')])

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingBackgroundSkills))
        assert '4' in pending.instruction

    def test_background_skill_count_for_edu_12_to_14(self):
        # UCP: STR=7 DEX=8 END=6 INT=0 EDU=12=C SOC=0 → EDU=12, DM+2 → 5 background skills
        projection = replay(1, [_started(), _ucp(ucp='7860C0')])

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingBackgroundSkills))
        assert '5' in pending.instruction

    def test_sets_characteristics_from_short_form(self):
        projection = replay(1, [_started(), _ucp(ucp='7869A5')])

        assert projection.summary.characteristics == {
            'STR': 7,
            'DEX': 8,
            'END': 6,
            'INT': 9,
            'EDU': 10,
            'SOC': 5,
        }

    def test_sets_characteristics_from_max_values(self):
        projection = replay(1, [_started(), _ucp(ucp='FFFFFF')])

        assert projection.summary.characteristics == {
            'STR': 15,
            'DEX': 15,
            'END': 15,
            'INT': 15,
            'EDU': 15,
            'SOC': 15,
        }

    def test_no_pending_ucp_after_ucp_provided(self):
        projection = replay(1, [_started(), _ucp_low_edu()])

        assert not any(isinstance(p, PendingUcp) for p in projection.pending_inputs)


class TestBackgroundSkillsEvent:
    def test_resolves_background_skills_pending(self):
        events = [_started(), _ucp(), _bg_skills()]

        projection = replay(1, events)

        assert len(projection.pending_inputs) == 1
        assert isinstance(projection.pending_inputs[0], PendingCareerChoice)

    def test_grants_skills_at_level_0_in_summary(self):
        events = [_started(), _ucp(), _bg_skills(skills=[Admin(), Athletics(), Carouse(), Drive()])]

        projection = replay(1, events)

        assert projection.summary.skill_level('Admin') == 0
        assert projection.summary.skill_level('Athletics') == 0
        assert projection.summary.skill_level('Carouse') == 0
        assert projection.summary.skill_level('Drive') == 0
        assert len(projection.summary.skills) == 4

    def test_rejects_wrong_number_of_skills(self):
        too_few = BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics()])

        with pytest.raises(ReplayError):
            replay(1, [_started(), _ucp(), too_few])

    def test_rejects_non_background_skill(self):
        # Advocate is not in BackgroundSkills
        invalid = BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Advocate(), Carouse(), Drive()])

        with pytest.raises(ReplayError):
            replay(1, [_started(), _ucp(), invalid])

    def test_all_background_skills_are_known_skill_types(self):
        known_types = {cls.name() for cls in BACKGROUND_SKILLS}
        all_types = {info.type for info in skill_list()}
        unknown = known_types - all_types
        assert unknown == set(), f'Unknown skill types in BACKGROUND_SKILLS: {unknown}'

    def test_background_skills_blocked_by_no_pending(self):
        # Cannot submit background_skills when no such pending exists (EDU=0)
        event = BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[])

        with pytest.raises(ReplayError):
            replay(1, [_started(), _ucp_low_edu(), event])


class TestReplayFromPersistedEventLog:
    def test_replaying_persisted_event_log_rebuilds_identical_projection(self):
        backend = SqliteCharacterBackend(':memory:')
        try:
            row = backend.start(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')
            character_id = row['id']
            backend.append_event(character_id, UcpEvent(fulfills='1.0', ucp='7869A5'))
            backend.append_event(
                character_id,
                BackgroundSkillsEvent(
                    fulfills='2.0',
                    skills=[Admin(), Athletics(), Carouse(), Drive()],
                ),
            )

            original = backend.get_projection(character_id)
            events = backend.load_typed_events(character_id)

            assert original is not None
            assert events is not None
            rebuilt = replay(character_id, events)
            assert rebuilt.model_dump(mode='json') == original.model_dump(mode='json')
        finally:
            backend.close()

    def test_replaying_three_term_persisted_log_rebuilds_identical_projection(self):
        backend = SqliteCharacterBackend(':memory:')
        try:
            generate_npc(
                backend,
                CohortParams(
                    career='Scout',
                    assignment='Courier',
                    sophont='Humaniti',
                    min_terms=3,
                    max_terms=3,
                    name_prefix='Replay',
                ),
                name='Replay Test',
                rng=Random(1),
            )

            original = backend.get_projection(1)
            events = backend.load_typed_events(1)

            assert original is not None
            assert events is not None
            assert original.summary.term_count == 3
            assert any(
                event.kind == 'skill_choice'
                and (skill := event.model_dump(mode='json')['skill'])['type'] == 'Pilot'
                and skill['small_craft']['value'] == 0
                and skill['spacecraft']['value'] == 1
                and skill['capital_ships']['value'] == 0
                for event in events
            )
            rebuilt = replay(1, events)
            assert rebuilt.model_dump(mode='json') == original.model_dump(mode='json')
        finally:
            backend.close()


class TestReplayBlocking:
    def test_rejects_unrelated_event_while_ucp_pending(self):
        unrelated = UcpEvent(id=2, fulfills=None, ucp='7869A5')

        with pytest.raises(ReplayError):
            replay(1, [_started(), unrelated])

    def test_rejects_event_with_unknown_fulfills(self):
        wrong = UcpEvent(id=2, fulfills='99.0', ucp='7869A5')

        with pytest.raises(ReplayError):
            replay(1, [_started(), wrong])


class TestDeterminism:
    def test_same_events_produce_same_projection(self):
        events = [_started(), _ucp_low_edu()]

        first = replay(1, events)
        second = replay(1, events)

        assert first.model_dump() == second.model_dump()

    def test_empty_events_raises(self):
        with pytest.raises(ReplayError):
            replay(1, [])


class TestCharacterStartedEventJsonRoundTrip:
    def test_sophont_survives_json_round_trip(self):
        import json

        from pydantic import TypeAdapter

        from ceres.character.events import AnyEvent

        event = _started()
        adapter: TypeAdapter[AnyEvent] = TypeAdapter(AnyEvent)
        serialized = json.dumps(event.model_dump())
        restored = adapter.validate_python(json.loads(serialized))

        assert isinstance(restored, CharacterStartedEvent)
        assert restored.sophont == VILANI

    def test_homeworld_survives_json_round_trip(self):
        import json

        from pydantic import TypeAdapter

        from ceres.character.events import AnyEvent

        event = _started()
        adapter: TypeAdapter[AnyEvent] = TypeAdapter(AnyEvent)
        serialized = json.dumps(event.model_dump())
        restored = adapter.validate_python(json.loads(serialized))

        assert isinstance(restored, CharacterStartedEvent)
        assert restored.homeworld.name == MOCK_WORLD.name
        assert restored.homeworld.uwp == MOCK_WORLD.uwp
