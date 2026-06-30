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
    PendingBackgroundSkills,
    PendingUcp,
    UcpHandler,
)
from ceres.character.domain.connection import (
    Contact,
)
from ceres.character.domain.health.health_events import (
    InjuryTableHandler,
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
from tests.unit.character.helpers import MOCK_WORLD, _creation_events, create_backend


def _drifter_wanderer_setup() -> list:
    """Three events placing a Drifter/Wanderer character at PendingSurvive."""
    creation = _creation_events(VILANI, MOCK_WORLD, 'NPC', 'Test')
    ev_ucp = Event(fulfills=(creation[-1].id, 0), handler=UcpHandler(ucp='786000'))  # EDU=0 → no pending created
    ev_entry = Event(
        fulfills=None,
        handler=CareerEntryHandler(career=DRIFTER, assignment=DRIFTER.assignment('Wanderer'), qualification_roll=10),
    )
    return [*creation, ev_ucp, ev_entry]


def _drifter_after_survive_success() -> list:
    """Extend _drifter_wanderer_setup with a successful SurviveEvent."""
    base = _drifter_wanderer_setup()
    return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=10))]


def _drifter_at_life_event() -> list:
    """Extend to a PendingLifeEvent via Drifter event 7 (Life Event)."""
    base = _drifter_after_survive_success()
    return [*base, Event(fulfills=(base[-1].id, 0), handler=TermEventHandler(roll=7))]


def _drifter_at_unusual_event() -> list:
    """Extend to PendingLifeEventUnusual + PendingAdvancement."""
    base = _drifter_at_life_event()
    return [*base, Event(fulfills=(base[-1].id, 0), handler=LifeEventHandler(roll=12))]


def _drifter_at_mishap() -> list:
    """Extend _drifter_wanderer_setup with auto-mishap (roll=2)."""
    base = _drifter_wanderer_setup()
    return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=2))]


def _scout_at_skill_table() -> list:
    """Events placing a Scout/Courier character with PendingSkillTable pending."""
    creation = _creation_events(VILANI, MOCK_WORLD, 'NPC', 'Test')
    ev_ucp = Event(fulfills=(creation[-1].id, 0), handler=UcpHandler(ucp='786000'))  # EDU=0, INT=0 → no pending
    ev_entry = Event(
        fulfills=None,
        handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=10),
    )
    ev_survive = Event(fulfills=(ev_entry.id, 0), handler=SurviveHandler(roll=10))
    ev_term = Event(fulfills=(ev_survive.id, 0), handler=TermEventHandler(roll=5))
    ev_advance = Event(fulfills=(ev_term.id, 0), handler=AdvancementHandler(roll=12))
    return [*creation, ev_ucp, ev_entry, ev_survive, ev_term, ev_advance]


def _drifter_at_injury_table() -> list:
    """Extend to PendingInjuryTable via Drifter mishap 2 (from_table)."""
    base = _drifter_at_mishap()
    return [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=2))]


def _creation(sophont: Sophont = VILANI) -> list[Event]:
    return _creation_events(sophont, MOCK_WORLD, 'NPC', 'Boss')


def _ucp(prev: Event | None = None, ucp: str = '7869A5') -> Event:
    fulfills = (prev.id, 0) if prev is not None else None
    return Event(fulfills=fulfills, handler=UcpHandler(ucp=ucp))


def _ucp_low_edu(prev: Event | None = None) -> Event:
    """UCP with EDU=0 → 0 background skills, no pending created."""
    fulfills = (prev.id, 0) if prev is not None else None
    return Event(fulfills=fulfills, handler=UcpHandler(ucp='786000'))


def _bg_skills(ucp: Event | None = None, skills: list | None = None) -> Event:
    if skills is None:
        skills = [Admin(), Athletics(), Carouse(), Drive()]  # 4 skills for EDU=10
    fulfills = (ucp.id, 0) if ucp is not None else None
    return Event(fulfills=fulfills, handler=BackgroundSkillsHandler(skills=skills))


class TestCreationFlow:
    def test_full_creation_ends_with_ucp_pending(self):
        creation = _creation()
        projection = replay(1, creation)

        assert len(projection.pending_inputs) == 1
        assert isinstance(projection.pending_inputs[0], PendingUcp)

    def test_ucp_pending_is_blocking(self):
        projection = replay(1, _creation())

        assert projection.pending_inputs[0].blocking is True

    def test_sets_character_id(self):
        projection = replay(42, _creation())

        assert projection.character_id == 42

    def test_sets_name_sophont_and_homeworld_in_summary(self):
        projection = replay(1, _creation())

        assert projection.summary.name == 'Boss'
        assert projection.summary.sophont == VILANI
        assert projection.summary.homeworld == MOCK_WORLD

    def test_sets_birthworld_equal_to_homeworld(self):
        projection = replay(1, _creation())

        assert projection.summary.birthworld == MOCK_WORLD

    def test_first_pending_after_sophont_is_ucp(self):
        projection = replay(1, _creation())

        assert isinstance(projection.pending_inputs[0], PendingUcp)


