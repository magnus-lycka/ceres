from pathlib import Path

from ceres.settings import cache_dir, config_dir, data_dir


def test_config_dir_returns_path():
    assert isinstance(config_dir(), Path)


def test_data_dir_returns_path():
    assert isinstance(data_dir(), Path)


def test_cache_dir_returns_path():
    assert isinstance(cache_dir(), Path)


def test_cache_dir_differs_from_data_dir():
    assert cache_dir() != data_dir()


def test_dirs_contain_ceres():
    assert 'ceres' in str(config_dir()).lower()
    assert 'ceres' in str(data_dir()).lower()
    assert 'ceres' in str(cache_dir()).lower()
