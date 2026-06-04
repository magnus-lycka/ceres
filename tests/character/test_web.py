"""Integration tests for the character web UI routes."""

from fastapi.testclient import TestClient
import pytest

from ceres.character.app import build_app
from ceres.character.sophonts import HUMANITI, VILANI
from ceres.character.store import SqliteCharacterBackend
from ceres.worlds import DEFAULT_MILIEU, SectorWorldFilters
from tests.character.helpers import MOCK_WORLD, MOCK_WORLD_2


@pytest.fixture
def client():
    with SqliteCharacterBackend(':memory:') as backend:
        yield TestClient(build_app(backend), follow_redirects=True)


@pytest.fixture
def client_with_backend():
    with SqliteCharacterBackend(':memory:') as backend:
        yield TestClient(build_app(backend), follow_redirects=True), backend


# ── character list ────────────────────────────────────────────────────────────


def test_character_list_empty(client):
    r = client.get('/ui/')
    assert r.status_code == 200
    assert 'Characters' in r.text


def test_character_list_shows_characters(client_with_backend):
    client, backend = client_with_backend
    backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Aria')
    r = client.get('/ui/')
    assert r.status_code == 200
    assert 'Aria' in r.text
    assert 'Delete Selected' in r.text
    assert 'name="character_ids"' in r.text


# ── character creation ────────────────────────────────────────────────────────


def test_new_character_form(client):
    r = client.get('/ui/characters/new')
    assert r.status_code == 200
    assert 'New Character' in r.text
    assert 'Humaniti' in r.text
    assert 'Not selected' in r.text
    assert 'Choose Homeworld' in r.text
    assert 'formnovalidate' in r.text


def test_new_character_form_shows_selected_homeworld_from_query(client, monkeypatch):
    monkeypatch.setattr('ceres.character.web.routes.fetch_world', lambda sector, hex_code: MOCK_WORLD)

    r = client.get(
        '/ui/characters/new',
        params={'homeworld_sector': 'Troj', 'homeworld_hex': '2715', 'name': 'Ada', 'player': 'NPC'},
    )

    assert r.status_code == 200
    assert 'Hexx' in r.text
    assert 'Trojan Reach' in r.text
    assert 'value="2715"' in r.text
    assert 'value="Troj"' in r.text


def test_sector_picker_page_renders_search_input(client):
    r = client.get('/ui/worlds/sectors')
    assert r.status_code == 200
    assert 'Sector' in r.text
    assert 'sector-query' in r.text


def test_sector_search_returns_matching_options(client, monkeypatch):
    from ceres.adapters.travellermap import SectorInfo

    def fake_search(query: str, *, milieu: str = DEFAULT_MILIEU):
        assert query == 'tro'
        assert milieu == DEFAULT_MILIEU
        return [
            SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='Troj', tags='OTU', names=['Trojan Reach']),
            SectorInfo(x=1, y=0, milieu=DEFAULT_MILIEU, abbreviation='Vlan', tags='OTU', names=['The Trojans']),
        ]

    monkeypatch.setattr('ceres.character.web.routes.search_sectors', fake_search)

    r = client.get('/ui/worlds/sectors/search', params={'q': 'tro'})
    assert r.status_code == 200
    assert 'Trojan Reach' in r.text
    assert 'Troj' in r.text
    assert '/ui/worlds/sectors/Troj' in r.text


def test_sector_search_preserves_character_form_query(client, monkeypatch):
    from ceres.adapters.travellermap import SectorInfo

    monkeypatch.setattr(
        'ceres.character.web.routes.search_sectors',
        lambda query, milieu=DEFAULT_MILIEU: [
            SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='Troj', tags='OTU', names=['Trojan Reach'])
        ],
    )

    r = client.get(
        '/ui/worlds/sectors/search',
        params={'q': 'troj', 'name': 'Ada', 'player': 'NPC', 'sophont': 'Humaniti'},
    )
    assert r.status_code == 200
    assert '/ui/worlds/sectors/Troj?name=Ada&amp;sophont=Humaniti&amp;player=NPC' in r.text


def test_sector_search_blank_query_returns_empty_results(client):
    r = client.get('/ui/worlds/sectors/search', params={'q': ''})
    assert r.status_code == 200
    assert r.text.strip() == ''


