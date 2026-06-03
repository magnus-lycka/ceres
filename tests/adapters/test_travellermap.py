import pytest

from ceres.adapters import travellermap
from ceres.adapters.travellermap import (
    SectorInfo,
    SectorWorldEntry,
    TravellerMapWorld,
    _extract,
    _parse_column_positions,
    _parse_sec_worlds,
    clear_travellermap_cache,
    fetch_sector,
    fetch_sector_worlds,
    fetch_sectors,
    fetch_world,
)

_SAMPLE_WORLD_JSON = {
    'Name': 'Hexx',
    'Hex': '2715',
    'UWP': 'B78A577-D',
    'PBG': '314',
    'Zone': '',
    'Bases': 'N',
    'Allegiance': 'ImDd',
    'Stellar': 'F6 V',
    'SS': 'H',
    'Ix': '{ 1 }',
    'Ex': '(C45+1)',
    'Cx': '[565D]',
    'Nobility': 'Bc',
    'Worlds': 11,
    'ResourceUnits': 240,
    'Subsector': 7,
    'Quadrant': 1,
    'WorldX': -102,
    'WorldY': -25,
    'Remarks': 'Ni Wa Pr Ht',
    'LegacyBaseCode': 'N',
    'Sector': 'Trojan Reach',
    'SubsectorName': 'Tobia',
    'SectorAbbreviation': 'Troj',
    'AllegianceName': 'Third Imperium, Domain of Deneb',
}

_SAMPLE_SECTOR_JSON = {
    'X': -7,
    'Y': -8,
    'Milieu': 'M1105',
    'Abbreviation': 'Chti',
    'Tags': 'OTU',
    'Names': [{'Text': 'Chtierabl', 'Lang': 'zh'}],
}

_SAMPLE_SEC_TEXT = """\
# Sector: Trojan Reach
# Milieu: M1105
# Alleg: FlLe: "Federation of Llellewyloly"
# Alleg: NaHu: "Non-Aligned, Human-dominated"

Hex  Name              UWP       Remarks                       {Ix}   (Ex)    [Cx]   N     B  Z PBG W  A    Stellar
---- ----------------- --------- ----------------------------- ------ ------- ------ ----- -- - --- -- ---- ---------
0103 Taltern           E530240-6 De Lo Po                      { -3 } (410-5) [1111] -     -  - 202 7  NaHu M2 V M2 V
0110 Bilke             D987341-7 Lo FlorW                      { -3 } (520-5) [1113] -     -  - 202 6  FlLe F0 V
0201 Szirp             A436538-D Ni Ht                         { 1 }  (745+1) [565D] -     -  - 800 9  NaHu M8 V
"""


