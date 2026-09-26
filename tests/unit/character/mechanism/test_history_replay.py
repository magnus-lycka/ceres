"""History is derived from immutable event inputs at each replay prefix."""

from ceres.character.domain.career import MERCHANT
from ceres.character.domain.career.career_events import (
    CareerEntryHandler,
    PendingCareerChoice,
    PendingSurvive,
    PendingTermEvent,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.character_start import (
    BackgroundSkillsHandler,
    PendingBackgroundSkills,
    PendingUcp,
    UcpHandler,
)
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD, _creation_events


def test_repeated_replay_and_earlier_prefix_preserve_the_source_events():
    events = list(_creation_events(VILANI, MOCK_WORLD))
    for pending_type, handler in [
        (PendingUcp, UcpHandler(ucp='7869A5')),
        (PendingBackgroundSkills, BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])),
        (
            PendingCareerChoice,
            CareerEntryHandler(
                career=MERCHANT,
                assignment=MERCHANT.assignment('Merchant Marine'),
                qualification_roll=9,
            ),
        ),
        (PendingSurvive, SurviveHandler(roll=7)),
        (PendingTermEvent, TermEventHandler(roll=9)),
        (PendingAdvancedTrainingSkillRoll, SkillRollHandler(skill=Chars.EDU, modified_roll=7)),
    ]:
        projection = replay(1, events)
        pending = next(p for p in projection.pending_inputs if isinstance(p, pending_type))
        events.append(Event(fulfills=pending.pending_id, handler=handler))
    original = [event.model_dump_json() for event in events]

    for _ in range(2):
        assert replay(1, events).creation_history == [
            'Term 1 event (Merchant): You are given advanced training in a specialist field. '
            'Failed the EDU check (7 against 8+).'
        ]
        assert replay(1, events[:-1]).creation_history == [
            'Term 1 event (Merchant): You are given advanced training in a specialist field. '
            'In progress: Roll EDU 8+ to increase any one skill you already have by one level'
        ]
    assert [event.model_dump_json() for event in events] == original
