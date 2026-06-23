"""Integration tests for the character web UI routes."""

from html import unescape
import re
from typing import Any, Literal

from fastapi.testclient import TestClient
import pytest

from ceres.character.domain.career import CITIZEN, SCOUT
from ceres.character.domain.career.career_events import CareerEntryHandler, ReenlistHandler
from ceres.character.domain.character_start import (
    BackgroundSkillsHandler,
    FinishCreationHandler,
    PendingUcp,
    UcpHandler,
)
from ceres.character.domain.homeworld.homeworld_events import (
    HomeworldChangeRequiredHandler,
    PendingHomeworldChangeRequired,
)
from ceres.character.domain.sophont import HUMANITI, VILANI
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.store import SqliteCharacterBackend
from ceres.character.web.app import build_app
from ceres.worlds import DEFAULT_MILIEU, SectorWorldFilters
from tests.character.helpers import MOCK_WORLD, MOCK_WORLD_2


def _append_pending_event(
    backend: SqliteCharacterBackend,
    character_id: int,
    handler: Any,
    pending_type: type | None = None,
) -> Event:
    projection = backend.get_projection(character_id)
    assert projection is not None
    pending = next(
        (p for p in projection.pending_inputs if pending_type is None or isinstance(p, pending_type)),
        None,
    )
    assert pending is not None
    return backend.append_event(character_id, Event(fulfills=pending.pending_id, handler=handler))


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


def test_character_list_shows_ucp_latest_career_and_rank(client_with_backend, monkeypatch):
    from ceres.character.domain.career.career_data import CareerTerm
    from ceres.character.domain.character_state import CharacterSummary
    from ceres.character.domain.characteristics import Chars

    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Aria')
    citizen = CITIZEN
    assignment = citizen.assignment('Colonist')
    assert assignment is not None
    monkeypatch.setattr(
        backend,
        'get_summary',
        lambda character_id: CharacterSummary(
            name='Aria',
            sophont=HUMANITI,
            homeworld=MOCK_WORLD,
            characteristics={
                Chars.STR: 8,
                Chars.DEX: 9,
                Chars.END: 10,
                Chars.INT: 6,
                Chars.EDU: 7,
                Chars.SOC: 11,
            },
            rank=3,
            career_terms=[CareerTerm(career=citizen, assignment=assignment)],
        ),
    )

    r = client.get('/ui/')

    assert r.status_code == 200
    assert '89A67B' in r.text
    assert 'Citizen' in r.text
    assert '3 · Settler' in r.text
    assert 'Rank 3' not in r.text
    assert f'/ui/characters/{row["id"]}' in r.text


def test_character_list_shows_last_career_after_leaving_it(client_with_backend, monkeypatch):
    from ceres.character.domain.character_state import CharacterSummary

    client, backend = client_with_backend
    backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Retired')
    scout = SCOUT
    monkeypatch.setattr(
        backend,
        'get_summary',
        lambda character_id: CharacterSummary(
            name='Retired',
            sophont=HUMANITI,
            homeworld=MOCK_WORLD,
            last_career=scout,
            rank=2,
        ),
    )

    r = client.get('/ui/')

    assert 'Scout' in r.text
    assert re.search(r'>\s*2\s*<', r.text)
    assert 'Rank 2' not in r.text


def test_character_list_reads_stored_summaries_without_replaying(client_with_backend, monkeypatch):
    client, backend = client_with_backend
    backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Stored')
    monkeypatch.setattr(
        backend,
        'get_projection',
        lambda character_id: pytest.fail('Character list must not replay event logs'),
    )

    r = client.get('/ui/')

    assert r.status_code == 200
    assert 'Stored' in r.text


def test_character_list_reads_updated_persisted_summary(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Stored')
    _append_pending_event(backend, row['id'], UcpHandler(ucp='89A67B'), PendingUcp)

    r = client.get('/ui/')

    assert '89A67B' in r.text


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


def test_sector_search_preserves_world_filter_query(client, monkeypatch):
    from ceres.adapters.travellermap import SectorInfo

    monkeypatch.setattr(
        'ceres.character.web.routes.search_sectors',
        lambda query, milieu=DEFAULT_MILIEU: [
            SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='Troj', tags='OTU', names=['Trojan Reach'])
        ],
    )

    r = client.get(
        '/ui/worlds/sectors/search',
        params=[
            ('q', 'troj'),
            ('character_id', '7'),
            ('fulfills', '12.0'),
            ('reference_sector', 'Troj'),
            ('reference_hex', '2513'),
            ('filters', '1'),
            ('bases', 'S'),
            ('bases', 'W'),
            ('tech_levels', '8'),
            ('tech_levels', 'A'),
        ],
    )

    assert r.status_code == 200
    link = unescape(r.text)
    assert '/ui/worlds/sectors/Troj?' in link
    assert 'character_id=7' in link
    assert 'fulfills=12.0' in link
    assert 'reference_sector=Troj' in link
    assert 'reference_hex=2513' in link
    assert 'filters=1' in link
    assert 'bases=S' in link
    assert 'bases=W' in link
    assert 'tech_levels=8' in link
    assert 'tech_levels=A' in link


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


