"""Betrayal choices and consequences through the character HTTP interface."""

from fastapi.testclient import TestClient
import pytest

from ceres.character.domain.career import ROGUE
from ceres.character.domain.career.career_events import CareerEntryHandler, SurviveHandler
from ceres.character.domain.character_start import BackgroundSkillsHandler, UcpHandler
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.connection_events import ConnectionNameHandler, ConnectionsRollHandler
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.service import CharacterService
from ceres.character.web.app import build_app
from tests.unit.character.helpers import MOCK_WORLD, _creation_events, create_backend


@pytest.fixture
def betrayal_client(tmp_path, request):
    events = _creation_events(VILANI, MOCK_WORLD)
    ucp = Event(fulfills=(events[-1].id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(
        fulfills=(ucp.id, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
    )
    entry = Event(
        fulfills=(background.id, 0),
        handler=CareerEntryHandler(career=ROGUE, assignment=ROGUE.assignment('Thief'), qualification_roll=6),
    )
    survive = Event(fulfills=(entry.id, 0), handler=SurviveHandler(roll=4))
    database = tmp_path / 'betrayal.sqlite'
    backend = create_backend(database)
    friends = []
    if getattr(request, 'param', False):
        for index, kind in enumerate([ConnectionKind.CONTACT, ConnectionKind.ALLY]):
            friends.extend(
                [
                    Event(handler=ConnectionsRollHandler(connection_type=kind, count=1, origin='Old friend')),
                    Event(
                        fulfills=f'connection_name_{index}',
                        handler=ConnectionNameHandler(
                            connection_index=index,
                            name=['Vessa Koh', 'Slim Slirk'][index],
                            note='Met at university',
                        ),
                    ),
                ]
            )
        friends[0].fulfills = (background.id, 0)
        entry.fulfills = None
    row = backend.start([*events, ucp, background], name='Rogue', player='NPC')
    for event in [*friends, entry, survive]:
        if isinstance(event.fulfills, tuple):
            projection = backend.get_projection(row['id'])
            assert projection is not None
            event.fulfills = projection.pending_inputs[0].pending_id
        backend.append_event(row['id'], event)
    backend.close()
    with CharacterService(database) as service, TestClient(build_app(service)) as client:
        yield client, f'/api/characters/{row["id"]}'


def choose(client, url, values):
    pending = client.get(url).json()['pending']
    response = client.post(url + '/choices', json={'fulfills': pending['id'], 'values': values})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize(('kind', 'roll'), [('rival', 7), ('enemy', 2)])
def test_unexpected_betrayer_has_relationship_choice_and_prison_roll(betrayal_client, kind, roll):
    client, url = betrayal_client
    view = choose(client, url, {'roll': '3'})
    assert view['problems'] == []
    assert sum('Betrayed by a friend.' in line for line in view['changes']) == 1
    inputs = view['pending']['inputs']
    relationship = next(spec for spec in inputs if spec['name'] == 'relationship')
    assert relationship['options'] == [['Rival', 'rival'], ['Enemy', 'enemy']]
    prison_roll = next(spec for spec in inputs if spec['name'] == 'roll')
    assert prison_roll['kind'] == 'NumberEntry'
    assert (prison_roll['min'], prison_roll['max']) == (2, 12)
    assert 'Prisoner' in prison_roll['label']
    name = next(spec for spec in inputs if spec['name'] == 'name')
    assert 'optional' in name['label'].lower()
    assert 'unknown' not in view['pending']['instruction'].lower()
    view = choose(client, url, {'relationship': kind, 'roll': str(roll), 'name': 'Vessa Koh'})
    assert any(line.startswith(f'{kind.title()}: Vessa Koh') for line in view['connections'])
    assert view['age'] == 22
    assert view['pending']['inputs'][0]['kind'] == 'CareerChoice'
    careers = [career['name'] for career in view['pending']['inputs'][0]['career_options']]
    assert (careers == ['Prisoner']) is (roll == 2)


@pytest.mark.parametrize('betrayal_client', [True], indirect=True)
def test_choose_existing_betrayer_preserves_identity_and_other_friends(betrayal_client):
    client, url = betrayal_client
    view = choose(client, url, {'roll': '3'})
    inputs = view['pending']['inputs']
    betrayer = next(spec for spec in inputs if spec['name'] == 'connection_index')
    assert betrayer['options'] == [['Contact: Vessa Koh', '0'], ['Ally: Slim Slirk', '1']]
    assert not any(spec['name'] == 'name' for spec in inputs)
    view = choose(client, url, {'connection_index': '0', 'relationship': 'enemy', 'roll': '7'})
    assert view['connections'] == [
        'Enemy: Vessa Koh — Met at university',
        'Ally: Slim Slirk — Met at university',
    ]


def test_unexpected_betrayer_name_can_be_left_blank(betrayal_client):
    client, url = betrayal_client
    choose(client, url, {'roll': '3'})
    view = choose(client, url, {'relationship': 'rival', 'roll': '12', 'name': ''})
    assert view['connections'] == ['Rival: An unexpected betrayer']
    assert view['pending']['inputs'][0]['kind'] == 'CareerChoice'
