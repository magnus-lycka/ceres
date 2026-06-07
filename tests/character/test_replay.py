import pytest

from ceres.character.domain.career import CITIZEN, DRIFTER, SCOUT
from ceres.character.domain.career.career_events import (
    AdvancementHandler,
    CareerEntryHandler,
    DraftHandler,
    LifeEventHandler,
    LifeEventUnusualHandler,
    MishapHandler,
    PendingCareerChoice,
    SkillTableHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.character_start import (
    BACKGROUND_SKILLS,
    BackgroundSkillsHandler,
    CharacterStartedHandler,
    PendingBackgroundSkills,
    PendingUcp,
    UcpHandler,
)
from ceres.character.domain.connection import (
    Ally,
    Contact,
)
from ceres.character.domain.health.health_events import (
    InjuryTableHandler,
    PendingCharacteristicChoice,
    PendingInjuryTable,
)
from ceres.character.domain.skills import (
    Admin,
    Advocate,
    AnySkill,
    Athletics,
    Carouse,
    Drive,
    SpaceScience,
    VaccSuit,
    _skill_classes,
)
from ceres.character.domain.sophont import VILANI, Sophont
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import ReplayError, replay
from ceres.character.mechanism.store import SqliteCharacterBackend
from tests.character.helpers import MOCK_WORLD


def _drifter_wanderer_setup() -> list:
    """Three events placing a Drifter/Wanderer character at PendingSurvive('3.0').

    Uses EDU=0 UCP to skip background skills. Drifter always qualifies (target END 0).
    """
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Test')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='786000')),  # EDU=0 → no pending created
        Event(
            id=3,
            handler=CareerEntryHandler(
                career=DRIFTER, assignment=DRIFTER.assignment('Wanderer'), qualification_roll=10
            ),
        ),
        # all service skills auto-granted → PendingSurvive('3.0')
    ]


def _drifter_after_survive_success() -> list:
    """Extend _drifter_wanderer_setup with a successful SurviveEvent → PendingTermEvent('4.0')."""
    return [*_drifter_wanderer_setup(), Event(id=4, fulfills=(3, 0), handler=SurviveHandler(roll=10))]


def _drifter_at_life_event() -> list:
    """Extend to a PendingLifeEvent('5.0') via Drifter event 7 (Life Event)."""
    return [*_drifter_after_survive_success(), Event(id=5, fulfills=(4, 0), handler=TermEventHandler(roll=7))]


def _drifter_at_unusual_event() -> list:
    """Extend to PendingLifeEventUnusual('6.0') + PendingAdvancement('6.1')."""
    return [*_drifter_at_life_event(), Event(id=6, fulfills=(5, 0), handler=LifeEventHandler(roll=12))]


def _drifter_at_mishap() -> list:
    """Extend _drifter_wanderer_setup with auto-mishap (roll=2) → PendingMishap('4.0')."""
    return [*_drifter_wanderer_setup(), Event(id=4, fulfills=(3, 0), handler=SurviveHandler(roll=2))]


def _scout_at_skill_table() -> list:
    """Events placing a Scout/Courier character with PendingSkillTable('6.0') pending.

    Uses EDU=0 UCP. Qualifies (INT 5+, DM-3, roll=10 → 7≥5). Advances via EDU 9+
    (DM-3, roll=12 → 9≥9). Rank 1 bonus (Vacc Suit 1) granted automatically.
    """
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Test')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='786000')),  # EDU=0, INT=0 → no pending created
        Event(
            id=3,
            handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=10),
        ),
        Event(id=4, fulfills=(3, 0), handler=SurviveHandler(roll=10)),  # END=6, target=5 → success
        Event(id=5, fulfills=(4, 0), handler=TermEventHandler(roll=5)),  # benefit_dm → PendingAdvancement('5.0')
        Event(id=6, fulfills=(5, 0), handler=AdvancementHandler(roll=12)),  # EDU 9+, DM-3 → 9≥9 success
        # rank 1 bonus (Vacc Suit 1) auto-granted → PendingSkillTable('6.0') + PendingAssignmentChangeChoice('6.1')
    ]


def _drifter_at_injury_table() -> list:
    """Extend to PendingInjuryTable('5.0') via Drifter mishap 2 (from_table)."""
    return [*_drifter_at_mishap(), Event(id=5, fulfills=(4, 0), handler=MishapHandler(roll=2))]


def _started(id: int = 1, sophont: Sophont = VILANI) -> Event:
    return Event(
        id=id, handler=CharacterStartedHandler(sophont=sophont, homeworld=MOCK_WORLD, player='NPC', name='Boss')
    )