def test_sector_filter_page_sorts_by_reference_hex_in_another_sector(client, monkeypatch):
    from ceres.adapters.travellermap import SectorInfo
    from ceres.worlds import SectorWorldFilters
    from tests.worlds.test_sector_filters import _entry

    worlds = [
        _entry(name='Further', hex_code='0301', uwp='C433567-A', bases='W', allegiance='ImAp', remarks='Ni Po'),
        _entry(name='Border', hex_code='0101', uwp='A867A99-D', bases='N', allegiance='ImDd', remarks='Hi In'),
    ]
    filters = SectorWorldFilters(
        worlds=worlds,
        sector_abbreviation='Dene',
        sector_name='Deneb',
        sector_x=1,
        sector_y=0,
        allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
    )
    monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda _: filters)
    monkeypatch.setattr(
        'ceres.character.web.routes.search_sectors',
        lambda query, milieu=DEFAULT_MILIEU: [
            SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='Troj', tags='OTU', names=['Trojan Reach'])
        ],
    )

    r = client.get('/ui/worlds/sectors/Dene', params={'reference_sector': 'Troj', 'reference_hex': '3201'})

    assert r.status_code == 200
    assert 'name="reference_sector" value="Troj"' in r.text
    assert '>1<' in r.text
    assert '>3<' in r.text
    assert r.text.index('Border') < r.text.index('Further')


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
    assert 'UCP' in r.text
    assert 'Humaniti' in r.text
    assert 'Hexx (Trojan Reach 2715)' in r.text
    assert 'Career(name=' not in r.text


