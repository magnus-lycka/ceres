from ceres.adapters.travellermap import (
    SectorInfo,
    SectorWorldEntry,
    TravellerMapWorld,
    _parse_column_positions,
    _parse_sec_worlds,
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


class TestParseSectorWorlds:
    def test_count(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert len(worlds) == 3

    def test_first_entry(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert worlds[0] == SectorWorldEntry(hex='0103', name='Taltern', uwp='E530240-6', remarks='De Lo Po')

    def test_second_entry(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert worlds[1] == SectorWorldEntry(hex='0110', name='Bilke', uwp='D987341-7', remarks='Lo FlorW')

    def test_third_entry(self) -> None:
        worlds = _parse_sec_worlds(_SAMPLE_SEC_TEXT)
        assert worlds[2] == SectorWorldEntry(hex='0201', name='Szirp', uwp='A436538-D', remarks='Ni Ht')

    def test_empty_text(self) -> None:
        assert _parse_sec_worlds('') == []

    def test_only_comments(self) -> None:
        assert _parse_sec_worlds('# comment\n# another\n') == []