class TestUcpEvent:
    def test_ucp_pending_removed_after_ucp_event(self):
        c = _creation()
        projection = replay(1, [*c, _ucp_low_edu(c[-1])])

        assert not any(isinstance(p, PendingUcp) for p in projection.pending_inputs)

    def test_creates_background_skills_pending_when_edu_has_positive_dm(self):
        # EDU=10 → DM+1 → 4 background skills
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='7869A5')])

        assert len(projection.pending_inputs) == 1
        assert isinstance(projection.pending_inputs[0], PendingBackgroundSkills)
        assert projection.pending_inputs[0].blocking is True

    def test_background_skills_pending_id_derived_from_ucp_event_id(self):
        c = _creation()
        ev_ucp = _ucp(c[-1], ucp='7869A5')
        projection = replay(1, [*c, ev_ucp])

        assert projection.pending_inputs[0].id == f'{ev_ucp.id}.0'

    def test_background_skills_pending_count_in_instruction(self):
        # EDU=10 → DM+1 → 4 skills
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='7869A5')])

        assert '4' in projection.pending_inputs[0].instruction

    def test_background_skills_pending_has_options_list(self):
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='7869A5')])

        assert isinstance(projection.pending_inputs[0], PendingBackgroundSkills)
        options = projection.pending_inputs[0].options
        assert any(isinstance(o, Admin) for o in options)
        assert any(isinstance(o, VaccSuit) for o in options)
        assert options == sorted(options, key=lambda o: type(o).name())

    def test_no_background_skills_pending_when_edu_zero(self):
        # EDU=0 → DM-3 → max(0, -3+3)=0 background skills
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='786000')])

        assert projection.pending_inputs == []

    def test_background_skill_count_for_edu_6_to_8(self):
        # UCP: STR=7 DEX=8 END=6 INT=0 EDU=7 SOC=0 → EDU=7, DM+0 → 3 background skills
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='786070')])

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingBackgroundSkills))
        assert '3' in pending.instruction

    def test_background_skill_count_for_edu_9_to_11(self):
        # UCP: STR=7 DEX=8 END=6 INT=0 EDU=9 SOC=0 → EDU=9, DM+1 → 4 background skills
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='786090')])

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingBackgroundSkills))
        assert '4' in pending.instruction

    def test_background_skill_count_for_edu_12_to_14(self):
        # UCP: STR=7 DEX=8 END=6 INT=0 EDU=12=C SOC=0 → EDU=12, DM+2 → 5 background skills
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='7860C0')])

        pending = next(p for p in projection.pending_inputs if isinstance(p, PendingBackgroundSkills))
        assert '5' in pending.instruction

    def test_sets_characteristics_from_short_form(self):
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='7869A5')])

        assert projection.summary.characteristics == {
            'STR': 7,
            'DEX': 8,
            'END': 6,
            'INT': 9,
            'EDU': 10,
            'SOC': 5,
        }

    def test_sets_characteristics_from_max_values(self):
        c = _creation()
        projection = replay(1, [*c, _ucp(c[-1], ucp='FFFFFF')])

        assert projection.summary.characteristics == {
            'STR': 15,
            'DEX': 15,
            'END': 15,
            'INT': 15,
            'EDU': 15,
            'SOC': 15,
        }

    def test_no_pending_ucp_after_ucp_provided(self):
        c = _creation()
        projection = replay(1, [*c, _ucp_low_edu(c[-1])])

        assert not any(isinstance(p, PendingUcp) for p in projection.pending_inputs)