def test_wizard_shows_career_name_not_repr(client_with_backend, monkeypatch):
    from ceres.character.domain.career.career_data import AssignmentData, CareerTerm
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary

    client, backend = client_with_backend
    citizen = CITIZEN
    _colonist = citizen.assignment('Colonist')
    assert _colonist is not None
    colonist: AssignmentData = _colonist
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
                rank=3,
                career_terms=[
                    CareerTerm(
                        career=citizen,
                        assignment=colonist,
                    )
                    for _ in range(3)
                ],
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
    from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive

    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Clio')
    _append_pending_event(backend, row['id'], UcpHandler(ucp='7869A5'), PendingUcp)
    _append_pending_event(
        backend,
        row['id'],
        BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    _append_pending_event(backend, row['id'], FinishCreationHandler())
    backend.append_event(
        row['id'],
        Event(
            handler=HomeworldChangeRequiredHandler(
                reason='Citizen mishap 5: forcing you to leave the planet.',
                source_kind='career_mishap',
                source_career='Citizen',
            )
        ),
    )

    r = client.get(f'/ui/characters/{row["id"]}/wizard')
    assert r.status_code == 200
    assert 'Choose New Homeworld' in r.text
    assert (
        f'/ui/worlds/sectors/Troj?character_id={row["id"]}&fulfills=5.0&reference_sector=Troj&reference_hex=2715'
        in r.text
    )


def test_wizard_select_world_input_links_to_filtered_sector_picker(client_with_backend, monkeypatch):
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.input_specs import SelectWorld, WorldFilterCriteria, WorldRef
    from ceres.character.mechanism.pending_input import PendingInputBase

    class PendingWorldSelection(PendingInputBase):
        kind: Literal['test_world_selection'] = 'test_world_selection'

        def event_from_form(self, form: Any) -> Any:
            raise NotImplementedError

        def input_specs(self, projection: CharacterProjection):
            return [
                SelectWorld(
                    name='homeworld',
                    label='Choose Scout world',
                    sector_abbreviation='Troj',
                    reference_world=WorldRef(sector_abbreviation='Troj', hex='2513'),
                    filters=WorldFilterCriteria(
                        bases=('S', 'W'),
                        tech_levels=('8', '9', 'A', 'B', 'C'),
                    ),
                )
            ]

    client, backend = client_with_backend
    monkeypatch.setattr(
        backend,
        'get_projection',
        lambda character_id: CharacterProjection(
            character_id=character_id,
            summary=CharacterSummary(name='Clio', sophont=HUMANITI, homeworld=MOCK_WORLD),
            pending_inputs=[
                PendingWorldSelection(
                    pending_id=(12, 0),
                    instruction='Pick a suitable world',
                )
            ],
        ),
    )

    r = client.get('/ui/characters/7/wizard')

    assert r.status_code == 200
    page = unescape(r.text)
    assert 'Choose Scout world' in page
    assert '/ui/worlds/sectors/Troj?' in page
    assert 'character_id=7' in page
    assert 'fulfills=12.0' in page
    assert 'reference_sector=Troj' in page
    assert 'reference_hex=2513' in page
    assert 'filters=1' in page
    assert 'bases=S' in page
    assert 'bases=W' in page
    assert 'tech_levels=8' in page
    assert 'tech_levels=A' in page


def test_selecting_homeworld_from_wizard_picker_updates_character(client_with_backend, monkeypatch):
    from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive
    from tests.worlds.test_sector_filters import _sample_worlds

    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Clio')
    _append_pending_event(backend, row['id'], UcpHandler(ucp='7869A5'), PendingUcp)
    _append_pending_event(
        backend,
        row['id'],
        BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    _append_pending_event(backend, row['id'], FinishCreationHandler())
    backend.append_event(
        row['id'],
        Event(
            handler=HomeworldChangeRequiredHandler(
                reason='Citizen mishap 5: forcing you to leave the planet.',
                source_kind='career_mishap',
                source_career='Citizen',
            )
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
    monkeypatch.setattr(
        'ceres.character.domain.homeworld.homeworld_events.fetch_world', lambda sector, hex_code: MOCK_WORLD_2
    )

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
    assert not any(isinstance(p, PendingHomeworldChangeRequired) for p in projection.pending_inputs)


# ── event submission (HTMX) ───────────────────────────────────────────────────


def test_submit_ucp_event(client_with_backend):
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Drax')
    cid = row['id']
    projection = backend.get_projection(cid)
    assert projection is not None
    pi = projection.pending_inputs[0]
    assert isinstance(pi, PendingUcp)

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
    assert 'background' in r.text.lower()


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
    from ceres.character.domain.career.career_data import AssignmentData, CareerTerm
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary

    client, backend = client_with_backend
    citizen = CITIZEN
    _colonist = citizen.assignment('Colonist')
    assert _colonist is not None
    colonist: AssignmentData = _colonist
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
                rank=3,
                career_terms=[
                    CareerTerm(
                        career=citizen,
                        assignment=colonist,
                    )
                    for _ in range(3)
                ],
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


def test_choose_career_shows_career_qualification_and_assignment_descriptions(client_with_backend):
    from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive

    client, backend = client_with_backend
    character_id = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Aria')['id']
    _append_pending_event(backend, character_id, UcpHandler(ucp='7869A5'), PendingUcp)
    _append_pending_event(
        backend,
        character_id,
        BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )

    r = client.get(f'/ui/characters/{character_id}/wizard')

    assert r.status_code == 200
    assert 'Members of the exploratory service.' in r.text
    assert 'INT 5+' in r.text
    assert 'You are responsible for shuttling messages and high value packages around the galaxy.' in r.text
    assert '/ui/careers/' not in r.text


# ── event_from_form unit tests ────────────────────────────────────────────────


def test_event_from_form_ucp():
    from ceres.character.domain.character_start import PendingUcp

    pi = PendingUcp(pending_id=(1, 0), instruction='')
    event = pi.event_from_form({'STR': '7', 'DEX': '8', 'END': '6', 'INT': '9', 'EDU': '10', 'SOC': '5'})
    assert isinstance(event.handler, UcpHandler)
    assert event.ucp == '7869A5'
    assert event.fulfills == (1, 0)


def test_event_from_form_career_choice():
    from ceres.character.domain.career import SCOUT
    from ceres.character.domain.career.career_events import PendingCareerChoice

    pi = PendingCareerChoice(pending_id=(3, 0), instruction='', options=[SCOUT])
    event = pi.event_from_form({'career': 'Scout', 'assignment': 'Courier', 'roll': '8'})
    assert isinstance(event.handler, CareerEntryHandler)
    assert event.career.name == 'Scout'
    assert event.assignment.name == 'Courier'
    assert event.qualification_roll == 8


def test_event_from_form_career_choice_missing_assignment_raises():
    from ceres.character.domain.career import CITIZEN
    from ceres.character.domain.career.career_events import PendingCareerChoice

    pi = PendingCareerChoice(pending_id=(3, 0), instruction='', options=[CITIZEN])
    with pytest.raises(ReplayError, match='Unknown assignment'):
        pi.event_from_form({'career': 'Citizen', 'assignment': '', 'roll': '8'})


def test_event_from_form_reenlist_true():
    from ceres.character.domain.career.career_events import PendingReenlist

    pi = PendingReenlist(pending_id=(5, 1), instruction='')
    event = pi.event_from_form({'reenlist': 'true'})
    assert isinstance(event.handler, ReenlistHandler)
    assert event.reenlist is True


def test_event_from_form_reenlist_false():
    from ceres.character.domain.career.career_events import PendingReenlist

    pi = PendingReenlist(pending_id=(5, 1), instruction='')
    event = pi.event_from_form({'reenlist': 'false'})
    assert isinstance(event.handler, ReenlistHandler)
    assert event.reenlist is False


def test_build_event_unknown_raises():
    from starlette.datastructures import FormData

    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
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
    from ceres.character.domain.character_state import CharacterSummary

    kwargs.setdefault('name', 'Test')
    kwargs.setdefault('sophont', VILANI)
    kwargs.setdefault('homeworld', MOCK_WORLD)
    return CharacterSummary(**kwargs)


def test_diff_shows_characteristic_change():
    from ceres.character.domain.character_state import diff_summaries as _diff_summaries
    from ceres.character.domain.characteristics import Chars

    before = _make_summary(characteristics={Chars.STR: 7, Chars.DEX: 8})
    after = _make_summary(characteristics={Chars.STR: 8, Chars.DEX: 8})
    changes = _diff_summaries(before, after)
    assert any('STR' in c and '7' in c and '8' in c for c in changes)


def test_diff_shows_new_skill():
    from ceres.character.domain.character_state import diff_summaries as _diff_summaries
    from ceres.character.domain.skills import Admin

    before = _make_summary()
    after = _make_summary(skills=[Admin()])
    changes = _diff_summaries(before, after)
    assert any('Admin' in c for c in changes)


def test_diff_shows_skill_level_up():
    from ceres.character.domain.character_state import diff_summaries as _diff_summaries
    from ceres.character.domain.skills import Admin, Level

    before = _make_summary(skills=[Admin()])
    after = _make_summary(skills=[Admin(level=Level(value=1))])
    changes = _diff_summaries(before, after)
    assert any('Admin' in c and '0' in c and '1' in c for c in changes)


def test_diff_shows_rank_change():
    from ceres.character.domain.character_state import diff_summaries as _diff_summaries

    before = _make_summary(rank=0)
    after = _make_summary(rank=1)
    changes = _diff_summaries(before, after)
    assert any('Rank' in c and '1' in c for c in changes)


def test_diff_shows_cash_gain():
    from ceres.character.domain.character_state import diff_summaries as _diff_summaries

    before = _make_summary(cash=0)
    after = _make_summary(cash=5000)
    changes = _diff_summaries(before, after)
    assert any('5000' in c or '5,000' in c for c in changes)


def test_diff_shows_new_narrative():
    from ceres.character.domain.character_state import diff_summaries as _diff_summaries

    before = _make_summary(narrative=['Term 1'])
    after = _make_summary(narrative=['Term 1', 'Survived the storm'])
    changes = _diff_summaries(before, after)
    assert any('Survived the storm' in c for c in changes)


def test_diff_empty_when_nothing_changed():
    from ceres.character.domain.character_state import diff_summaries as _diff_summaries

    s = _make_summary(characteristics={}, skills=[])
    assert _diff_summaries(s, s) == []


def test_post_event_response_updates_all_summary_displays_oob(client_with_backend):
    """HTMX response should update both the page header and detailed summary."""
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
    assert 'id="wizard-header"' in r.text
    assert 'id="char-summary"' in r.text
    assert r.text.count('hx-swap-oob="true"') == 2


# ── connection_type_from_instruction ─────────────────────────────────────────