class TestTravellerMapWorldFields:
    def test_plain_fields(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.name == 'Hexx'
        assert world.hex == '2715'
        assert world.uwp == 'B78A577-D'
        assert world.pbg == '314'
        assert world.zone == ''
        assert world.bases == 'N'
        assert world.ss == 'H'
        assert world.remarks == 'Ni Wa Pr Ht'
        assert world.sector == 'Trojan Reach'
        assert world.sector_abbreviation == 'Troj'
        assert world.allegiance_name == 'Third Imperium, Domain of Deneb'
        assert world.subsector_name == 'Tobia'
        assert world.worlds == 11
        assert world.resource_units == 240
        assert world.world_x == -102
        assert world.world_y == -25

    def test_tl(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.tl == 13  # D in hex

    def test_starport(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.starport == 'B'

    def test_size(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.size == 7

    def test_atmosphere(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.atmosphere == 8

    def test_hydrographics(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.hydrographics == 10  # A in hex

    def test_population(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.population == 5

    def test_government(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.government == 7

    def test_law_level(self) -> None:
        world = TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert world.law_level == 7


class TestSectorInfo:
    def test_from_raw(self) -> None:
        info = SectorInfo.from_raw(_SAMPLE_SECTOR_JSON)
        assert info.abbreviation == 'Chti'
        assert info.milieu == 'M1105'
        assert info.tags == 'OTU'
        assert info.names == ['Chtierabl']
        assert info.x == -7
        assert info.y == -8

    def test_multiple_names(self) -> None:
        raw = {**_SAMPLE_SECTOR_JSON, 'Names': [{'Text': 'Name One'}, {'Text': 'Name Two'}]}
        info = SectorInfo.from_raw(raw)
        assert info.names == ['Name One', 'Name Two']

    def test_no_names(self) -> None:
        raw = {**_SAMPLE_SECTOR_JSON, 'Names': []}
        info = SectorInfo.from_raw(raw)
        assert info.names == []

    def test_missing_abbreviation_defaults_to_empty_string(self) -> None:
        raw = dict(_SAMPLE_SECTOR_JSON)
        raw.pop('Abbreviation')
        info = SectorInfo.from_raw(raw)
        assert info.abbreviation == ''


class TestParseColumnPositions:
    def test_three_columns(self) -> None:
        sep = '---- -------------------- ---------'
        cols = _parse_column_positions(sep)
        assert cols == [(0, 4), (5, 25), (26, 35)]

    def test_single_column(self) -> None:
        assert _parse_column_positions('----') == [(0, 4)]

    def test_trailing_column(self) -> None:
        cols = _parse_column_positions('---- ----')
        assert cols == [(0, 4), (5, 9)]

    def test_separator_ending_after_column(self) -> None:
        cols = _parse_column_positions('---- ---- ')
        assert cols == [(0, 4), (5, 9)]


class TestExtract:
    def test_extracts_full_column(self) -> None:
        assert _extract('0103 Taltern', [(0, 4), (5, 12)], 1) == 'Taltern'

    def test_extracts_truncated_column(self) -> None:
        assert _extract('0103 Ta', [(0, 4), (5, 12)], 1) == 'Ta'

    def test_missing_column_is_empty(self) -> None:
        assert _extract('0103', [(0, 4), (5, 12)], 1) == ''


class TestParseSectorWorlds:
    def test_count(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert len(worlds) == 3

    def test_first_entry(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert worlds[0] == SectorWorldEntry(
            hex='0103',
            name='Taltern',
            uwp='E530240-6',
            remarks='De Lo Po',
            bases='-',
            allegiance='NaHu',
        )

    def test_second_entry(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert worlds[1] == SectorWorldEntry(
            hex='0110',
            name='Bilke',
            uwp='D987341-7',
            remarks='Lo FlorW',
            bases='-',
            allegiance='FlLe',
        )

    def test_third_entry(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert worlds[2] == SectorWorldEntry(
            hex='0201',
            name='Szirp',
            uwp='A436538-D',
            remarks='Ni Ht',
            bases='-',
            allegiance='NaHu',
        )

    def test_empty_text(self) -> None:
        assert _parse_sec_worlds('') == []

    def test_only_comments(self) -> None:
        assert _parse_sec_worlds('# comment\n# another\n') == []


class TestFetchSector:
    def test_parses_sector_name_and_allegiance_labels_from_sec_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT)
        requests: list[tuple[str, dict | None]] = []

        def client_factory() -> _FakeClient:
            client = _FakeClient()
            client.response = response
            client.requests = requests
            return client

        monkeypatch.setattr(travellermap.httpx, 'Client', client_factory)

        sector = travellermap.fetch_sector('Troj')

        assert sector.abbreviation == 'Troj'
        assert sector.name == 'Trojan Reach'
        assert sector.allegiance_names == {
            'FlLe': 'Federation of Llellewyloly',
            'NaHu': 'Non-Aligned, Human-dominated',
        }
        assert [world.name for world in sector.worlds] == ['Taltern', 'Bilke', 'Szirp']
        assert requests == [('https://travellermap.com/data/Troj', None)]
        assert response.raise_for_status_called


class _FakeResponse:
    def __init__(self, *, json_data: dict | None = None, text: str = '') -> None:
        self._json_data = {} if json_data is None else json_data
        self.text = text
        self.raise_for_status_called = False

    def json(self) -> dict:
        return self._json_data

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True


class _FakeClient:
    requests: list[tuple[str, dict | None]]
    response: _FakeResponse

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get(self, url: str, *, params: dict | None = None) -> _FakeResponse:
        self.requests.append((url, params))
        return self.response


class TestFetchSectors:
    def setup_method(self) -> None:
        clear_travellermap_cache()

    def test_fetches_sector_info_from_travellermap_data_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(json_data={'Sectors': [_SAMPLE_SECTOR_JSON]})
        requests: list[tuple[str, dict | None]] = []

        def client_factory() -> _FakeClient:
            client = _FakeClient()
            client.response = response
            client.requests = requests
            return client

        monkeypatch.setattr(travellermap.httpx, 'Client', client_factory)

        sectors = fetch_sectors('M1120')

        assert sectors == [SectorInfo.from_raw(_SAMPLE_SECTOR_JSON)]
        assert requests == [('https://travellermap.com/data', {'milieu': 'M1120'})]
        assert response.raise_for_status_called

    def test_reuses_cached_sector_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(json_data={'Sectors': [_SAMPLE_SECTOR_JSON]})
        requests: list[tuple[str, dict | None]] = []

        def client_factory() -> _FakeClient:
            client = _FakeClient()
            client.response = response
            client.requests = requests
            return client

        monkeypatch.setattr(travellermap.httpx, 'Client', client_factory)

        first = fetch_sectors('M1120')
        second = fetch_sectors('M1120')

        assert first == second == [SectorInfo.from_raw(_SAMPLE_SECTOR_JSON)]
        assert requests == [('https://travellermap.com/data', {'milieu': 'M1120'})]


class TestFetchSectorWorlds:
    def setup_method(self) -> None:
        clear_travellermap_cache()

    def test_fetches_and_parses_sector_sec_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT)
        requests: list[tuple[str, dict | None]] = []

        def client_factory() -> _FakeClient:
            client = _FakeClient()
            client.response = response
            client.requests = requests
            return client

        monkeypatch.setattr(travellermap.httpx, 'Client', client_factory)

        worlds = fetch_sector_worlds('Troj')

        assert worlds[0] == SectorWorldEntry(
            hex='0103',
            name='Taltern',
            uwp='E530240-6',
            remarks='De Lo Po',
            bases='-',
            allegiance='NaHu',
        )
        assert requests == [('https://travellermap.com/data/Troj', None)]
        assert response.raise_for_status_called

    def test_reuses_cached_sector_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT)
        requests: list[tuple[str, dict | None]] = []

        def client_factory() -> _FakeClient:
            client = _FakeClient()
            client.response = response
            client.requests = requests
            return client

        monkeypatch.setattr(travellermap.httpx, 'Client', client_factory)

        sector = fetch_sector('Troj')
        worlds = fetch_sector_worlds('Troj')
        again = fetch_sector('Troj')

        assert sector.name == 'Trojan Reach'
        assert [world.name for world in worlds] == ['Taltern', 'Bilke', 'Szirp']
        assert again == sector
        assert requests == [('https://travellermap.com/data/Troj', None)]


class TestFetchWorld:
    def test_fetches_world_from_travellermap_data_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(json_data={'Worlds': [_SAMPLE_WORLD_JSON]})
        requests: list[tuple[str, dict | None]] = []

        def client_factory() -> _FakeClient:
            client = _FakeClient()
            client.response = response
            client.requests = requests
            return client

        monkeypatch.setattr(travellermap.httpx, 'Client', client_factory)

        world = fetch_world('Troj', '2715')

        assert world == TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert requests == [('https://travellermap.com/data/Troj/2715', None)]
        assert response.raise_for_status_called

    def test_missing_world_raises_value_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(json_data={'Worlds': []})

        def client_factory() -> _FakeClient:
            client = _FakeClient()
            client.response = response
            client.requests = []
            return client

        monkeypatch.setattr(travellermap.httpx, 'Client', client_factory)

        with pytest.raises(ValueError, match='No world at Troj/9999'):
            fetch_world('Troj', '9999')

        assert response.raise_for_status_called
