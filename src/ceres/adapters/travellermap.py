from functools import cache
import hashlib
import json
from pathlib import Path
from time import time

import httpx
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_pascal

from ceres import settings
from ceres.shared import ehex_to_int

_BASE_URL = 'https://travellermap.com/data'
_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60


def _optional_ehex_to_int(code: str) -> int | None:
    if code == '?':
        return None
    return ehex_to_int(code)


def _cache_root() -> Path:
    return settings.cache_dir() / 'travellermap'


def _cache_key(url: str, params: dict | None = None) -> str:
    params_key = '' if params is None else json.dumps(params, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(f'{url}?{params_key}'.encode()).hexdigest()


def _cache_path(url: str, params: dict | None = None) -> Path:
    return _cache_root() / f'{_cache_key(url, params)}.json'


def _read_cached_payload(url: str, params: dict | None = None) -> str | None:
    path = _cache_path(url, params)
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    fetched_at = float(raw.get('fetched_at', 0))
    if time() - fetched_at > _CACHE_TTL_SECONDS:
        return None
    return str(raw['payload'])


def _write_cached_payload(url: str, payload: str, params: dict | None = None) -> None:
    path = _cache_path(url, params)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'fetched_at': time(), 'payload': payload}))


def _fetch_text(url: str, *, params: dict | None = None) -> str:
    cached = _read_cached_payload(url, params)
    if cached is not None:
        return cached
    with httpx.Client() as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.text or json.dumps(response.json())
        _write_cached_payload(url, payload, params)
        return payload


def _fetch_json(url: str, *, params: dict | None = None) -> dict:
    return json.loads(_fetch_text(url, params=params))


class SectorInfo(BaseModel):
    x: int
    y: int
    milieu: str
    abbreviation: str
    tags: str
    names: list[str]

    @classmethod
    def from_raw(cls, raw: dict) -> SectorInfo:
        return cls(
            x=raw['X'],
            y=raw['Y'],
            milieu=raw['Milieu'],
            abbreviation=raw.get('Abbreviation', ''),
            tags=raw['Tags'],
            names=[n['Text'] for n in raw.get('Names', [])],
        )


class SectorWorldEntry(BaseModel):
    hex: str
    name: str
    uwp: str
    remarks: str
    ix: str
    ex: str
    cx: str
    nobility: str
    bases: str
    zone: str
    pbg: str
    world_count: str
    allegiance: str
    stellar: str

    @property
    def starport(self) -> str:
        return self.uwp[0]

    @property
    def size(self) -> int | None:
        return _optional_ehex_to_int(self.uwp[1])

    @property
    def atmosphere(self) -> int | None:
        return _optional_ehex_to_int(self.uwp[2])

    @property
    def hydrographics(self) -> int | None:
        return _optional_ehex_to_int(self.uwp[3])

    @property
    def population(self) -> int | None:
        return _optional_ehex_to_int(self.uwp[4])

    @property
    def government(self) -> int | None:
        return _optional_ehex_to_int(self.uwp[5])

    @property
    def law_level(self) -> int | None:
        return _optional_ehex_to_int(self.uwp[6])

    @property
    def tl(self) -> int | None:
        return _optional_ehex_to_int(self.uwp[8])


class SectorData(BaseModel):
    abbreviation: str
    name: str
    sector_x: int = 0
    sector_y: int = 0
    allegiance_names: dict[str, str] = Field(default_factory=dict)
    worlds: list[SectorWorldEntry]


class TravellerMapWorld(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_pascal)

    name: str
    hex: str
    uwp: str = Field(validation_alias='UWP')
    pbg: str = Field(validation_alias='PBG')
    zone: str
    bases: str
    allegiance: str
    stellar: str
    ss: str = Field(validation_alias='SS')
    ix: str
    ex: str
    cx: str
    nobility: str
    worlds: int
    resource_units: int
    subsector: int
    quadrant: int
    world_x: int
    world_y: int
    remarks: str
    legacy_base_code: str
    sector: str
    subsector_name: str
    sector_abbreviation: str
    allegiance_name: str

    @property
    def starport(self) -> str:
        return self.uwp[0]

    @property
    def size(self) -> int:
        return ehex_to_int(self.uwp[1])

    @property
    def atmosphere(self) -> int:
        return ehex_to_int(self.uwp[2])

    @property
    def hydrographics(self) -> int:
        return ehex_to_int(self.uwp[3])

    @property
    def population(self) -> int:
        return ehex_to_int(self.uwp[4])

    @property
    def government(self) -> int:
        return ehex_to_int(self.uwp[5])

    @property
    def law_level(self) -> int:
        return ehex_to_int(self.uwp[6])

    @property
    def tl(self) -> int:
        return ehex_to_int(self.uwp[8])


def _parse_column_positions(separator: str) -> list[tuple[int, int]]:
    cols: list[tuple[int, int]] = []
    in_col = False
    start = 0
    for i, ch in enumerate(separator):
        if ch == '-' and not in_col:
            start = i
            in_col = True
        elif ch != '-' and in_col:
            cols.append((start, i))
            in_col = False
    if in_col:
        cols.append((start, len(separator)))
    return cols


