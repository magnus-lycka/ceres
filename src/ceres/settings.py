from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir, user_data_dir


def config_dir() -> Path:
    return Path(user_config_dir('ceres'))


def data_dir() -> Path:
    return Path(user_data_dir('ceres'))


def cache_dir() -> Path:
    return Path(user_cache_dir('ceres'))
