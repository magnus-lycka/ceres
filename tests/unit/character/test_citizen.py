from ceres.character.domain.career import CITIZEN, SCOUT
from ceres.character.domain.career.career_events import (
    AdvancementHandler,
    CareerChoiceHandler,
    CareerEntryHandler,
    MishapHandler,
    PendingAdvancement,
    PendingChoices,
    PendingInitialTrainingChoice,
    PendingMusterOut,
    PendingSkillChoice,
    PendingSurvive,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.citizen import (
    CitizenEvent8DoSo,
    CitizenEvent8GainContact,
    CitizenEvent8GainDeception,
    CitizenEvent8GainStreetwise,
    CitizenEvent8Refuse,
    CitizenMishap4Cooperate,
    CitizenMishap4Resist,
    PendingCitizenMishap5SkillRoll,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import (
    Ally,
    Contact,
    Enemy,
    Rival,
)
from ceres.character.domain.skills import (
    Admin,
    AnySkill,
    Athletics,
    Carouse,
    Drive,
    Engineer,
    GunCombat,
    Level,
    Mechanic,
    Steward,
    Streetwise,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD, AnySkillAtLevelTestMixin


def _setup(skills: list[AnySkill] | None = None) -> list:
    chosen = skills if skills is not None else [Admin(), Athletics(), Carouse(), Drive()]
    started = Event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'))
    ucp = Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(fulfills=(ucp.id, 0), handler=BackgroundSkillsHandler(skills=chosen))
    return [started, ucp, background]


def _after_scout_term() -> list:
    base = _setup()
    scout = Event(
        fulfills=(base[-1].id, 0),
        handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
    )
    survive = Event(fulfills=(scout.id, 0), handler=SurviveHandler(roll=8))
    term_event = Event(fulfills=(survive.id, 0), handler=TermEventHandler(roll=5))
    advancement = Event(fulfills=(term_event.id, 0), handler=AdvancementHandler(roll=3))
    leave = Event(fulfills=(advancement.id, 0), handler=ReenlistHandler(reenlist=False))
    return [*base, scout, survive, term_event, advancement, leave]


def test_citizen_career_loads_from_yaml():
    citizen = CITIZEN
    worker = citizen.assignment('Worker')
    colonist = citizen.assignment('Colonist')

    assert [assignment.name for assignment in citizen.assignments] == ['Corporate', 'Worker', 'Colonist']
    assert worker is not None
    assert colonist is not None
    assert worker.survival.target == 4
    assert colonist.advancement.target == 5


def test_citizen_first_career_basic_training_uses_assignment_skills():
    base = _setup()
    events = [
        *base,
        Event(
            fulfills=(base[-1].id, 0),
            handler=CareerEntryHandler(career=CITIZEN, assignment=CITIZEN.assignment('Worker'), qualification_roll=5),
        ),
    ]

    projection = replay(1, events)

    assert projection.summary.skill_level(Mechanic) == 0
    assert projection.summary.skill_level(Steward) is None


def test_citizen_subsequent_career_basic_training_chooses_one_assignment_skill():
    base = _after_scout_term()
    events = [
        *base,
        Event(
            fulfills=(base[-1].id, 0),
            handler=CareerEntryHandler(career=CITIZEN, assignment=CITIZEN.assignment('Worker'), qualification_roll=5),
        ),
    ]

    projection = replay(1, events)

    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice))
    assert Engineer() in pending.options
    assert Mechanic() not in pending.options
    assert Steward() not in pending.options
    assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


def test_citizen_subsequent_career_basic_training_choice_unlocks_survival():
    base = _after_scout_term()
    citizen = Event(
        fulfills=(base[-1].id, 0),
        handler=CareerEntryHandler(career=CITIZEN, assignment=CITIZEN.assignment('Worker'), qualification_roll=5),
    )
    events = [
        *base,
        citizen,
        Event(fulfills=(citizen.id, 0), handler=SkillChoiceHandler(skill=Mechanic())),
    ]

    projection = replay(1, events)

    assert projection.summary.skill_level(Mechanic) == 0
    assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


# ── Corporate assignment helpers ──────────────────────────────────────────────
# Corporate table (Advocate, Admin, Broker, Electronics+spec, Diplomat, Leadership)
# has no broad-category skills, so all training is auto-applied: no PendingInitialTrainingChoice.
# Qualification: EDU 5+, EDU=10, DM+1 → need roll 4.
# Corporate survival: SOC 6+, SOC=5, DM−1 → need roll 7 (7+DM-1=6 ≥ 6 ✓).


def _enter_citizen(assignment: str = 'Corporate', qual_roll: int = 4, skills: list[AnySkill] | None = None) -> list:
    base = _setup(skills=skills)
    entry = Event(
        fulfills=(base[-1].id, 0),
        handler=CareerEntryHandler(
            career=CITIZEN, assignment=CITIZEN.assignment(assignment), qualification_roll=qual_roll
        ),
    )
    return [
        *base,
        entry,
    ]


def _through_survive(assignment: str = 'Corporate', survive_roll: int = 7) -> list:
    base = _enter_citizen(assignment)
    return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Corporate') -> list:
    base = _through_survive(assignment)
    return [*base, Event(fulfills=(base[-1].id, 0), handler=TermEventHandler(roll=event_roll))]


class TestCitizenDirectOutcomeRows:
    def test_mishap_2_adds_enemy_and_ends_career(self):
        base = _enter_citizen()
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=2))
        projection = replay(1, [*base, survive, Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=2))])

        assert any(isinstance(c, Enemy) for c in projection.summary.connections)
        assert projection.summary.current_career is None

    def test_mishap_3_decreases_soc_and_ends_career(self):
        base = _enter_citizen()
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=2))
        projection = replay(1, [*base, survive, Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=3))])

        assert projection.summary.characteristics[Chars.SOC] == 4
        assert projection.summary.current_career is None

    def test_event_5_adds_benefit_dm(self):
        projection = replay(1, _through_term_event(5))

        dms = projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms
        assert len(dms) == 1
        assert dms[0].amount == 1

    def test_event_9_adds_advancement_dm(self):
        projection = replay(1, _through_term_event(9))

        assert projection.pending_advancement_dm == 2

    def test_event_11_adds_ally(self):
        projection = replay(1, _through_term_event(11))

        assert any(isinstance(c, Ally) for c in projection.summary.connections)


