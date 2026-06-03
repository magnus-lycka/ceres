"""Replay integrity tests.

For each configuration: generate a character (no fixed seed), save the projection,
reload the event log, replay it, and assert the result is byte-for-byte identical.

The event log must capture 100% of choices. Replay must be fully deterministic.
"""

import pytest

from ceres.character.replay import replay
from ceres.character.store import SqliteCharacterBackend
from ceres.character.web.bulk import CohortParams, generate_npc

CONFIGS = [
    ('Army', 'Support', 1, 3),
    ('Army', 'Infantry', 2, 4),
    ('Army', 'Cavalry', 1, 2),
    ('Navy', 'Line/Crew', 2, 4),
    ('Navy', 'Flight', 1, 3),
    ('Marines', 'Ground Assault', 1, 3),
    ('Scout', 'Courier', 2, 4),
    ('Scout', 'Surveyor', 1, 3),
    ('Merchant', 'Merchant Marine', 2, 4),
    ('Agent', 'Law Enforcement', 1, 3),
    ('Rogue', 'Thief', 1, 3),
    ('Rogue', 'Pirate', 2, 4),
    ('Drifter', 'Barbarian', 1, 3),
    ('Drifter', 'Wanderer', 2, 4),
    ('Noble', 'Administrator', 1, 3),
    ('Citizen', 'Corporate', 2, 4),
    ('Entertainer', 'Performer', 1, 3),
    ('Scholar', 'Physician', 1, 3),
    ('Prisoner', 'Thug', 1, 2),
]


# Run each config 3 times to catch non-determinism in mishap/life-event branches
@pytest.mark.parametrize('career,assignment,min_t,max_t', CONFIGS)
@pytest.mark.parametrize('run', [1, 2, 3])
def test_replay_is_identical_to_original(career, assignment, min_t, max_t, run):
    backend = SqliteCharacterBackend(':memory:')
    try:
        generate_npc(
            backend,
            CohortParams(
                career=career,
                assignment=assignment,
                sophont='Humaniti',
                min_terms=min_t,
                max_terms=max_t,
                name_prefix='T',
            ),
            name=f'{career} {assignment}',
        )
        original = backend.get_projection(1)
        events = backend.load_typed_events(1)

        assert original is not None, 'generation produced no projection'
        assert events is not None and len(events) > 1, 'event log is empty'

        rebuilt = replay(1, events)
        orig_dump = original.model_dump(mode='json')
        rebuilt_dump = rebuilt.model_dump(mode='json')

        assert orig_dump == rebuilt_dump, (
            f'{career}/{assignment} run={run}: replay diverged\n'
            f'term_count: orig={orig_dump["summary"]["term_count"]} '
            f'rebuilt={rebuilt_dump["summary"]["term_count"]}\n'
            f'orig skills:    {[s["type"] for s in orig_dump["summary"]["skills"]]}\n'
            f'rebuilt skills: {[s["type"] for s in rebuilt_dump["summary"]["skills"]]}'
        )
    finally:
        backend.close()
