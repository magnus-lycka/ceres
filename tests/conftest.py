from __future__ import annotations

import cProfile
import io
import pstats
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        '--with-generated-output',
        action='store_true',
        default=False,
        help='run tests that write generated regression artifacts to disk',
    )
    parser.addoption(
        '--with-slow',
        action='store_true',
        default=False,
        help='run tests marked as slow',
    )
    parser.addoption(
        '--all-tests',
        action='store_true',
        default=False,
        help='run all optional tests, including generated-output and slow tests',
    )
    parser.addoption(
        '--profile-session',
        action='store_true',
        default=False,
        help='profile the full pytest session with cProfile',
    )
    parser.addoption(
        '--profile-sort',
        action='store',
        default='cumtime',
        choices=('cumtime', 'tottime', 'calls'),
        help='sort order for cProfile output',
    )
    parser.addoption(
        '--profile-limit',
        action='store',
        type=int,
        default=30,
        help='number of cProfile rows to print in the terminal summary',
    )
    parser.addoption(
        '--profile-dir',
        action='store',
        default='.pytest-profiles',
        help='directory for cProfile output files',
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        'markers',
        'generated_output: writes generated regression artifacts to disk',
    )
    config.addinivalue_line(
        'markers',
        'slow: slow test skipped by default',
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption('--all-tests'):
        return

    skip_generated = pytest.mark.skip(
        reason='skipped generated-output test; pass --with-generated-output or --all-tests to run it',
    )
    skip_slow = pytest.mark.skip(
        reason='skipped slow test; pass --with-slow or --all-tests to run it',
    )

    for item in items:
        if 'generated_output' in item.keywords and not config.getoption('--with-generated-output'):
            item.add_marker(skip_generated)
        if 'slow' in item.keywords and not config.getoption('--with-slow'):
            item.add_marker(skip_slow)


def pytest_sessionstart(session: pytest.Session) -> None:
    config = session.config
    if not config.getoption('--profile-session'):
        return

    output_dir = Path(config.getoption('--profile-dir'))
    output_dir.mkdir(parents=True, exist_ok=True)

    profiler = cProfile.Profile()
    profiler.enable()

    config._session_profiler = profiler
    config._session_profile_dir = output_dir


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    config = session.config
    profiler: cProfile.Profile | None = getattr(config, '_session_profiler', None)
    if profiler is None:
        return

    profiler.disable()

    output_dir: Path = config._session_profile_dir
    stats_path = output_dir / 'session.pstats'
    report_path = output_dir / 'session.txt'
    sort_key = config.getoption('--profile-sort')
    limit = config.getoption('--profile-limit')

    profiler.dump_stats(stats_path)

    report_buffer = io.StringIO()
    stats = pstats.Stats(profiler, stream=report_buffer)
    stats.strip_dirs()
    stats.sort_stats(sort_key)
    stats.print_stats(limit)
    report_path.write_text(report_buffer.getvalue(), encoding='utf-8')

    config._session_profile_stats_path = stats_path
    config._session_profile_report_path = report_path
    config._session_profile_report = report_buffer.getvalue()


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    report = getattr(config, '_session_profile_report', None)
    if report is None:
        return

    stats_path: Path = config._session_profile_stats_path
    report_path: Path = config._session_profile_report_path
    sort_key = config.getoption('--profile-sort')
    limit = config.getoption('--profile-limit')

    terminalreporter.write_sep('-', f'cProfile top {limit} by {sort_key}')
    for line in report.rstrip().splitlines():
        terminalreporter.write_line(line)
    terminalreporter.write_line(f'raw stats: {stats_path}')
    terminalreporter.write_line(f'text report: {report_path}')
