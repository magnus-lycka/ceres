from ceres.adapters.travellermap import SectorInfo, SectorWorldEntry
from ceres.worlds import DEFAULT_MILIEU, SectorWorldFilters, SectorWorldOptions, search_sectors


def _entry(
    *,
    name: str,
    hex_code: str,
    uwp: str,
    bases: str,
    allegiance: str,
    remarks: str,
) -> SectorWorldEntry:
    return SectorWorldEntry(
        hex=hex_code,
        name=name,
        uwp=uwp,
        remarks=remarks,
        ix='{ 0 }',
        ex='(000+0)',
        cx='[0000]',
        nobility='-',
        bases=bases,
        zone='-',
        pbg='111',
        world_count='1',
        allegiance=allegiance,
        stellar='G2 V',
    )


def _sample_worlds() -> list[SectorWorldEntry]:
    return [
        _entry(
            name='Aster',
            hex_code='0101',
            uwp='A867A99-D',
            bases='NS',
            allegiance='ImDd',
            remarks='Hi In',
        ),
        _entry(
            name='Beryl',
            hex_code='0102',
            uwp='C433567-A',
            bases='W',
            allegiance='ImAp',
            remarks='Ni Po',
        ),
        _entry(
            name='Cinder',
            hex_code='0103',
            uwp='E100200-7',
            bases='',
            allegiance='NaHu',
            remarks='Ba Va',
        ),
    ]


def _sample_worlds_with_unaligned() -> list[SectorWorldEntry]:
    return [
        *_sample_worlds(),
        _entry(
            name='Drift',
            hex_code='0104',
            uwp='B544678-9',
            bases='',
            allegiance='',
            remarks='Ni',
        ),
    ]


def _sample_worlds_with_unknown_uwp() -> list[SectorWorldEntry]:
    return [
        *_sample_worlds(),
        _entry(
            name='Anomaly',
            hex_code='9999',
            uwp='???????-?',
            bases='',
            allegiance='NaXX',
            remarks='',
        ),
    ]