def test_sector_search_without_abbreviation_is_not_selectable(client, monkeypatch):
    from ceres.adapters.travellermap import SectorInfo

    monkeypatch.setattr(
        'ceres.character.web.routes.search_sectors',
        lambda query, milieu=DEFAULT_MILIEU: [
            SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='', tags='OTU', names=['Aslan Hierate'])
        ],
    )

    r = client.get('/ui/worlds/sectors/search', params={'q': 'aslan'})
    assert r.status_code == 200
    assert 'Aslan Hierate' in r.text
    assert '/ui/worlds/sectors/' not in r.text


def test_sector_filter_page_renders_checkbox_options(client, monkeypatch):
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _sample_worlds

    monkeypatch.setattr(
        'ceres.character.web.routes.SectorWorldFilters.from_travellermap',
        lambda sector_abbreviation: SectorWorldFilters(
            worlds=_sample_worlds(),
            sector_abbreviation=sector_abbreviation,
            sector_name='Trojan Reach',
            allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
        ),
    )

    r = client.get('/ui/worlds/sectors/Troj')
    assert r.status_code == 200
    assert 'Trojan Reach' in r.text
    assert 'ImDd' in r.text
    assert 'Third Imperium, Domain of Deneb' in r.text
    assert 'Ni' in r.text
    assert 'name="allegiances"' in r.text
    assert 'name="remarks"' in r.text
    assert 'name="starports"' in r.text
    assert 'data-check-all' in r.text
    assert 'data-clear-all' in r.text
    assert 'checked' in r.text
    assert 'Apply Filters' in r.text
    assert 'Aster' in r.text
    assert 'Beryl' in r.text
    assert 'Cinder' in r.text
    assert 'Hex' in r.text
    assert 'Stellar' in r.text
    assert '{ 0 }' in r.text
    assert '(000+0)' in r.text
    assert '[0000]' in r.text
    assert '111' in r.text
    assert 'G2 V' in r.text
    assert 'Filter by world name or hex' in r.text
    assert 'Select' in r.text


def test_sector_filter_page_applies_query_filters_and_shows_matching_worlds(client, monkeypatch):
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _sample_worlds

    monkeypatch.setattr(
        'ceres.character.web.routes.SectorWorldFilters.from_travellermap',
        lambda sector_abbreviation: SectorWorldFilters(
            worlds=_sample_worlds(),
            sector_abbreviation=sector_abbreviation,
            sector_name='Trojan Reach',
            allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
        ),
    )

    r = client.get('/ui/worlds/sectors/Troj', params={'filters': '1', 'remarks': 'Ni'})
    assert r.status_code == 200
    assert '1 matching worlds' in r.text
    assert 'Beryl' in r.text
    assert 'Aster' not in r.text
    assert 'Cinder' not in r.text


def test_sector_filter_page_can_filter_by_world_name_or_hex(client, monkeypatch):
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _sample_worlds

    monkeypatch.setattr(
        'ceres.character.web.routes.SectorWorldFilters.from_travellermap',
        lambda sector_abbreviation: SectorWorldFilters(
            worlds=_sample_worlds(),
            sector_abbreviation=sector_abbreviation,
            sector_name='Trojan Reach',
            allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
        ),
    )

    by_name = client.get('/ui/worlds/sectors/Troj', params={'filters': '1', 'world_query': 'ber'})
    assert by_name.status_code == 200
    assert 'Beryl' in by_name.text
    assert 'Aster' not in by_name.text

    by_hex = client.get('/ui/worlds/sectors/Troj', params={'filters': '1', 'world_query': '0103'})
    assert by_hex.status_code == 200
    assert 'Cinder' in by_hex.text
    assert 'Aster' not in by_hex.text


def test_sector_filter_page_select_link_returns_to_new_character_form_with_world(client, monkeypatch):
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _sample_worlds

    monkeypatch.setattr(
        'ceres.character.web.routes.SectorWorldFilters.from_travellermap',
        lambda sector_abbreviation: SectorWorldFilters(
            worlds=_sample_worlds(),
            sector_abbreviation=sector_abbreviation,
            sector_name='Trojan Reach',
            allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
        ),
    )

    r = client.get('/ui/worlds/sectors/Troj', params={'name': 'Ada', 'player': 'NPC', 'sophont': 'Humaniti'})
    assert r.status_code == 200
    assert (
        '/ui/characters/new?name=Ada&amp;sophont=Humaniti&amp;player=NPC&homeworld_sector=Troj&homeworld_hex=0101'
    ) in r.text


