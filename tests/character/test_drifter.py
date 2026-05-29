from ceres.character.careers.loader import load_careers, selectable_careers
from ceres.character.events import BackgroundSkillsEvent, CareerEvent, CharacterStartedEvent, UcpEvent
from ceres.character.projection import PendingInitialTrainingChoice, PendingSurvive
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive


def _setup() -> list:
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def test_drifter_career_loads_and_is_selectable():
    drifter = load_careers()['Drifter']

    assert 'Drifter' in selectable_careers()
    assert [assignment.name for assignment in drifter.assignments] == ['Barbarian', 'Wanderer', 'Scavenger']


def test_drifter_first_career_basic_training_uses_assignment_skills():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Drifter', assignment='Wanderer', qualification_roll=0),
    ]

    projection = replay(1, events)

    assert projection.summary.skill_level('Deception') == 0
    assert projection.summary.skill_level('Survival') == 0
    assert projection.summary.skill_level('Melee') is None


def test_drifter_basic_training_defers_survival_for_assignment_skill_choices():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Drifter', assignment='Scavenger', qualification_roll=0),
    ]

    projection = replay(1, events)

    assert any(isinstance(p, PendingInitialTrainingChoice) for p in projection.pending_inputs)
    assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)
