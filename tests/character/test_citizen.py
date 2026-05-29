from ceres.character.careers.loader import load_careers
from ceres.character.events import (
    AdvancementEvent,
    BackgroundSkillsEvent,
    CareerEvent,
    CharacterStartedEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.projection import PendingInitialTrainingChoice, PendingSurvive
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, Mechanic


def _setup() -> list:
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
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

    assert projection.summary.skill_level('Mechanic') == 0
    assert projection.summary.skill_level('Steward') is None


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
    assert 'Engineer' in pending.options
    assert 'Mechanic' not in pending.options
    assert 'Steward' not in pending.options
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

    assert projection.summary.skill_level('Mechanic') == 0
    assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)