def test_sector_filter_page_shows_no_allegiance_option_for_blank_allegiance_worlds(client, monkeypatch):
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _sample_worlds_with_unaligned

    monkeypatch.setattr(
        'ceres.character.web.routes.SectorWorldFilters.from_travellermap',
        lambda sector_abbreviation: SectorWorldFilters(
            worlds=_sample_worlds_with_unaligned(),
            sector_abbreviation=sector_abbreviation,
            sector_name='Trojan Reach',
            allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
        ),
    )

    r = client.get('/ui/worlds/sectors/Troj')
    assert r.status_code == 200
    assert 'No Allegiance' in r.text


def test_sector_filter_page_treats_all_checked_as_unconstrained(client, monkeypatch):
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _sample_worlds_with_unaligned

    worlds = _sample_worlds_with_unaligned()
    filters = SectorWorldFilters(
        worlds=worlds,
        sector_abbreviation='Troj',
        sector_name='Trojan Reach',
        allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
    )

    monkeypatch.setattr(
        'ceres.character.web.routes.SectorWorldFilters.from_travellermap',
        lambda sector_abbreviation: filters,
    )

    params = [('filters', '1')]
    params.extend(('allegiances', value) for value in filters.options.allegiances)
    params.extend(('remarks', value) for value in filters.options.remarks)
    params.extend(('bases', value) for value in filters.options.bases)
    params.extend(('starports', value) for value in filters.options.starports)
    params.extend(('sizes', str(value)) for value in filters.options.sizes)
    params.extend(('atmospheres', str(value)) for value in filters.options.atmospheres)
    params.extend(('hydrographics', str(value)) for value in filters.options.hydrographics)
    params.extend(('populations', str(value)) for value in filters.options.populations)
    params.extend(('governments', str(value)) for value in filters.options.governments)
    params.extend(('law_levels', str(value)) for value in filters.options.law_levels)
    params.extend(('tech_levels', str(value)) for value in filters.options.tech_levels)

    r = client.get('/ui/worlds/sectors/Troj', params=params)
    assert r.status_code == 200
    assert '4 matching worlds' in r.text
    assert 'Aster' in r.text
    assert 'Beryl' in r.text
    assert 'Cinder' in r.text
    assert 'Drift' in r.text


def test_sector_filter_page_prefills_reference_hex_from_current_homeworld(client_with_backend, monkeypatch):
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _entry

    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Ada')
    worlds = [
        _entry(name='Far', hex_code='2916', uwp='A867A99-D', bases='N', allegiance='ImDd', remarks='Hi In'),
        _entry(name='Near', hex_code='2614', uwp='C433567-A', bases='W', allegiance='ImAp', remarks='Ni Po'),
        _entry(name='Middle', hex_code='2715', uwp='E100200-7', bases='', allegiance='NaHu', remarks='Ba Va'),
    ]
    filters = SectorWorldFilters(
        worlds=worlds,
        sector_abbreviation='Troj',
        sector_name='Trojan Reach',
        allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
    )
    monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda _: filters)

    r = client.get('/ui/worlds/sectors/Troj', params={'character_id': row['id'], 'fulfills': '1.0'})
    assert r.status_code == 200
    assert 'name="reference_hex"' in r.text
    assert 'value="2715"' in r.text
    assert '>Dist<' in r.text

    ordered = sorted(worlds, key=lambda world: (filters.world_distance_parsecs('2715', world), world.hex, world.name))
    positions = [r.text.index(world.name) for world in ordered]
    assert positions == sorted(positions)


def test_sector_filter_page_sorts_by_manual_reference_hex(client, monkeypatch):
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _entry

    worlds = [
        _entry(name='Far', hex_code='2916', uwp='A867A99-D', bases='N', allegiance='ImDd', remarks='Hi In'),
        _entry(name='Near', hex_code='2614', uwp='C433567-A', bases='W', allegiance='ImAp', remarks='Ni Po'),
        _entry(name='Middle', hex_code='2715', uwp='E100200-7', bases='', allegiance='NaHu', remarks='Ba Va'),
    ]
    filters = SectorWorldFilters(
        worlds=worlds,
        sector_abbreviation='Troj',
        sector_name='Trojan Reach',
        allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
    )
    monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda _: filters)

    r = client.get('/ui/worlds/sectors/Troj', params={'reference_hex': '2513'})
    assert r.status_code == 200
    assert 'value="2513"' in r.text
    assert '>Dist<' in r.text
    assert '>2<' in r.text
    assert '>3<' in r.text
    assert '>5<' in r.text

    ordered = sorted(worlds, key=lambda world: (filters.world_distance_parsecs('2513', world), world.hex, world.name))
    positions = [r.text.index(world.name) for world in ordered]
    assert positions == sorted(positions)