# ── mishap 4: investigation by authorities ────────────────────────────────────


class TestCitizenMishap4:
    def _setup_to_mishap(self) -> list:
        base = _enter_citizen()
        return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=6))]

    def test_mishap_4_creates_choice_pending(self):
        base = self._setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=4))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CitizenMishap4Cooperate, CitizenMishap4Resist}

    def test_cooperate_adds_contact(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=4))
        events = [
            *base,
            mishap,
            Event(
                fulfills=(mishap.id, 0),
                handler=CareerChoiceHandler(choice=CitizenMishap4Cooperate.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        contacts = [c for c in projection.summary.connections if isinstance(c, Contact)]
        assert len(contacts) == 1

    def test_cooperate_ends_career_and_keeps_benefit_roll(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=4))
        events = [
            *base,
            mishap,
            Event(
                fulfills=(mishap.id, 0),
                handler=CareerChoiceHandler(choice=CitizenMishap4Cooperate.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_resist_adds_rival(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=4))
        events = [
            *base,
            mishap,
            Event(
                fulfills=(mishap.id, 0),
                handler=CareerChoiceHandler(choice=CitizenMishap4Resist.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_resist_ends_career_and_loses_benefit_roll(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=4))
        events = [
            *base,
            mishap,
            Event(
                fulfills=(mishap.id, 0),
                handler=CareerChoiceHandler(choice=CitizenMishap4Resist.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── mishap 5: revolution ──────────────────────────────────────────────────────


class TestCitizenMishap5:
    def _setup_to_mishap(self) -> list:
        base = _enter_citizen()
        return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=6))]

    def test_mishap_5_creates_streetwise_roll_pending(self):
        base = self._setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCitizenMishap5SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Streetwise()]

    def test_success_creates_skill_choice_from_existing_skills(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_success_skill_choice_uses_existing_instances_not_fresh(self):
        # Drive(wheel=1): options must carry the existing instance so that
        # build_skill_select_options restricts choices to the wheel specialty only.
        custom_skills: list[AnySkill] = [Admin(), Athletics(), Carouse(), Drive(wheel=Level(value=1))]
        base = _enter_citizen(skills=custom_skills)
        survive = Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=6))
        mishap = Event(fulfills=(survive.id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            survive,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=9)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        drive_option = next((o for o in pending.options if isinstance(o, Drive)), None)
        assert drive_option is not None
        assert drive_option.wheel.value == 1  # existing instance, not a fresh Drive()

    def test_failure_no_skill_choice(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_both_outcomes_end_career(self):
        for roll in (9, 7):
            base = self._setup_to_mishap()
            mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
            events = [
                *base,
                mishap,
                Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Streetwise(), modified_roll=roll)),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, f'roll={roll}'


# ── event 6: advanced training ────────────────────────────────────────────────


class TestCitizenEvent6(AnySkillAtLevelTestMixin):
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=6)

    def _absent_skill_type(self) -> type:
        return GunCombat  # not in Citizen Corporate service skills or standard background skills

    def _absent_skill_instance(self) -> GunCombat:
        return GunCombat(slug=Level(value=1))

    def _threshold(self) -> int:
        return 10


# ── event 8: illegal information ─────────────────────────────────────────────


class TestCitizenEvent8:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=8)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CitizenEvent8DoSo, CitizenEvent8Refuse}

    def test_refuse_schedules_advancement_dm_2(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=CitizenEvent8Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_advancement_dm == 2

    def test_refuse_queues_advancement(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=CitizenEvent8Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_use_it_creates_reward_choice_pending(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=CitizenEvent8DoSo.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        reward_pending = next(
            (
                p
                for p in projection.pending_inputs
                if isinstance(p, PendingChoices)
                and any(
                    isinstance(c, (CitizenEvent8GainContact, CitizenEvent8GainStreetwise, CitizenEvent8GainDeception))
                    for c in p.choices
                )
            ),
            None,
        )
        assert reward_pending is not None
        assert any(isinstance(c, CitizenEvent8GainContact) for c in reward_pending.choices)

    def test_use_it_immediately_adds_extra_benefit_roll(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=CitizenEvent8DoSo.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_use_it_continues_career(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=CitizenEvent8DoSo.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Citizen'