def _extract(line: str, col_positions: list[tuple[int, int]], idx: int) -> str:
    start, end = col_positions[idx]
    if end <= len(line):
        return line[start:end].strip()
    if start < len(line):
        return line[start:].strip()
    return ''


def _parse_sec_worlds(text: str) -> list[SectorWorldEntry]:
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith('#')]
    if len(lines) < 3:  # noqa: PLR2004 - SEC text needs header, separator, and at least one data row.
        return []

    header, separator, *data_lines = lines
    col_positions = _parse_column_positions(separator)
    fields = [header[s:e].strip().lower() for s, e in col_positions]

    hex_idx = fields.index('hex')
    name_idx = fields.index('name')
    uwp_idx = fields.index('uwp')
    remarks_idx = fields.index('remarks')
    ix_idx = fields.index('{ix}')
    ex_idx = fields.index('(ex)')
    cx_idx = fields.index('[cx]')
    nobility_idx = fields.index('n')
    bases_idx = fields.index('b')
    zone_idx = fields.index('z')
    pbg_idx = fields.index('pbg')
    world_count_idx = fields.index('w')
    allegiance_idx = fields.index('a')
    stellar_idx = fields.index('stellar')

    return [
        SectorWorldEntry(
            hex=_extract(line, col_positions, hex_idx),
            name=_extract(line, col_positions, name_idx),
            uwp=_extract(line, col_positions, uwp_idx),
            remarks=_extract(line, col_positions, remarks_idx),
            ix=_extract(line, col_positions, ix_idx),
            ex=_extract(line, col_positions, ex_idx),
            cx=_extract(line, col_positions, cx_idx),
            nobility=_extract(line, col_positions, nobility_idx),
            bases=_extract(line, col_positions, bases_idx),
            zone=_extract(line, col_positions, zone_idx),
            pbg=_extract(line, col_positions, pbg_idx),
            world_count=_extract(line, col_positions, world_count_idx),
            allegiance=_extract(line, col_positions, allegiance_idx),
            stellar=_extract(line, col_positions, stellar_idx),
        )
        for line in data_lines
    ]


def _parse_sector_name(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith('# Sector:'):
            return line.partition(':')[2].strip() or fallback
    return fallback


def _sector_name_from_directory(sector_abbreviation: str, fallback: str) -> str:
    for sector in fetch_sectors():
        if sector.abbreviation.lower() == sector_abbreviation.lower() and sector.names:
            return sector.names[0]
    return fallback


def fetch_sector_coordinates(sector_abbreviation: str) -> tuple[int, int]:
    for sector in fetch_sectors():
        if sector.abbreviation.lower() == sector_abbreviation.lower():
            return sector.x, sector.y
    return 0, 0


def _parse_allegiance_names(text: str) -> dict[str, str]:
    allegiance_names: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith('# Alleg:'):
            continue
        payload = line[len('# Alleg:') :].strip()
        code, _, label = payload.partition(':')
        if not code or not label:
            continue
        allegiance_names[code.strip()] = label.strip().strip('"')
    return allegiance_names


def fetch_sectors(milieu: str = 'M1105') -> list[SectorInfo]:
    return [sector.model_copy(deep=True) for sector in _fetch_sectors_cached(milieu)]


@cache
def _fetch_sectors_cached(milieu: str) -> tuple[SectorInfo, ...]:
    payload = _fetch_text(_BASE_URL, params={'milieu': milieu})
    return tuple(SectorInfo.from_raw(s) for s in json.loads(payload).get('Sectors', []))


def fetch_sector_worlds(sector_abbreviation: str) -> list[SectorWorldEntry]:
    return fetch_sector(sector_abbreviation).worlds


def fetch_sector(sector_abbreviation: str) -> SectorData:
    return _fetch_sector_cached(sector_abbreviation).model_copy(deep=True)


@cache
def _fetch_sector_cached(sector_abbreviation: str) -> SectorData:
    payload = _fetch_text(f'{_BASE_URL}/{sector_abbreviation}')
    sector_name = _parse_sector_name(payload, sector_abbreviation)
    if sector_name == sector_abbreviation:
        sector_name = _sector_name_from_directory(sector_abbreviation, sector_abbreviation)
    return SectorData(
        abbreviation=sector_abbreviation,
        name=sector_name,
        allegiance_names=_parse_allegiance_names(payload),
        worlds=_parse_sec_worlds(payload),
    )


def clear_travellermap_memory_cache() -> None:
    _fetch_sectors_cached.cache_clear()
    _fetch_sector_cached.cache_clear()


def clear_travellermap_cache() -> None:
    clear_travellermap_memory_cache()
    cache_root = _cache_root()
    if not cache_root.exists():
        return
    for path in cache_root.glob('*.json'):
        path.unlink()


def fetch_world(sector_abbreviation: str, hex_code: str) -> TravellerMapWorld:
    payload = _fetch_json(f'{_BASE_URL}/{sector_abbreviation}/{hex_code}')
    worlds = payload.get('Worlds', [])
    if not worlds:
        raise ValueError(f'No world at {sector_abbreviation}/{hex_code}')
    return TravellerMapWorld.model_validate(worlds[0])