def test_create_character_redirects_to_wizard(client):
    r = client.post(
        '/ui/characters/new',
        data={'name': 'Bob', 'sophont': 'Humaniti', 'player': 'NPC'},
        follow_redirects=False,
    )
    assert r.status_code == 422
    assert 'Homeworld is required' in r.text


def test_create_character_uses_selected_homeworld(client_with_backend, monkeypatch):
    client, backend = client_with_backend
    monkeypatch.setattr('ceres.character.web.routes.fetch_world', lambda sector, hex_code: MOCK_WORLD)

    r = client.post(
        '/ui/characters/new',
        data={
            'name': 'Bob',
            'sophont': 'Humaniti',
            'player': 'NPC',
            'homeworld_sector': 'Troj',
            'homeworld_hex': '2715',
        },
        follow_redirects=False,
    )

    assert r.status_code == 303
    projection = backend.get_projection(1)
    assert projection is not None
    assert projection.summary.homeworld.name == 'Hexx'
    assert projection.summary.homeworld.sector_abbreviation == 'Troj'


def test_create_character_blank_name_returns_form(client):
    r = client.post('/ui/characters/new', data={'name': '', 'sophont': 'Humaniti', 'player': 'NPC'})
    assert r.status_code == 422
    assert 'required' in r.text.lower()


# ── character deletion ───────────────────────────────────────────────────────


