import httpx
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_pascal

from ceres.shared import ehex_to_int

_BASE_URL = 'https://travellermap.com/data'


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
            abbreviation=raw['Abbreviation'],
            tags=raw['Tags'],
            names=[n['Text'] for n in raw.get('Names', [])],
        )


class SectorWorldEntry(BaseModel):
    hex: str
    name: str
    uwp: str
    remarks: str


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
    if len(lines) < 3:
        return []

    header, separator, *data_lines = lines
    col_positions = _parse_column_positions(separator)
    fields = [header[s:e].strip().lower() for s, e in col_positions]

    hex_idx = fields.index('hex')
    name_idx = fields.index('name')
    uwp_idx = fields.index('uwp')
    remarks_idx = fields.index('remarks')

    return [
        SectorWorldEntry(
            hex=_extract(line, col_positions, hex_idx),
            name=_extract(line, col_positions, name_idx),
            uwp=_extract(line, col_positions, uwp_idx),
            remarks=_extract(line, col_positions, remarks_idx),
        )
        for line in data_lines
    ]


def fetch_sectors(milieu: str = 'M1105') -> list[SectorInfo]:
    with httpx.Client() as client:
        response = client.get(_BASE_URL, params={'milieu': milieu})
        response.raise_for_status()
        return [SectorInfo.from_raw(s) for s in response.json().get('Sectors', [])]


def fetch_sector_worlds(sector_abbreviation: str) -> list[SectorWorldEntry]:
    with httpx.Client() as client:
        response = client.get(f'{_BASE_URL}/{sector_abbreviation}')
        response.raise_for_status()
        return _parse_sec_worlds(response.text)


def fetch_world(sector_abbreviation: str, hex_code: str) -> TravellerMapWorld:
    with httpx.Client() as client:
        response = client.get(f'{_BASE_URL}/{sector_abbreviation}/{hex_code}')
        response.raise_for_status()
        worlds = response.json().get('Worlds', [])
        if not worlds:
            raise ValueError(f'No world at {sector_abbreviation}/{hex_code}')
        return TravellerMapWorld.model_validate(worlds[0])