def _ucp(id: int = 2, ucp: str = '7869A5') -> Event:
    return Event(id=id, fulfills=(1, 0), handler=UcpHandler(ucp=ucp))


def _ucp_low_edu(id: int = 2) -> Event:
    """UCP with EDU=0 → 0 background skills, no pending created."""
    return Event(id=id, fulfills=(1, 0), handler=UcpHandler(ucp='786000'))


def _bg_skills(id: int = 3, skills: list | None = None) -> Event:
    if skills is None:
        skills = [Admin(), Athletics(), Carouse(), Drive()]  # 4 skills for EDU=10
    return Event(id=id, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=skills))


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

    def test_sets_birthworld_equal_to_homeworld_on_start(self):
        projection = replay(1, [_started()])

        assert projection.summary.birthworld == MOCK_WORLD

    def test_birthworld_is_immutable_starting_world(self):
        projection = replay(1, [_started()])

        assert projection.summary.birthworld == projection.summary.homeworld

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

        assert isinstance(projection.pending_inputs[0], PendingBackgroundSkills)
        options = projection.pending_inputs[0].options
        assert any(isinstance(o, Admin) for o in options)
        assert any(isinstance(o, VaccSuit) for o in options)
        assert options == sorted(options, key=lambda o: type(o).name())

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

        assert projection.summary.skill_level(Admin) == 0
        assert projection.summary.skill_level(Athletics) == 0
        assert projection.summary.skill_level(Carouse) == 0
        assert projection.summary.skill_level(Drive) == 0
        assert len(projection.summary.skills) == 4

    def test_rejects_wrong_number_of_skills(self):
        too_few = Event(id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics()]))

        with pytest.raises(ReplayError):
            replay(1, [_started(), _ucp(), too_few])

    def test_rejects_non_background_skill(self):
        # Advocate is not in BackgroundSkills
        invalid = Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Advocate(), Carouse(), Drive()])
        )

        with pytest.raises(ReplayError):
            replay(1, [_started(), _ucp(), invalid])

    def test_all_background_skills_are_known_skill_types(self):
        all_classes = set(_skill_classes(AnySkill))
        unknown = BACKGROUND_SKILLS - all_classes
        assert unknown == set(), f'Unknown classes in BACKGROUND_SKILLS: {unknown}'

    def test_background_skills_blocked_by_no_pending(self):
        # Cannot submit background_skills when no such pending exists (EDU=0)
        event = Event(id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[]))

        with pytest.raises(ReplayError):
            replay(1, [_started(), _ucp_low_edu(), event])