def test_delete_character_redirects_to_list(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Doomed')
    r = client.post(f'/ui/characters/{row["id"]}/delete')
    assert r.status_code == 200
    assert 'Doomed' not in r.text


def test_delete_character_removes_from_list(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Ephemeral')
    client.post(f'/ui/characters/{row["id"]}/delete')
    assert backend.get_projection(row['id']) is None


def test_bulk_delete_characters_removes_checked_rows(client_with_backend):
    client, backend = client_with_backend
    first = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='First')
    second = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Second')
    third = backend.start(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Third')

    r = client.post(
        '/ui/characters/delete',
        data={'character_ids': [str(first['id']), str(third['id'])]},
    )

    assert r.status_code == 200
    assert backend.get_projection(first['id']) is None
    assert backend.get_projection(third['id']) is None
    assert backend.get_projection(second['id']) is not None
    assert 'First' not in r.text
    assert 'Third' not in r.text
    assert 'Second' in r.text


def test_bulk_delete_with_no_selection_is_noop(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Still Here')

    r = client.post('/ui/characters/delete', data={})

    assert r.status_code == 200
    assert backend.get_projection(row['id']) is not None
    assert 'Still Here' in r.text


def test_delete_nonexistent_character_redirects(client):
    r = client.post('/ui/characters/9999/delete')
    assert r.status_code == 200


# ── wizard ────────────────────────────────────────────────────────────────────


def test_wizard_shows_ucp_pending(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Clio')
    r = client.get(f'/ui/characters/{row["id"]}/wizard')
    assert r.status_code == 200
    assert 'ucp' in r.text
    assert 'Humaniti' in r.text
    assert 'Hexx (Trojan Reach 2715)' in r.text
    assert 'Career(name=' not in r.text


def test_wizard_shows_career_name_not_repr(client_with_backend, monkeypatch):
    from ceres.character.careers.career_data import Career
    from ceres.character.state import CharacterProjection, CharacterSummary

    client, backend = client_with_backend
    monkeypatch.setattr(
        backend,
        'get_projection',
        lambda character_id: CharacterProjection(
            character_id=character_id,
            summary=CharacterSummary(
                name='Clio',
                age=30,
                sophont=HUMANITI,
                homeworld=MOCK_WORLD,
                current_career=Career(
                    name='Citizen',
                    source='Core',
                    description=(
                        'Individuals serving in a corporation, bureaucracy or industry, '
                        'or who are making a new life on an untamed planet.'
                    ),
                ),
                current_assignment='Colonist',
                rank=3,
                term_count=3,
            ),
        ),
    )

    r = client.get('/ui/characters/1/wizard')
    assert r.status_code == 200
    assert 'Citizen' in r.text
    assert '(Colonist)' in r.text
    assert 'Rank 3' in r.text
    assert '3 terms' in r.text
    assert 'Age 30' in r.text
    assert 'Career(name=' not in r.text


def test_wizard_404_for_missing_character(client):
    r = client.get('/ui/characters/9999/wizard')
    assert r.status_code == 404


def test_wizard_homeworld_change_pending_links_to_sector_picker(client_with_backend):
    from ceres.character.events import (
        BackgroundSkillsEvent,
        FinishCreationEvent,
        HomeworldChangeRequiredEvent,
        UcpEvent,
    )
    from ceres.character.skills import Admin, Athletics, Carouse, Drive

    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Clio')
    backend.append_event(row['id'], UcpEvent(fulfills='1.0', ucp='7869A5'))
    backend.append_event(
        row['id'],
        BackgroundSkillsEvent(fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    backend.append_event(row['id'], FinishCreationEvent(fulfills='3.0'))
    backend.append_event(
        row['id'],
        HomeworldChangeRequiredEvent(
            reason='Citizen mishap 5: forcing you to leave the planet.',
            source_kind='career_mishap',
            source_career='Citizen',
        ),
    )

    r = client.get(f'/ui/characters/{row["id"]}/wizard')
    assert r.status_code == 200
    assert 'Choose New Homeworld' in r.text
    assert f'/ui/worlds/sectors?character_id={row["id"]}&fulfills=5.0' in r.text


def test_selecting_homeworld_from_wizard_picker_updates_character(client_with_backend, monkeypatch):
    from ceres.character.events import (
        BackgroundSkillsEvent,
        FinishCreationEvent,
        HomeworldChangeRequiredEvent,
        UcpEvent,
    )
    from ceres.character.skills import Admin, Athletics, Carouse, Drive
    from tests.worlds.test_sector_filters import _sample_worlds

    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Clio')
    backend.append_event(row['id'], UcpEvent(fulfills='1.0', ucp='7869A5'))
    backend.append_event(
        row['id'],
        BackgroundSkillsEvent(fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    backend.append_event(row['id'], FinishCreationEvent(fulfills='3.0'))
    backend.append_event(
        row['id'],
        HomeworldChangeRequiredEvent(
            reason='Citizen mishap 5: forcing you to leave the planet.',
            source_kind='career_mishap',
            source_career='Citizen',
        ),
    )

    sample_worlds = _sample_worlds()
    monkeypatch.setattr(
        'ceres.character.web.routes.SectorWorldFilters.from_travellermap',
        lambda sector_abbreviation: SectorWorldFilters(
            worlds=sample_worlds,
            sector_abbreviation=sector_abbreviation,
            sector_name='Trojan Reach',
            allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
        ),
    )
    monkeypatch.setattr('ceres.adapters.travellermap.fetch_world', lambda sector, hex_code: MOCK_WORLD_2)

    sector_page = client.get('/ui/worlds/sectors/Troj', params={'character_id': row['id'], 'fulfills': '5.0'})
    assert sector_page.status_code == 200
    assert f'action="/ui/characters/{row["id"]}/homeworld"' in sector_page.text

    r = client.post(
        f'/ui/characters/{row["id"]}/homeworld',
        data={'fulfills': '5.0', 'sector': 'Troj', 'hex_code': '0103'},
    )
    assert r.status_code == 200

    projection = backend.get_projection(row['id'])
    assert projection is not None
    assert projection.summary.homeworld == MOCK_WORLD_2
    assert not any(p.kind == 'homeworld_change_required' for p in projection.pending_inputs)


# ── event submission (HTMX) ───────────────────────────────────────────────────


def test_submit_ucp_event(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Drax')
    cid = row['id']
    projection = backend.get_projection(cid)
    assert projection is not None
    pi = projection.pending_inputs[0]
    assert pi.kind == 'ucp'

    r = client.post(
        f'/ui/characters/{cid}/events',
        data={
            'kind': 'ucp',
            'fulfills': pi.id,
            'STR': '7',
            'DEX': '7',
            'END': '7',
            'INT': '7',
            'EDU': '7',
            'SOC': '7',
        },
    )
    assert r.status_code == 200
    # Should now show background_skills pending
    assert 'background_skills' in r.text or 'background' in r.text.lower()


def test_submit_nonexistent_fulfills_shows_error(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Eryn')
    r = client.post(
        f'/ui/characters/{row["id"]}/events',
        data={'fulfills': 'nonexistent.999'},
    )
    assert r.status_code == 200
    assert 'error' in r.text.lower() or 'nonexistent' in r.text.lower()


# ── character sheet ───────────────────────────────────────────────────────────


def test_character_sheet_shows_name(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Fyra')
    r = client.get(f'/ui/characters/{row["id"]}')
    assert r.status_code == 200
    assert 'Fyra' in r.text
    assert 'Humaniti' in r.text
    assert 'Hexx (Trojan Reach 2715)' in r.text
    assert '>?\n' not in r.text
    assert 'Career(name=' not in r.text


def test_character_sheet_shows_career_name_not_repr(client_with_backend, monkeypatch):
    from ceres.character.careers.career_data import Career
    from ceres.character.state import CharacterProjection, CharacterSummary

    client, backend = client_with_backend
    monkeypatch.setattr(
        backend,
        'get_projection',
        lambda character_id: CharacterProjection(
            character_id=character_id,
            summary=CharacterSummary(
                name='Fyra',
                age=30,
                sophont=HUMANITI,
                homeworld=MOCK_WORLD,
                current_career=Career(
                    name='Citizen',
                    source='Core',
                    description=(
                        'Individuals serving in a corporation, bureaucracy or industry, '
                        'or who are making a new life on an untamed planet.'
                    ),
                ),
                current_assignment='Colonist',
                rank=3,
                term_count=3,
            ),
        ),
    )

    r = client.get('/ui/characters/1')
    assert r.status_code == 200
    assert 'Citizen' in r.text
    assert '(Colonist)' in r.text
    assert 'Rank 3' in r.text
    assert '3 terms' in r.text
    assert 'Age 30' in r.text
    assert 'Career(name=' not in r.text


def test_character_sheet_404(client):
    r = client.get('/ui/characters/9999')
    assert r.status_code == 404


# ── career assignments endpoint ───────────────────────────────────────────────


def test_career_assignments_returns_html(client):
    r = client.get('/ui/careers/Scout/assignments')
    assert r.status_code == 200
    assert 'Courier' in r.text or 'option' in r.text.lower()


def test_career_assignments_unknown_career(client):
    r = client.get('/ui/careers/NonexistentCareer/assignments')
    assert r.status_code == 200
    assert r.text == ''


# ── event_from_form unit tests ────────────────────────────────────────────────


def test_event_from_form_ucp():
    from starlette.datastructures import FormData

    from ceres.character.events import PendingUcp, UcpEvent

    pi = PendingUcp(id='1.0', instruction='')
    form = FormData({'STR': '7', 'DEX': '8', 'END': '6', 'INT': '9', 'EDU': '10', 'SOC': '5'})
    event = pi.event_from_form(form)
    assert isinstance(event, UcpEvent)
    assert event.ucp == '7869A5'
    assert event.fulfills == '1.0'


def test_event_from_form_career_choice():
    from starlette.datastructures import FormData

    from ceres.character.events import CareerEvent, PendingCareerChoice

    pi = PendingCareerChoice(id='3.0', instruction='')
    form = FormData({'career': 'Scout', 'assignment': 'Courier', 'roll': '8'})
    event = pi.event_from_form(form)
    assert isinstance(event, CareerEvent)
    assert event.career == 'Scout'
    assert event.assignment == 'Courier'
    assert event.qualification_roll == 8


def test_event_from_form_career_choice_missing_assignment_raises():
    from starlette.datastructures import FormData

    from ceres.character.events import PendingCareerChoice

    pi = PendingCareerChoice(id='3.0', instruction='')
    form = FormData({'career': 'Citizen', 'assignment': '', 'roll': '8'})
    with pytest.raises(ValueError, match="Missing assignment for career 'Citizen'"):
        pi.event_from_form(form)


def test_event_from_form_reenlist_true():
    from starlette.datastructures import FormData

    from ceres.character.events import PendingReenlist, ReenlistEvent

    pi = PendingReenlist(id='5.1', instruction='')
    form = FormData({'reenlist': 'true'})
    event = pi.event_from_form(form)
    assert isinstance(event, ReenlistEvent)
    assert event.reenlist is True


def test_event_from_form_reenlist_false():
    from starlette.datastructures import FormData

    from ceres.character.events import PendingReenlist, ReenlistEvent

    pi = PendingReenlist(id='5.1', instruction='')
    form = FormData({'reenlist': 'false'})
    event = pi.event_from_form(form)
    assert isinstance(event, ReenlistEvent)
    assert event.reenlist is False


def test_build_event_unknown_raises():
    from starlette.datastructures import FormData

    from ceres.character.state import CharacterProjection, CharacterSummary
    from ceres.character.web.routes import _build_event_from_form

    projection = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    form = FormData({})
    with pytest.raises(ValueError):
        _build_event_from_form('nonexistent.0', form, projection)


# ── _diff_summaries unit tests ────────────────────────────────────────────────


def _make_summary(**kwargs):
    from ceres.character.state import CharacterSummary

    kwargs.setdefault('name', 'Test')
    kwargs.setdefault('sophont', VILANI)
    kwargs.setdefault('homeworld', MOCK_WORLD)
    return CharacterSummary(**kwargs)


def test_diff_shows_characteristic_change():
    from ceres.character.characteristics import Chars
    from ceres.character.state import diff_summaries as _diff_summaries

    before = _make_summary(characteristics={Chars.STR: 7, Chars.DEX: 8})
    after = _make_summary(characteristics={Chars.STR: 8, Chars.DEX: 8})
    changes = _diff_summaries(before, after)
    assert any('STR' in c and '7' in c and '8' in c for c in changes)


def test_diff_shows_new_skill():
    from ceres.character.skills import Admin
    from ceres.character.state import diff_summaries as _diff_summaries

    before = _make_summary()
    after = _make_summary(skills=[Admin()])
    changes = _diff_summaries(before, after)
    assert any('Admin' in c for c in changes)


def test_diff_shows_skill_level_up():
    from ceres.character.skills import Admin, Level
    from ceres.character.state import diff_summaries as _diff_summaries

    before = _make_summary(skills=[Admin()])
    after = _make_summary(skills=[Admin(level=Level(value=1))])
    changes = _diff_summaries(before, after)
    assert any('Admin' in c and '0' in c and '1' in c for c in changes)


def test_diff_shows_rank_change():
    from ceres.character.state import diff_summaries as _diff_summaries

    before = _make_summary(rank=0)
    after = _make_summary(rank=1)
    changes = _diff_summaries(before, after)
    assert any('Rank' in c and '1' in c for c in changes)


def test_diff_shows_cash_gain():
    from ceres.character.state import diff_summaries as _diff_summaries

    before = _make_summary(cash=0)
    after = _make_summary(cash=5000)
    changes = _diff_summaries(before, after)
    assert any('5000' in c or '5,000' in c for c in changes)


def test_diff_shows_new_narrative():
    from ceres.character.state import diff_summaries as _diff_summaries

    before = _make_summary(narrative=['Term 1'])
    after = _make_summary(narrative=['Term 1', 'Survived the storm'])
    changes = _diff_summaries(before, after)
    assert any('Survived the storm' in c for c in changes)


def test_diff_empty_when_nothing_changed():
    from ceres.character.state import diff_summaries as _diff_summaries

    s = _make_summary(characteristics={}, skills=[])
    assert _diff_summaries(s, s) == []


def test_post_event_response_includes_char_summary_oob(client_with_backend):
    """HTMX response should include an OOB char-summary div after event submission."""
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Oryn')
    cid = row['id']
    projection = backend.get_projection(cid)
    assert projection is not None
    pi = projection.pending_inputs[0]
    r = client.post(
        f'/ui/characters/{cid}/events',
        data={
            'kind': 'ucp',
            'fulfills': pi.id,
            'STR': '7',
            'DEX': '8',
            'END': '6',
            'INT': '9',
            'EDU': '10',
            'SOC': '5',
        },
    )
    assert r.status_code == 200
    assert 'char-summary' in r.text


# ── connection_type_from_instruction ─────────────────────────────────────────
