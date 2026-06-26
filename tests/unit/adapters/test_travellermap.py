import json
from pathlib import Path

import pytest

from ceres.adapters import travellermap
from ceres.adapters.travellermap import (
    SectorInfo,
    SectorWorldEntry,
    TravellerMapWorld,
    _extract,
    _parse_allegiance_names,
    _parse_column_positions,
    _parse_sec_worlds,
    clear_travellermap_cache,
    clear_travellermap_memory_cache,
    fetch_sector,
    fetch_sector_coordinates,
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

_UNKNOWN_SEC_TEXT = """\
# Sector: Reft
# Milieu: M1105

Hex  Name              UWP       Remarks                       {Ix}   (Ex)    [Cx]   N     B  Z PBG W  A    Stellar
---- ----------------- --------- ----------------------------- ------ ------- ------ ----- -- - --- -- ---- ---------
0101 Marker            ???????-?                               { 0 }  (000+0) [0000] -     -  - 000 0  NaXX Pulsar
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

    @pytest.mark.parametrize(
        ('abbreviation', 'name'),
        [
            ('Spin', 'Spinward Marches'),
            ('Troj', 'Trojan Reach'),
            ('Dene', 'Deneb'),
            ('Core', 'Core'),
            ('Reft', 'Reft'),
            ('Touc', 'Touchstone'),
        ],
    )
    def test_directory_name_examples(self, abbreviation: str, name: str) -> None:
        info = SectorInfo(x=0, y=0, milieu='M1105', abbreviation=abbreviation, tags='OTU', names=[name])
        assert info.abbreviation == abbreviation
        assert info.names[0] == name


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
            ix='{ -3 }',
            ex='(410-5)',
            cx='[1111]',
            nobility='-',
            bases='-',
            zone='-',
            pbg='202',
            world_count='7',
            allegiance='NaHu',
            stellar='M2 V M2 V',
        )

    def test_second_entry(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert worlds[1] == SectorWorldEntry(
            hex='0110',
            name='Bilke',
            uwp='D987341-7',
            remarks='Lo FlorW',
            ix='{ -3 }',
            ex='(520-5)',
            cx='[1113]',
            nobility='-',
            bases='-',
            zone='-',
            pbg='202',
            world_count='6',
            allegiance='FlLe',
            stellar='F0 V',
        )

    def test_third_entry(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert worlds[2] == SectorWorldEntry(
            hex='0201',
            name='Szirp',
            uwp='A436538-D',
            remarks='Ni Ht',
            ix='{ 1 }',
            ex='(745+1)',
            cx='[565D]',
            nobility='-',
            bases='-',
            zone='-',
            pbg='800',
            world_count='9',
            allegiance='NaHu',
            stellar='M8 V',
        )

    def test_empty_text(self) -> None:
        assert _parse_sec_worlds('') == []

    def test_only_comments(self) -> None:
        assert _parse_sec_worlds('# comment\n# another\n') == []

    def test_unknown_uwp_digits_are_preserved_without_numeric_crash(self) -> None:
        worlds = _parse_sec_worlds(_UNKNOWN_SEC_TEXT)

        assert worlds[0] == SectorWorldEntry(
            hex='0101',
            name='Marker',
            uwp='???????-?',
            remarks='',
            ix='{ 0 }',
            ex='(000+0)',
            cx='[0000]',
            nobility='-',
            bases='-',
            zone='-',
            pbg='000',
            world_count='0',
            allegiance='NaXX',
            stellar='Pulsar',
        )
        assert worlds[0].starport == '?'
        assert worlds[0].size is None
        assert worlds[0].atmosphere is None
        assert worlds[0].hydrographics is None
        assert worlds[0].population is None
        assert worlds[0].government is None
        assert worlds[0].law_level is None
        assert worlds[0].tl is None


class TestFetchSector:
    def setup_method(self) -> None:
        clear_travellermap_cache()

    def test_parses_sector_name_and_allegiance_labels_from_sec_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT)
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)

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

    def test_falls_back_to_sector_directory_name_when_sec_header_lacks_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT.replace('# Sector: Trojan Reach\n', ''))
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)
        monkeypatch.setattr(
            travellermap,
            'fetch_sectors',
            lambda milieu='M1105': [
                SectorInfo(x=0, y=0, milieu='M1105', abbreviation='Troj', tags='OTU', names=['Trojan Reach'])
            ],
        )

        sector = travellermap.fetch_sector('Troj')

        assert sector.name == 'Trojan Reach'

    def test_uses_abbreviation_when_sector_not_in_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT.replace('# Sector: Trojan Reach\n', ''))
        client = _FakeClient()
        client.response = response
        client.requests = []
        monkeypatch.setattr(travellermap.httpx, 'Client', client)
        monkeypatch.setattr(
            travellermap,
            'fetch_sectors',
            lambda milieu='M1105': [
                SectorInfo(x=1, y=2, milieu='M1105', abbreviation='Spin', tags='OTU', names=['Spinward Marches'])
            ],
        )

        sector = travellermap.fetch_sector('Troj')

        assert sector.name == 'Troj'

    def test_loads_sector_coordinates_from_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(
            text=json.dumps(
                {
                    'Sectors': [
                        {
                            'X': -4,
                            'Y': 1,
                            'Milieu': 'M1105',
                            'Abbreviation': 'Troj',
                            'Tags': 'OTU',
                            'Names': [{'Text': 'Trojan Reach'}],
                        }
                    ]
                }
            )
        )
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)

        sector_x, sector_y = travellermap.fetch_sector_coordinates('Troj')

        assert (sector_x, sector_y) == (-4, 1)


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

    def __call__(self, **_kwargs: object) -> _FakeClient:
        return self

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
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)

        sectors = fetch_sectors('M1120')

        assert sectors == [SectorInfo.from_raw(_SAMPLE_SECTOR_JSON)]
        assert requests == [('https://travellermap.com/data', {'milieu': 'M1120'})]
        assert response.raise_for_status_called

    def test_reuses_cached_sector_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(json_data={'Sectors': [_SAMPLE_SECTOR_JSON]})
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)

        first = fetch_sectors('M1120')
        second = fetch_sectors('M1120')

        assert first == second == [SectorInfo.from_raw(_SAMPLE_SECTOR_JSON)]
        assert requests == [('https://travellermap.com/data', {'milieu': 'M1120'})]

    def test_reuses_disk_cached_sector_list(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        clear_travellermap_cache()
        response = _FakeResponse(json_data={'Sectors': [_SAMPLE_SECTOR_JSON]})
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)
        monkeypatch.setattr(travellermap.settings, 'cache_dir', lambda: tmp_path)

        first = fetch_sectors('M1120')
        clear_travellermap_memory_cache()
        second = fetch_sectors('M1120')

        assert first == second == [SectorInfo.from_raw(_SAMPLE_SECTOR_JSON)]
        assert requests == [('https://travellermap.com/data', {'milieu': 'M1120'})]


class TestFetchSectorWorlds:
    def setup_method(self) -> None:
        clear_travellermap_cache()

    def test_fetches_and_parses_sector_sec_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT)
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)

        worlds = fetch_sector_worlds('Troj')

        assert worlds[0] == SectorWorldEntry(
            hex='0103',
            name='Taltern',
            uwp='E530240-6',
            remarks='De Lo Po',
            ix='{ -3 }',
            ex='(410-5)',
            cx='[1111]',
            nobility='-',
            bases='-',
            zone='-',
            pbg='202',
            world_count='7',
            allegiance='NaHu',
            stellar='M2 V M2 V',
        )
        assert requests == [('https://travellermap.com/data/Troj', None)]
        assert response.raise_for_status_called

    def test_reuses_cached_sector_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT)
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)

        sector = fetch_sector('Troj')
        worlds = fetch_sector_worlds('Troj')
        again = fetch_sector('Troj')

        assert sector.name == 'Trojan Reach'
        assert [world.name for world in worlds] == ['Taltern', 'Bilke', 'Szirp']
        assert again == sector
        assert requests == [('https://travellermap.com/data/Troj', None)]

    def test_reuses_disk_cached_sector_data(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        clear_travellermap_cache()
        response = _FakeResponse(text=_SAMPLE_SEC_TEXT)
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)
        monkeypatch.setattr(travellermap.settings, 'cache_dir', lambda: tmp_path)

        first = fetch_sector('Troj')
        clear_travellermap_memory_cache()
        second = fetch_sector('Troj')

        assert first == second
        assert requests == [('https://travellermap.com/data/Troj', None)]


class TestFetchWorld:
    def test_fetches_world_from_travellermap_data_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(json_data={'Worlds': [_SAMPLE_WORLD_JSON]})
        requests: list[tuple[str, dict | None]] = []
        client = _FakeClient()
        client.response = response
        client.requests = requests
        monkeypatch.setattr(travellermap.httpx, 'Client', client)

        world = fetch_world('Troj', '2715')

        assert world == TravellerMapWorld.model_validate(_SAMPLE_WORLD_JSON)
        assert requests == [('https://travellermap.com/data/Troj/2715', None)]
        assert response.raise_for_status_called

    def test_missing_world_raises_value_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        response = _FakeResponse(json_data={'Worlds': []})
        client = _FakeClient()
        client.response = response
        client.requests = []
        monkeypatch.setattr(travellermap.httpx, 'Client', client)

        with pytest.raises(ValueError, match='No world at Troj/9999'):
            fetch_world('Troj', '9999')

        assert response.raise_for_status_called


class TestSectorWorldEntryProperties:
    _ENTRY = SectorWorldEntry(
        hex='0103',
        name='Taltern',
        uwp='E530240-6',
        remarks='De Lo Po',
        ix='{ -3 }',
        ex='(410-5)',
        cx='[1111]',
        nobility='-',
        bases='-',
        zone='-',
        pbg='202',
        world_count='7',
        allegiance='NaHu',
        stellar='M2 V M2 V',
    )

    def test_starport(self) -> None:
        assert self._ENTRY.starport == 'E'

    def test_size(self) -> None:
        assert self._ENTRY.size == 5

    def test_atmosphere(self) -> None:
        assert self._ENTRY.atmosphere == 3

    def test_hydrographics(self) -> None:
        assert self._ENTRY.hydrographics == 0

    def test_population(self) -> None:
        assert self._ENTRY.population == 2

    def test_government(self) -> None:
        assert self._ENTRY.government == 4

    def test_law_level(self) -> None:
        assert self._ENTRY.law_level == 0

    def test_tl(self) -> None:
        assert self._ENTRY.tl == 6


class TestReadCachedPayload:
    def test_returns_none_for_expired_cache_entry(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(travellermap.settings, 'cache_dir', lambda: tmp_path)
        url = 'https://example.com/test'
        travellermap._write_cached_payload(url, 'some_payload')
        monkeypatch.setattr(travellermap, 'time', lambda: float('inf'))

        result = travellermap._read_cached_payload(url)

        assert result is None


class TestParseAllegianceNames:
    def test_valid_allegiance_line(self) -> None:
        text = '# Alleg: NaHu: "Non-Aligned, Human-dominated"\n'
        assert _parse_allegiance_names(text) == {'NaHu': 'Non-Aligned, Human-dominated'}

    def test_skips_line_with_no_label(self) -> None:
        text = '# Alleg: NaHu\n# Alleg: Good: "Valid"\n'
        assert _parse_allegiance_names(text) == {'Good': 'Valid'}

    def test_skips_line_with_no_code(self) -> None:
        text = '# Alleg: : No Code\n# Alleg: Good: "Valid"\n'
        assert _parse_allegiance_names(text) == {'Good': 'Valid'}

    def test_skips_non_allegiance_lines(self) -> None:
        text = '# Sector: Test\n# Alleg: AA: "Alpha"\n'
        assert _parse_allegiance_names(text) == {'AA': 'Alpha'}


class TestFetchSectorCoordinates:
    def setup_method(self) -> None:
        clear_travellermap_cache()

    def test_returns_zero_zero_when_no_sectors_in_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(travellermap, 'fetch_sectors', lambda milieu='M1105': [])

        assert fetch_sector_coordinates('Troj') == (0, 0)

    def test_returns_zero_zero_when_sector_not_in_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            travellermap,
            'fetch_sectors',
            lambda milieu='M1105': [
                SectorInfo(x=1, y=2, milieu='M1105', abbreviation='Spin', tags='OTU', names=['Spinward Marches'])
            ],
        )

        assert fetch_sector_coordinates('Troj') == (0, 0)


class TestClearTravellerMapCache:
    def test_does_nothing_when_cache_dir_does_not_exist(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        non_existent = tmp_path / 'nonexistent'
        monkeypatch.setattr(travellermap.settings, 'cache_dir', lambda: non_existent)
        clear_travellermap_cache()  # should not raise
