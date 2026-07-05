from pathlib import Path

from tools.check_unit_coverage import coverage_percent_from_line, test_path_for as unit_test_path_for


def test_coverage_percent_from_line_without_missing_column() -> None:
    line = 'src/ceres/character/mechanism/projection.py 5 0 0 0 100%'

    assert coverage_percent_from_line(line) == 100


def test_coverage_percent_from_line_with_missing_column() -> None:
    line = 'src/ceres/character/domain/psionics_data.py 79 0 20 2 98% 60->62, 62->64'

    assert coverage_percent_from_line(line) == 98


def test_coverage_percent_from_line_returns_none_when_no_percent_is_present() -> None:
    assert coverage_percent_from_line('no coverage data here') is None


def test_test_path_for_maps_source_to_mirror_unit_test() -> None:
    src = Path('src/ceres/character/domain/psionics_data.py').resolve()

    assert unit_test_path_for(src).as_posix().endswith('/tests/unit/character/domain/test_psionics_data.py')
