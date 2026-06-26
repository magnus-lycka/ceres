from ceres.worlds import DEFAULT_MILIEU, SectorWorldFilters, SectorWorldOptions, search_sectors


def test_default_milieu_is_string():
    assert isinstance(DEFAULT_MILIEU, str)
    assert DEFAULT_MILIEU  # not empty


def test_sector_world_options_is_importable():
    assert SectorWorldOptions is not None


def test_sector_world_filters_is_importable():
    assert SectorWorldFilters is not None


def test_search_sectors_is_callable():
    assert callable(search_sectors)