class TestBackgroundSkillsEvent:
    def test_resolves_background_skills_pending(self):
        c = _creation()
        ev_ucp = _ucp(c[-1])
        events = [*c, ev_ucp, _bg_skills(ev_ucp)]

        projection = replay(1, events)

        assert len(projection.pending_inputs) == 1
        assert isinstance(projection.pending_inputs[0], PendingCareerChoice)

    def test_grants_skills_at_level_0_in_summary(self):
        c = _creation()
        ev_ucp = _ucp(c[-1])
        events = [*c, ev_ucp, _bg_skills(ev_ucp, skills=[Admin(), Athletics(), Carouse(), Drive()])]

        projection = replay(1, events)

        assert projection.summary.skill_level(Admin) == 0
        assert projection.summary.skill_level(Athletics) == 0
        assert projection.summary.skill_level(Carouse) == 0
        assert projection.summary.skill_level(Drive) == 0
        assert len(projection.summary.skills) == 4

    def test_rejects_wrong_number_of_skills(self):
        c = _creation()
        ev_ucp = _ucp(c[-1])
        too_few = Event(fulfills=(ev_ucp.id, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics()]))

        with pytest.raises(ReplayError):
            replay(1, [*c, ev_ucp, too_few])

    def test_rejects_non_background_skill(self):
        # Advocate is not in BackgroundSkills
        c = _creation()
        ev_ucp = _ucp(c[-1])
        invalid = Event(
            fulfills=(ev_ucp.id, 0),
            handler=BackgroundSkillsHandler(skills=[Admin(), Advocate(), Carouse(), Drive()]),
        )

        with pytest.raises(ReplayError):
            replay(1, [*c, ev_ucp, invalid])

    def test_all_background_skills_are_known_skill_types(self):
        all_classes = set(_skill_classes(AnySkill))
        unknown = BACKGROUND_SKILLS - all_classes
        assert unknown == set(), f'Unknown classes in BACKGROUND_SKILLS: {unknown}'

    def test_background_skills_blocked_by_no_pending(self):
        # Cannot submit background_skills when no such pending exists (EDU=0)
        c = _creation()
        ev_ucp = _ucp_low_edu(c[-1])
        event = Event(fulfills=(ev_ucp.id, 0), handler=BackgroundSkillsHandler(skills=[]))

        with pytest.raises(ReplayError):
            replay(1, [*c, ev_ucp, event])


class TestReplayFromPersistedEventLog:
    def test_replaying_persisted_event_log_rebuilds_identical_projection(self):
        backend = create_backend(':memory:')
        try:
            row = backend.start(_creation_events(VILANI, MOCK_WORLD, 'NPC', 'Boss'), player='NPC', name='Boss')
            character_id = row['id']
            projection = backend.get_projection(character_id)
            assert projection is not None
            ucp_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingUcp))
            backend.append_event(character_id, Event(fulfills=ucp_pending.pending_id, handler=UcpHandler(ucp='7869A5')))
            projection = backend.get_projection(character_id)
            assert projection is not None
            background_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingBackgroundSkills))
            backend.append_event(
                character_id,
                Event(
                    fulfills=background_pending.pending_id,
                    handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
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
        unrelated = Event(fulfills=None, handler=UcpHandler(ucp='7869A5'))

        with pytest.raises(ReplayError):
            replay(1, [*_creation(), unrelated])

    def test_rejects_event_with_unknown_fulfills(self):
        unknown_pending = (99, 0)
        wrong = Event(fulfills=unknown_pending, handler=UcpHandler(ucp='7869A5'))

        with pytest.raises(ReplayError):
            replay(1, [*_creation(), wrong])


class TestDeterminism:
    def test_same_events_produce_same_projection(self):
        c = _creation()
        events = [*c, _ucp_low_edu(c[-1])]

        first = replay(1, events)
        second = replay(1, events)

        assert first.model_dump() == second.model_dump()

    def test_empty_events_raises(self):
        with pytest.raises(ReplayError):
            replay(1, [])


class TestCreationEventJsonRoundTrip:
    def test_sophont_selected_event_survives_json_round_trip(self):
        import json

        from pydantic import TypeAdapter

        from ceres.character.domain.character_start import SophontSelectedHandler

        ev = _creation()[-1]  # the SophontSelectedHandler event
        adapter: TypeAdapter[Event] = TypeAdapter(Event)
        serialized = json.dumps(ev.model_dump())
        restored = adapter.validate_python(json.loads(serialized))

        assert isinstance(restored.handler, SophontSelectedHandler)
        assert restored.handler.sophont == VILANI

    def test_homeworld_selected_event_survives_json_round_trip(self):
        import json

        from pydantic import TypeAdapter

        from ceres.character.domain.character_start import HomeworldSelectedHandler

        ev = _creation()[1]  # the HomeworldSelectedHandler event
        adapter: TypeAdapter[Event] = TypeAdapter(Event)
        serialized = json.dumps(ev.model_dump())
        restored = adapter.validate_python(json.loads(serialized))

        assert isinstance(restored.handler, HomeworldSelectedHandler)
        assert restored.handler.homeworld.name == MOCK_WORLD.name
        assert restored.handler.homeworld.uwp == MOCK_WORLD.uwp


class TestLifeEventValidation:
    def test_roll_too_low_raises(self):
        base = _drifter_at_life_event()
        with pytest.raises(ReplayError, match='2-12'):
            replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=LifeEventHandler(roll=1))])

    def test_roll_too_high_raises(self):
        base = _drifter_at_life_event()
        with pytest.raises(ReplayError, match='2-12'):
            replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=LifeEventHandler(roll=13))])


