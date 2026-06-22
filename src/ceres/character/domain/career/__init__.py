def __getattr__(name: str):
    career_module_names: dict[str, str] = {
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
        'PSION': 'psion',
        'ROGUE': 'rogue',
        'SCHOLAR': 'scholar',
        'SCOUT': 'scout',
    }
    if name in career_module_names:
        import importlib

        mod = importlib.import_module(f'ceres.character.domain.career.{career_module_names[name]}')
        return getattr(mod, name)
    if name in ('load_careers', 'selectable_careers'):
        from ceres.character.domain.career.loader import load_careers as _lc, selectable_careers as _sc

        return {'load_careers': _lc, 'selectable_careers': _sc}[name]
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