class TestReplayFromPersistedEventLog:
    def test_replaying_persisted_event_log_rebuilds_identical_projection(self):
        backend = SqliteCharacterBackend(':memory:')
        try:
            row = backend.start(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')
            character_id = row['id']
            backend.append_event(character_id, Event(fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')))
            backend.append_event(
                character_id,
                Event(
                    fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
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


class TestReplayBlocking:
    def test_rejects_unrelated_event_while_ucp_pending(self):
        unrelated = Event(id=2, fulfills=None, handler=UcpHandler(ucp='7869A5'))

        with pytest.raises(ReplayError):
            replay(1, [_started(), unrelated])

    def test_rejects_event_with_unknown_fulfills(self):
        wrong = Event(id=2, fulfills=(99, 0), handler=UcpHandler(ucp='7869A5'))

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

        event = _started()
        adapter: TypeAdapter[Event] = TypeAdapter(Event)
        serialized = json.dumps(event.model_dump())
        restored = adapter.validate_python(json.loads(serialized))

        assert isinstance(restored.handler, CharacterStartedHandler)
        assert restored.sophont == VILANI

    def test_homeworld_survives_json_round_trip(self):
        import json

        from pydantic import TypeAdapter

        event = _started()
        adapter: TypeAdapter[Event] = TypeAdapter(Event)
        serialized = json.dumps(event.model_dump())
        restored = adapter.validate_python(json.loads(serialized))

        assert isinstance(restored.handler, CharacterStartedHandler)
        assert restored.homeworld.name == MOCK_WORLD.name
        assert restored.homeworld.uwp == MOCK_WORLD.uwp


class TestLifeEventValidation:
    def test_roll_too_low_raises(self):
        with pytest.raises(ReplayError, match='2-12'):
            replay(1, [*_drifter_at_life_event(), Event(id=6, fulfills=(5, 0), handler=LifeEventHandler(roll=1))])

    def test_roll_too_high_raises(self):
        with pytest.raises(ReplayError, match='2-12'):
            replay(1, [*_drifter_at_life_event(), Event(id=6, fulfills=(5, 0), handler=LifeEventHandler(roll=13))])


class TestLifeEventUnusualBranches:
    def test_roll_out_of_range_raises(self):
        with pytest.raises(ReplayError, match='1-6'):
            replay(
                1, [*_drifter_at_unusual_event(), Event(id=7, fulfills=(6, 0), handler=LifeEventUnusualHandler(roll=7))]
            )

    def test_roll_1_gains_ally(self):
        projection = replay(
            1, [*_drifter_at_unusual_event(), Event(id=7, fulfills=(6, 0), handler=LifeEventUnusualHandler(roll=1))]
        )
        assert any(isinstance(c, Ally) for c in projection.summary.connections)

    def test_roll_2_gains_contact_and_space_science(self):
        projection = replay(
            1, [*_drifter_at_unusual_event(), Event(id=7, fulfills=(6, 0), handler=LifeEventUnusualHandler(roll=2))]
        )
        assert any(isinstance(c, Contact) for c in projection.summary.connections)
        assert projection.summary.skill_level(SpaceScience) == 1

    def test_roll_3_no_mechanical_effect(self):
        projection = replay(
            1, [*_drifter_at_unusual_event(), Event(id=7, fulfills=(6, 0), handler=LifeEventUnusualHandler(roll=3))]
        )
        assert not projection.summary.connections

    def test_roll_6_no_mechanical_effect(self):
        projection = replay(
            1, [*_drifter_at_unusual_event(), Event(id=7, fulfills=(6, 0), handler=LifeEventUnusualHandler(roll=6))]
        )
        assert not projection.summary.connections


class TestInjuryTableValidation:
    def test_roll_zero_raises(self):
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, [*_drifter_at_injury_table(), Event(id=6, fulfills=(5, 0), handler=InjuryTableHandler(roll=0))])

    def test_roll_seven_raises(self):
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, [*_drifter_at_injury_table(), Event(id=6, fulfills=(5, 0), handler=InjuryTableHandler(roll=7))])


class TestMishapInjuryEffects:
    def test_severe_injury_creates_characteristic_choice(self):
        # Drifter mishap 1: severity=severe → choose STR/DEX/END to reduce by 2
        events = [*_drifter_at_mishap(), Event(id=5, fulfills=(4, 0), handler=MishapHandler(roll=1))]
        projection = replay(1, events)
        char_choices = [p for p in projection.pending_inputs if isinstance(p, PendingCharacteristicChoice)]
        assert len(char_choices) == 1
        assert 'reduce by 2' in char_choices[0].instruction
        assert char_choices[0].amount == 2

    def test_from_table_injury_creates_injury_table_pending(self):
        # Drifter mishap 2: severity=from_table → roll on injury table
        events = [*_drifter_at_mishap(), Event(id=5, fulfills=(4, 0), handler=MishapHandler(roll=2))]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)


class TestSkillTableErrors:
    def test_unknown_table_raises(self):
        events = [
            *_scout_at_skill_table(),
            Event(id=7, fulfills=(6, 0), handler=SkillTableHandler(table='bogus_table', roll=3)),
        ]
        with pytest.raises(ReplayError, match='Unknown skill table'):
            replay(1, events)

    def test_min_edu_not_met_raises(self):
        # EDU=0 < advanced_education min_edu=8
        events = [
            *_scout_at_skill_table(),
            Event(id=7, fulfills=(6, 0), handler=SkillTableHandler(table='advanced_education', roll=3)),
        ]
        with pytest.raises(ReplayError, match='requires EDU'):
            replay(1, events)

    def test_roll_zero_raises(self):
        events = [
            *_scout_at_skill_table(),
            Event(id=7, fulfills=(6, 0), handler=SkillTableHandler(table='service_skills', roll=0)),
        ]
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, events)

    def test_roll_seven_raises(self):
        events = [
            *_scout_at_skill_table(),
            Event(id=7, fulfills=(6, 0), handler=SkillTableHandler(table='service_skills', roll=7)),
        ]
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, events)


class TestDraftErrors:
    def _events_with_draft_choice(self) -> list:
        """Citizen qualification fails (EDU 5+, EDU=0) → PendingDraftChoice('3.0')."""
        return [
            Event(
                id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Test')
            ),
            Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='786000')),  # EDU=0 → no pending created
            Event(
                id=3,
                handler=CareerEntryHandler(
                    career=CITIZEN, assignment=CITIZEN.assignment('Corporate'), qualification_roll=1
                ),
            ),
            # EDU 5+, DM-3: 1-3=-2 < 5 → fails → PendingDraftChoice('3.0')
        ]

    def test_unknown_career_draft_raises(self):
        from pydantic import ValidationError

        with pytest.raises((ValidationError, Exception)):
            DraftHandler(career='NoSuchCareer')  # ty: ignore[invalid-argument-type]