class TestLifeEventUnusualBranches:
    def test_roll_out_of_range_raises(self):
        base = _drifter_at_unusual_event()
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=LifeEventUnusualHandler(roll=7))])

    def test_roll_1_queues_psionics_roll_pending(self):
        from ceres.character.domain.career.career_events import PendingLifeEventPsionicsRoll

        base = _drifter_at_unusual_event()
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=LifeEventUnusualHandler(roll=1))])
        assert not projection.summary.connections
        assert any(isinstance(p, PendingLifeEventPsionicsRoll) for p in projection.pending_inputs)

    def test_roll_2_gains_contact_and_queues_science_choice(self):
        from ceres.character.domain.career.career_events import PendingLifeEventAlienScience

        base = _drifter_at_unusual_event()
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=LifeEventUnusualHandler(roll=2))])
        assert any(isinstance(c, Contact) for c in projection.summary.connections)
        assert any(isinstance(p, PendingLifeEventAlienScience) for p in projection.pending_inputs)
        assert projection.summary.skill_level(SpaceScience) is None

    def test_roll_3_no_mechanical_effect(self):
        base = _drifter_at_unusual_event()
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=LifeEventUnusualHandler(roll=3))])
        assert not projection.summary.connections

    def test_roll_6_no_mechanical_effect(self):
        base = _drifter_at_unusual_event()
        projection = replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=LifeEventUnusualHandler(roll=6))])
        assert not projection.summary.connections


class TestInjuryTableValidation:
    def test_roll_zero_raises(self):
        base = _drifter_at_injury_table()
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=InjuryTableHandler(roll=0))])

    def test_roll_seven_raises(self):
        base = _drifter_at_injury_table()
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, [*base, Event(fulfills=(base[-1].id, 0), handler=InjuryTableHandler(roll=7))])


class TestMishapInjuryEffects:
    def test_from_table_injury_creates_injury_table_pending(self):
        # Drifter mishap 2: severity=from_table → roll on injury table
        base = _drifter_at_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=2))]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)


class TestSkillTableErrors:
    def test_unknown_table_raises(self):
        base = _scout_at_skill_table()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=SkillTableHandler(table='bogus_table', roll=3))]
        with pytest.raises(ReplayError, match='Unknown skill table'):
            replay(1, events)

    def test_min_edu_not_met_raises(self):
        # EDU=0 < advanced_education min_edu=8
        base = _scout_at_skill_table()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillTableHandler(table='advanced_education', roll=3)),
        ]
        with pytest.raises(ReplayError, match='requires EDU'):
            replay(1, events)

    def test_roll_zero_raises(self):
        base = _scout_at_skill_table()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=SkillTableHandler(table='service_skills', roll=0))]
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, events)

    def test_roll_seven_raises(self):
        base = _scout_at_skill_table()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=SkillTableHandler(table='service_skills', roll=7))]
        with pytest.raises(ReplayError, match='1-6'):
            replay(1, events)


class TestDraftErrors:
    def _events_with_draft_choice(self) -> list:
        """Citizen qualification fails (EDU 5+, EDU=0) → PendingDraftChoice."""
        c = _creation_events(VILANI, MOCK_WORLD, 'NPC', 'Test')
        ev_ucp = Event(fulfills=(c[-1].id, 0), handler=UcpHandler(ucp='786000'))  # EDU=0 → no pending created
        ev_entry = Event(
            handler=CareerEntryHandler(
                career=CITIZEN,
                assignment=CITIZEN.assignment('Corporate'),
                qualification_roll=1,
            ),
        )
        # EDU 5+, DM-3: 1-3=-2 < 5 → fails → PendingDraftChoice
        return [*c, ev_ucp, ev_entry]

    def test_unknown_career_draft_raises(self):
        from pydantic import ValidationError

        with pytest.raises((ValidationError, Exception)):
            DraftHandler(career='NoSuchCareer')  # ty: ignore[invalid-argument-type]
