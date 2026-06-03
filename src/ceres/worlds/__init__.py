from collections.abc import Iterable
from dataclasses import dataclass, field

from ceres.adapters.travellermap import SectorInfo, SectorWorldEntry, fetch_sector, fetch_sectors

NO_ALLEGIANCE = 'No Allegiance'


@dataclass(frozen=True)
class SectorWorldOptions:
    allegiances: tuple[str, ...] = ()
    remarks: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()
    starports: tuple[str, ...] = ()
    sizes: tuple[int, ...] = ()
    atmospheres: tuple[int, ...] = ()
    hydrographics: tuple[int, ...] = ()
    populations: tuple[int, ...] = ()
    governments: tuple[int, ...] = ()
    law_levels: tuple[int, ...] = ()
    tech_levels: tuple[int, ...] = ()


def _sorted_strings(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))


def _sorted_ints(values: Iterable[int]) -> tuple[int, ...]:
    return tuple(sorted(set(values)))


def _remark_tokens(world: SectorWorldEntry) -> set[str]:
    return {token for token in world.remarks.split() if token}


def _base_codes(world: SectorWorldEntry) -> set[str]:
    return {code for code in world.bases if code not in {'', '-'} and code.strip()}


def _normalize_selection[T](values: Iterable[T] | None) -> set[T] | None:
    if values is None:
        return None
    selected = set(values)
    return selected or None


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
            sizes=_sorted_ints(world.size for world in self.worlds),
            atmospheres=_sorted_ints(world.atmosphere for world in self.worlds),
            hydrographics=_sorted_ints(world.hydrographics for world in self.worlds),
            populations=_sorted_ints(world.population for world in self.worlds),
            governments=_sorted_ints(world.government for world in self.worlds),
            law_levels=_sorted_ints(world.law_level for world in self.worlds),
            tech_levels=_sorted_ints(world.tl for world in self.worlds),
        )

    def filter_worlds(
        self,
        *,
        allegiances: Iterable[str] | None = None,
        remarks: Iterable[str] | None = None,
        bases: Iterable[str] | None = None,
        starports: Iterable[str] | None = None,
        sizes: Iterable[int] | None = None,
        atmospheres: Iterable[int] | None = None,
        hydrographics: Iterable[int] | None = None,
        populations: Iterable[int] | None = None,
        governments: Iterable[int] | None = None,
        law_levels: Iterable[int] | None = None,
        tech_levels: Iterable[int] | None = None,
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
            if selected_sizes is not None and world.size not in selected_sizes:
                continue
            if selected_atmospheres is not None and world.atmosphere not in selected_atmospheres:
                continue
            if selected_hydrographics is not None and world.hydrographics not in selected_hydrographics:
                continue
            if selected_populations is not None and world.population not in selected_populations:
                continue
            if selected_governments is not None and world.government not in selected_governments:
                continue
            if selected_law_levels is not None and world.law_level not in selected_law_levels:
                continue
            if selected_tech_levels is not None and world.tl not in selected_tech_levels:
                continue
            matches.append(world)
        return matches


__all__ = ['NO_ALLEGIANCE', 'SectorWorldFilters', 'SectorWorldOptions', 'search_sectors']