class TestSectorWorldOptions:
    def test_collects_checkbox_values_from_sector_worlds(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        assert filters.options == SectorWorldOptions(
            allegiances=('ImAp', 'ImDd', 'NaHu'),
            remarks=('Ba', 'Hi', 'In', 'Ni', 'Po', 'Va'),
            bases=('N', 'S', 'W'),
            starports=('A', 'C', 'E'),
            sizes=('1', '4', '8'),
            atmospheres=('0', '3', '6'),
            hydrographics=('0', '3', '7'),
            populations=('2', '5', 'A'),
            governments=('0', '6', '9'),
            law_levels=('0', '7', '9'),
            tech_levels=('7', 'A', 'D'),
        )

    def test_empty_sector_has_empty_options(self) -> None:
        filters = SectorWorldFilters(worlds=[])

        assert filters.options == SectorWorldOptions()

    def test_collects_no_allegiance_option_when_any_world_has_blank_allegiance(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds_with_unaligned())

        assert filters.options.allegiances == ('ImAp', 'ImDd', 'NaHu', 'No Allegiance')

    def test_includes_unknown_uwp_codes_in_code_filter_options(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds_with_unknown_uwp())

        assert filters.options.starports == ('A', 'C', 'E', '?')
        assert filters.options.sizes == ('1', '4', '8', '?')
        assert filters.options.atmospheres == ('0', '3', '6', '?')
        assert filters.options.hydrographics == ('0', '3', '7', '?')
        assert filters.options.populations == ('2', '5', 'A', '?')
        assert filters.options.governments == ('0', '6', '9', '?')
        assert filters.options.law_levels == ('0', '7', '9', '?')
        assert filters.options.tech_levels == ('7', 'A', 'D', '?')


class TestSectorWorldFiltering:
    def test_filter_returns_all_worlds_when_no_selection_is_given(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        assert [world.name for world in filters.filter_worlds()] == ['Aster', 'Beryl', 'Cinder']

    def test_filter_by_allegiance_subset(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        selected = filters.filter_worlds(allegiances={'ImDd', 'NaHu'})

        assert [world.name for world in selected] == ['Aster', 'Cinder']

    def test_filter_by_remark_subset(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        selected = filters.filter_worlds(remarks={'Po', 'Va'})

        assert [world.name for world in selected] == ['Beryl', 'Cinder']

    def test_filter_by_base_subset(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        selected = filters.filter_worlds(bases={'S', 'W'})

        assert [world.name for world in selected] == ['Aster', 'Beryl']

    def test_filter_by_uwp_component_subsets(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        selected = filters.filter_worlds(starports={'A', 'E'}, tech_levels={'D'})

        assert [world.name for world in selected] == ['Aster']

    def test_filter_by_no_allegiance(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds_with_unaligned())

        selected = filters.filter_worlds(allegiances={'No Allegiance'})

        assert [world.name for world in selected] == ['Drift']

    def test_filter_by_unknown_uwp_value(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds_with_unknown_uwp())

        selected = filters.filter_worlds(sizes={'?'}, tech_levels={'?'})

        assert [world.name for world in selected] == ['Anomaly']

    def test_filter_combines_categories_with_and_logic(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        selected = filters.filter_worlds(allegiances={'ImDd', 'ImAp'}, remarks={'Ni'}, bases={'W'})

        assert [world.name for world in selected] == ['Beryl']

    def test_filter_uses_or_logic_within_each_category(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        selected = filters.filter_worlds(starports={'A', 'C'}, populations={'5', 'A'})

        assert [world.name for world in selected] == ['Aster', 'Beryl']

    def test_filter_uses_uwp_codes_not_numeric_conversion(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        selected = filters.filter_worlds(populations={'A'}, tech_levels={'D'})

        assert [world.name for world in selected] == ['Aster']

    def test_filter_by_world_name_or_hex(self) -> None:
        filters = SectorWorldFilters(worlds=_sample_worlds())

        by_name = filters.filter_worlds(world_query='ber')
        by_hex = filters.filter_worlds(world_query='0103')

        assert [world.name for world in by_name] == ['Beryl']
        assert [world.name for world in by_hex] == ['Cinder']


class TestSectorFromTravellerMap:
    def test_loads_sector_worlds_from_adapter_without_fetching_each_world(self, monkeypatch) -> None:
        sample_worlds = _sample_worlds()
        called_sectors: list[str] = []

        from ceres.adapters.travellermap import SectorData

        def fake_fetch_sector(sector_abbreviation: str) -> SectorData:
            called_sectors.append(sector_abbreviation)
            return SectorData(
                abbreviation=sector_abbreviation,
                name='Trojan Reach',
                allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
                worlds=sample_worlds,
            )

        monkeypatch.setattr('ceres.worlds.sector_filters.fetch_sector', fake_fetch_sector)

        filters = SectorWorldFilters.from_travellermap('Troj')

        assert called_sectors == ['Troj']
        assert filters.sector_abbreviation == 'Troj'
        assert filters.sector_name == 'Trojan Reach'
        assert filters.allegiance_names == {'ImDd': 'Third Imperium, Domain of Deneb'}
        assert [world.name for world in filters.worlds] == ['Aster', 'Beryl', 'Cinder']


class TestSearchSectors:
    def test_matches_sector_abbreviation_and_name_case_insensitively(self, monkeypatch) -> None:
        sectors = [
            SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='Troj', tags='OTU', names=['Trojan Reach']),
            SectorInfo(x=1, y=0, milieu=DEFAULT_MILIEU, abbreviation='Dene', tags='OTU', names=['Deneb']),
            SectorInfo(x=2, y=0, milieu=DEFAULT_MILIEU, abbreviation='GvDn', tags='OTU', names=['Gvurrdon']),
        ]

        monkeypatch.setattr('ceres.worlds.sector_filters.fetch_sectors', lambda milieu=DEFAULT_MILIEU: sectors)

        assert [sector.abbreviation for sector in search_sectors('troj')] == ['Troj']
        assert [sector.abbreviation for sector in search_sectors('den')] == ['Dene']
        assert [sector.abbreviation for sector in search_sectors('gv')] == ['GvDn']

    def test_prefers_abbreviation_exact_match_then_prefix_then_name(self, monkeypatch) -> None:
        sectors = [
            SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='Troj', tags='OTU', names=['Trojan Reach']),
            SectorInfo(x=1, y=0, milieu=DEFAULT_MILIEU, abbreviation='Trin', tags='OTU', names=['Trinities']),
            SectorInfo(x=2, y=0, milieu=DEFAULT_MILIEU, abbreviation='Vlan', tags='OTU', names=['The Trojans']),
        ]

        monkeypatch.setattr('ceres.worlds.sector_filters.fetch_sectors', lambda milieu=DEFAULT_MILIEU: sectors)

        assert [sector.abbreviation for sector in search_sectors('tro')] == ['Troj', 'Vlan']
        assert [sector.abbreviation for sector in search_sectors('troj')] == ['Troj']

    def test_blank_query_returns_no_matches(self, monkeypatch) -> None:
        monkeypatch.setattr(
            'ceres.worlds.sector_filters.fetch_sectors',
            lambda milieu=DEFAULT_MILIEU: [_sample_sector_info()],
        )

        assert search_sectors('') == []

    def test_search_handles_sector_without_abbreviation(self, monkeypatch) -> None:
        sectors = [
            SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='', tags='OTU', names=['Aslan Hierate']),
            SectorInfo(x=1, y=0, milieu=DEFAULT_MILIEU, abbreviation='AsTn', tags='OTU', names=['Ashtan']),
        ]

        monkeypatch.setattr('ceres.worlds.sector_filters.fetch_sectors', lambda milieu=DEFAULT_MILIEU: sectors)

        assert [sector.names[0] for sector in search_sectors('aslan')] == ['Aslan Hierate']


def _sample_sector_info() -> SectorInfo:
    return SectorInfo(x=0, y=0, milieu=DEFAULT_MILIEU, abbreviation='Troj', tags='OTU', names=['Trojan Reach'])
