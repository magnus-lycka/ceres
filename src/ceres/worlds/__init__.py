from collections.abc import Iterable
from dataclasses import dataclass, field

from ceres.adapters.travellermap import SectorInfo, SectorWorldEntry, fetch_sector, fetch_sectors

NO_ALLEGIANCE = 'No Allegiance'
UNKNOWN_UWP = '?'


@dataclass(frozen=True)
class SectorWorldOptions:
    allegiances: tuple[str, ...] = ()
    remarks: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()
    starports: tuple[str, ...] = ()
    sizes: tuple[int | str, ...] = ()
    atmospheres: tuple[int | str, ...] = ()
    hydrographics: tuple[int | str, ...] = ()
    populations: tuple[int | str, ...] = ()
    governments: tuple[int | str, ...] = ()
    law_levels: tuple[int | str, ...] = ()
    tech_levels: tuple[int | str, ...] = ()


def _sorted_strings(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


def _sorted_uwp_values(values: Iterable[int | None]) -> tuple[int | str, ...]:
    values_list = list(values)
    known_values = sorted({value for value in values_list if value is not None})
    if any(value is None for value in values_list):
        return (UNKNOWN_UWP, *known_values)
    return tuple(known_values)


def _remark_tokens(world: SectorWorldEntry) -> set[str]:
    return {token for token in world.remarks.split() if token}


def _base_codes(world: SectorWorldEntry) -> set[str]:
    return {code for code in world.bases if code not in {'', '-'} and code.strip()}


def _normalize_selection[T](values: Iterable[T] | None) -> set[T] | None:
    if values is None:
        return None
    selected = set(values)
    return selected or None


def _matches_uwp_selection(selected: set[int | str] | None, value: int | None) -> bool:
    if selected is None:
        return True
    if value is None:
        return UNKNOWN_UWP in selected
    return value in selected


def _allegiance_options(worlds: Iterable[SectorWorldEntry]) -> tuple[str, ...]:
    values = {world.allegiance for world in worlds if world.allegiance}
    if any(not world.allegiance for world in worlds):
        values.add(NO_ALLEGIANCE)
    return tuple(sorted(values))


def search_sectors(query: str, *, milieu: str = 'M1105') -> list[SectorInfo]:
    needle = query.strip().lower()
    if not needle:
        return []

    def score(sector: SectorInfo) -> tuple[int, str]:
        abbreviation = sector.abbreviation.lower()
        names = [name.lower() for name in sector.names]
        if abbreviation == needle:
            rank = 0
        elif abbreviation.startswith(needle):
            rank = 1
        elif any(name.startswith(needle) for name in names):
            rank = 2
        elif needle in abbreviation:
            rank = 3
        else:
            rank = 4
        return (rank, sector.abbreviation)

    sectors = fetch_sectors(milieu)
    exact_abbreviation_matches = [sector for sector in sectors if sector.abbreviation.lower() == needle]
    if exact_abbreviation_matches:
        return sorted(exact_abbreviation_matches, key=score)
    matches = [
        sector
        for sector in sectors
        if needle in sector.abbreviation.lower() or any(needle in name.lower() for name in sector.names)
    ]
    return sorted(matches, key=score)


@dataclass(frozen=True)
class SectorWorldFilters:
    worlds: list[SectorWorldEntry] = field(default_factory=list)
    sector_abbreviation: str | None = None
    sector_name: str | None = None
    allegiance_names: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_travellermap(cls, sector_abbreviation: str) -> SectorWorldFilters:
        sector = fetch_sector(sector_abbreviation)
        return cls(
            worlds=sector.worlds,
            sector_abbreviation=sector.abbreviation,
            sector_name=sector.name,
            allegiance_names=sector.allegiance_names,
        )

    @property
    def options(self) -> SectorWorldOptions:
        return SectorWorldOptions(
            allegiances=_allegiance_options(self.worlds),
            remarks=_sorted_strings(token for world in self.worlds for token in _remark_tokens(world)),
            bases=_sorted_strings(code for world in self.worlds for code in _base_codes(world)),
            starports=_sorted_strings(world.starport for world in self.worlds),
            sizes=_sorted_uwp_values(world.size for world in self.worlds),
            atmospheres=_sorted_uwp_values(world.atmosphere for world in self.worlds),
            hydrographics=_sorted_uwp_values(world.hydrographics for world in self.worlds),
            populations=_sorted_uwp_values(world.population for world in self.worlds),
            governments=_sorted_uwp_values(world.government for world in self.worlds),
            law_levels=_sorted_uwp_values(world.law_level for world in self.worlds),
            tech_levels=_sorted_uwp_values(world.tl for world in self.worlds),
        )

    def filter_worlds(
        self,
        *,
        allegiances: Iterable[str] | None = None,
        remarks: Iterable[str] | None = None,
        bases: Iterable[str] | None = None,
        starports: Iterable[str] | None = None,
        sizes: Iterable[int | str] | None = None,
        atmospheres: Iterable[int | str] | None = None,
        hydrographics: Iterable[int | str] | None = None,
        populations: Iterable[int | str] | None = None,
        governments: Iterable[int | str] | None = None,
        law_levels: Iterable[int | str] | None = None,
        tech_levels: Iterable[int | str] | None = None,
    ) -> list[SectorWorldEntry]:
        selected_allegiances = _normalize_selection(allegiances)
        selected_remarks = _normalize_selection(remarks)
        selected_bases = _normalize_selection(bases)
        selected_starports = _normalize_selection(starports)
        selected_sizes = _normalize_selection(sizes)
        selected_atmospheres = _normalize_selection(atmospheres)
        selected_hydrographics = _normalize_selection(hydrographics)
        selected_populations = _normalize_selection(populations)
        selected_governments = _normalize_selection(governments)
        selected_law_levels = _normalize_selection(law_levels)
        selected_tech_levels = _normalize_selection(tech_levels)

        matches: list[SectorWorldEntry] = []
        for world in self.worlds:
            matches_no_allegiance = (
                not world.allegiance and selected_allegiances is not None and NO_ALLEGIANCE in selected_allegiances
            )
            if (
                selected_allegiances is not None
                and world.allegiance not in selected_allegiances
                and not matches_no_allegiance
            ):
                continue
            if selected_remarks is not None and _remark_tokens(world).isdisjoint(selected_remarks):
                continue
            if selected_bases is not None and _base_codes(world).isdisjoint(selected_bases):
                continue
            if selected_starports is not None and world.starport not in selected_starports:
                continue
            if not _matches_uwp_selection(selected_sizes, world.size):
                continue
            if not _matches_uwp_selection(selected_atmospheres, world.atmosphere):
                continue
            if not _matches_uwp_selection(selected_hydrographics, world.hydrographics):
                continue
            if not _matches_uwp_selection(selected_populations, world.population):
                continue
            if not _matches_uwp_selection(selected_governments, world.government):
                continue
            if not _matches_uwp_selection(selected_law_levels, world.law_level):
                continue
            if not _matches_uwp_selection(selected_tech_levels, world.tl):
                continue
            matches.append(world)
        return matches


__all__ = ['NO_ALLEGIANCE', 'UNKNOWN_UWP', 'SectorWorldFilters', 'SectorWorldOptions', 'search_sectors']
