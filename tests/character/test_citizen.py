from ceres.character.careers.citizen import (
    CitizenEvent8DoSo,
    CitizenEvent8GainContact,
    CitizenEvent8GainDeception,
    CitizenEvent8GainStreetwise,
    CitizenEvent8Refuse,
    CitizenMishap4Cooperate,
    CitizenMishap4Resist,
    PendingCitizenMishap5SkillRoll,
)
from ceres.character.careers.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.careers.loader import load_careers
from ceres.character.characteristics import Chars
from ceres.character.events import (
    AdvancementEvent,
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    PendingAdvancement,
    PendingChoices,
    PendingInitialTrainingChoice,
    PendingMusterOut,
    PendingSkillChoice,
    PendingSurvive,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, Engineer, Mechanic, Steward, Streetwise
from ceres.character.sophonts import VILANI
from ceres.character.state import (
    Contact,
    EffectTrigger,
    Rival,
)
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def test_citizen_career_loads_from_yaml():
    citizen = load_careers()['Citizen']
    worker = citizen.assignment('Worker')
    colonist = citizen.assignment('Colonist')

    assert [assignment.name for assignment in citizen.assignments] == ['Corporate', 'Worker', 'Colonist']
    assert worker is not None
    assert colonist is not None
    assert worker.survival.target == 4
    assert colonist.advancement.target == 5


def test_citizen_first_career_basic_training_uses_assignment_skills():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Citizen', assignment='Worker', qualification_roll=5),
    ]

    projection = replay(1, events)

    assert projection.summary.skill_level(Mechanic) == 0
    assert projection.summary.skill_level(Steward) is None


def test_citizen_subsequent_career_basic_training_chooses_one_assignment_skill():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills='4.0', roll=8),
        TermEventEvent(id=6, fulfills='5.0', roll=5),
        AdvancementEvent(id=7, fulfills='6.0', roll=3),
        ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
        CareerEvent(id=9, fulfills='8.0', career='Citizen', assignment='Worker', qualification_roll=5),
    ]

    projection = replay(1, events)

    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingInitialTrainingChoice))
    assert Engineer() in pending.options
    assert Mechanic() not in pending.options
    assert Steward() not in pending.options
    assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


def test_citizen_subsequent_career_basic_training_choice_unlocks_survival():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills='4.0', roll=8),
        TermEventEvent(id=6, fulfills='5.0', roll=5),
        AdvancementEvent(id=7, fulfills='6.0', roll=3),
        ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
        CareerEvent(id=9, fulfills='8.0', career='Citizen', assignment='Worker', qualification_roll=5),
        SkillChoiceEvent(id=10, fulfills='9.0', skill=Mechanic()),
    ]

    projection = replay(1, events)

    assert projection.summary.skill_level(Mechanic) == 0
    assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


# ── Corporate assignment helpers ──────────────────────────────────────────────
# Corporate table (Advocate, Admin, Broker, Electronics+spec, Diplomat, Leadership)
# has no broad-category skills, so all training is auto-applied: no PendingInitialTrainingChoice.
# Qualification: EDU 5+, EDU=10, DM+1 → need roll 4.
# Corporate survival: SOC 6+, SOC=5, DM−1 → need roll 7 (7+DM-1=6 ≥ 6 ✓).


def _enter_citizen(assignment: str = 'Corporate', qual_roll: int = 4) -> list:
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Citizen', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Corporate', survive_roll: int = 7) -> list:
    return [*_enter_citizen(assignment), SurviveEvent(id=5, fulfills='4.0', roll=survive_roll)]


def _through_term_event(event_roll: int, assignment: str = 'Corporate') -> list:
    return [*_through_survive(assignment), TermEventEvent(id=6, fulfills='5.0', roll=event_roll)]


# ── mishap 4: investigation by authorities ────────────────────────────────────


class TestCitizenMishap4:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_citizen(),
            SurviveEvent(id=5, fulfills='4.0', roll=6),  # SOC 6+, DM−1, 6 → 5 < 6 — fail
        ]

    def test_mishap_4_creates_choice_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=4)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CitizenMishap4Cooperate, CitizenMishap4Resist}

    def test_cooperate_adds_contact(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent.for_choice(CitizenMishap4Cooperate, id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        contacts = [c for c in projection.summary.connections if isinstance(c, Contact)]
        assert len(contacts) == 1

    def test_cooperate_ends_career_and_keeps_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent.for_choice(CitizenMishap4Cooperate, id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_resist_adds_rival(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent.for_choice(CitizenMishap4Resist, id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_resist_ends_career_and_loses_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent.for_choice(CitizenMishap4Resist, id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── mishap 5: revolution ──────────────────────────────────────────────────────


class TestCitizenMishap5:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_citizen(),
            SurviveEvent(id=5, fulfills='4.0', roll=6),
        ]

    def test_mishap_5_creates_streetwise_roll_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=5)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCitizenMishap5SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Streetwise()]

    def test_success_creates_skill_choice_from_existing_skills(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillRollEvent(id=7, fulfills='6.0', skill=Streetwise(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_no_skill_choice(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillRollEvent(id=7, fulfills='6.0', skill=Streetwise(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_both_outcomes_end_career(self):
        for roll in (9, 7):
            events = [
                *self._setup_to_mishap(),
                MishapEvent(id=6, fulfills='5.0', roll=5),
                SkillRollEvent(id=7, fulfills='6.0', skill=Streetwise(), modified_roll=roll),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, f'roll={roll}'


# ── event 6: advanced training ────────────────────────────────────────────────


class TestCitizenEvent6:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=6)

    def test_creates_edu_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingAdvancedTrainingSkillRoll)), None)
        assert pending is not None
        assert pending.options == [Chars.EDU]

    def test_success_creates_skill_choice_from_existing_skills(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', skill=Chars.EDU, modified_roll=11),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert any(isinstance(o, Admin) for o in pending.options)

    def test_failure_no_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', skill=Chars.EDU, modified_roll=9),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', skill=Chars.EDU, modified_roll=9),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


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
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(CitizenEvent8Refuse, id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        dm_effects = [se for se in projection.scheduled_effects if se.trigger == EffectTrigger.ADVANCEMENT]
        assert any(se.effect.get('amount') == 2 for se in dm_effects)

    def test_refuse_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(CitizenEvent8Refuse, id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_use_it_creates_reward_choice_pending(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(CitizenEvent8DoSo, id=7, fulfills='6.0'),
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
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(CitizenEvent8DoSo, id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_use_it_continues_career(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(CitizenEvent8DoSo, id=7, fulfills='6.0'),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Citizen'
