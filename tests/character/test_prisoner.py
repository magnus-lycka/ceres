from ceres.character.careers.loader import load_careers, selectable_careers
from ceres.character.events import BackgroundSkillsEvent, CareerEvent, CharacterStartedEvent, UcpEvent
from ceres.character.projection import PendingCareerChoice, PendingInitialTrainingChoice
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive


def _setup() -> list:
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def test_prisoner_career_loads_but_is_not_selectable():
    careers = load_careers()

    assert 'Prisoner' in careers
    assert 'Prisoner' not in selectable_careers()


def test_prisoner_is_not_listed_after_background_skills():
    projection = replay(1, _setup())

    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice))
    assert 'Prisoner' not in pending.options


def test_prisoner_can_be_entered_when_event_log_sends_character_there():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Prisoner', assignment='Inmate', qualification_roll=0),
    ]

    projection = replay(1, events)

    assert projection.summary.current_career == 'Prisoner'
    assert projection.summary.current_assignment == 'Inmate'
    assert projection.summary.skill_level('Melee') == 1
    assert any(isinstance(p, PendingInitialTrainingChoice) for p in projection.pending_inputs)
