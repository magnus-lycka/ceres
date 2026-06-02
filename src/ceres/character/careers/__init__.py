_CAREER_MODULE_NAMES: dict[str, str] = {
    'AGENT': 'agent',
    'ARMY': 'army',
    'CITIZEN': 'citizen',
    'DRIFTER': 'drifter',
    'ENTERTAINER': 'entertainer',
    'MARINES': 'marines',
    'MERCHANT': 'merchant',
    'NAVY': 'navy',
    'NOBLE': 'noble',
    'PRISONER': 'prisoner',
    'ROGUE': 'rogue',
    'SCHOLAR': 'scholar',
    'SCOUT': 'scout',
}

__all__ = [
    'AGENT',
    'ARMY',
    'CITIZEN',
    'DRIFTER',
    'ENTERTAINER',
    'MARINES',
    'MERCHANT',
    'NAVY',
    'NOBLE',
    'PRISONER',
    'ROGUE',
    'SCHOLAR',
    'SCOUT',
    'load_careers',
    'selectable_careers',
]


def __getattr__(name: str):
    if name in _CAREER_MODULE_NAMES:
        import importlib

        mod = importlib.import_module(f'ceres.character.careers.{_CAREER_MODULE_NAMES[name]}')
        value = getattr(mod, name)
        globals()[name] = value
        return value
    if name in ('load_careers', 'selectable_careers'):
        from ceres.character.careers.loader import load_careers as _lc, selectable_careers as _sc

        globals()['load_careers'] = _lc
        globals()['selectable_careers'] = _sc
        return globals()[name]
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
