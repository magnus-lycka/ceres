from collections.abc import Iterable
from dataclasses import dataclass, field

from ceres.adapters.travellermap import SectorInfo, SectorWorldEntry, fetch_sector, fetch_sectors

NO_ALLEGIANCE = 'No Allegiance'
UNKNOWN_UWP = '?'
DEFAULT_MILIEU = 'M1105'

UWP_STARPORT_INDEX = 0
UWP_SIZE_INDEX = 1
UWP_ATMOSPHERE_INDEX = 2
UWP_HYDROGRAPHICS_INDEX = 3
UWP_POPULATION_INDEX = 4
UWP_GOVERNMENT_INDEX = 5
UWP_LAW_LEVEL_INDEX = 6
UWP_TECH_LEVEL_INDEX = 8


@dataclass(frozen=True)
class SectorWorldOptions:
    allegiances: tuple[str, ...] = ()
    remarks: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()
    starports: tuple[str, ...] = ()
    sizes: tuple[str, ...] = ()
    atmospheres: tuple[str, ...] = ()
    hydrographics: tuple[str, ...] = ()
    populations: tuple[str, ...] = ()
    governments: tuple[str, ...] = ()
    law_levels: tuple[str, ...] = ()
    tech_levels: tuple[str, ...] = ()


def search_sectors(query: str, *, milieu: str = DEFAULT_MILIEU) -> list[SectorInfo]:
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

    @staticmethod
    def _sorted_strings(values: Iterable[str]) -> tuple[str, ...]:
        return tuple(sorted({value for value in values if value}))

    @staticmethod
    def _sort_uwp_codes(values: Iterable[str]) -> tuple[str, ...]:
        value_set = {value for value in values if value}

        def sort_key(code: str) -> tuple[int, str]:
            if code == UNKNOWN_UWP:
                return (1, code)
            return (0, code)

        return tuple(sorted(value_set, key=sort_key))

    @staticmethod
    def _normalize_selection[T](values: Iterable[T] | None) -> set[T] | None:
        if values is None:
            return None
        selected = set(values)
        return selected or None

    @staticmethod
    def _matches_selected_codes(selected: set[str] | None, value: str) -> bool:
        if selected is None:
            return True
        return value in selected

    @staticmethod
    def _remark_tokens(world: SectorWorldEntry) -> set[str]:
        return {token for token in world.remarks.split() if token}

    @staticmethod
    def _base_codes(world: SectorWorldEntry) -> set[str]:
        return {code for code in world.bases if code not in {'', '-'} and code.strip()}

    @staticmethod
    def _uwp_code(world: SectorWorldEntry, index: int) -> str:
        return world.uwp[index]

    def sorted_uwp_codes(self, index: int) -> tuple[str, ...]:
        return self._sort_uwp_codes(self._uwp_code(world, index) for world in self.worlds)

    @staticmethod
    def _hex_coordinates(hex_code: str) -> tuple[int, int]:
        return int(hex_code[:2]), int(hex_code[2:])

    @classmethod
    def hex_distance_parsecs(cls, origin_hex: str, destination_hex: str) -> int:
        # Even-Q vertical layout hex grid, coordinates down and right
        def even_q_to_cube(col, row):
            x = col
            z = row - (col + (col % 2)) // 2
            y = -x - z
            return x, y, z

        col1, row1 = cls._hex_coordinates(origin_hex)
        col2, row2 = cls._hex_coordinates(destination_hex)
        x1, y1, z1 = even_q_to_cube(col1, row1)
        x2, y2, z2 = even_q_to_cube(col2, row2)
        return max(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1))

    def world_distance_parsecs(self, reference_hex: str, world: SectorWorldEntry) -> int:
        return self.hex_distance_parsecs(reference_hex, world.hex)

    @staticmethod
    def _matches_world_query(world: SectorWorldEntry, world_query: str | None) -> bool:
        if world_query is None:
            return True
        needle = world_query.strip().lower()
        if not needle:
            return True
        return needle in world.name.lower() or needle in world.hex.lower()

    def _world_matches_filters(
        self,
        world: SectorWorldEntry,
        *,
        selected_allegiances: set[str] | None,
        selected_remarks: set[str] | None,
        selected_bases: set[str] | None,
        selected_starports: set[str] | None,
        selected_sizes: set[str] | None,
        selected_atmospheres: set[str] | None,
        selected_hydrographics: set[str] | None,
        selected_populations: set[str] | None,
        selected_governments: set[str] | None,
        selected_law_levels: set[str] | None,
        selected_tech_levels: set[str] | None,
        world_query: str | None,
    ) -> bool:
        matches_no_allegiance = (
            not world.allegiance and selected_allegiances is not None and NO_ALLEGIANCE in selected_allegiances
        )
        matches_allegiance = (
            selected_allegiances is None or world.allegiance in selected_allegiances or matches_no_allegiance
        )
        checks = (
            self._matches_world_query(world, world_query),
            matches_allegiance,
            selected_remarks is None or not self._remark_tokens(world).isdisjoint(selected_remarks),
            selected_bases is None or not self._base_codes(world).isdisjoint(selected_bases),
            selected_starports is None or world.starport in selected_starports,
            self._matches_selected_codes(selected_sizes, self._uwp_code(world, UWP_SIZE_INDEX)),
            self._matches_selected_codes(selected_atmospheres, self._uwp_code(world, UWP_ATMOSPHERE_INDEX)),
            self._matches_selected_codes(selected_hydrographics, self._uwp_code(world, UWP_HYDROGRAPHICS_INDEX)),
            self._matches_selected_codes(selected_populations, self._uwp_code(world, UWP_POPULATION_INDEX)),
            self._matches_selected_codes(selected_governments, self._uwp_code(world, UWP_GOVERNMENT_INDEX)),
            self._matches_selected_codes(selected_law_levels, self._uwp_code(world, UWP_LAW_LEVEL_INDEX)),
            self._matches_selected_codes(selected_tech_levels, self._uwp_code(world, UWP_TECH_LEVEL_INDEX)),
        )
        return all(checks)

    def _allegiance_options(self) -> tuple[str, ...]:
        values = {world.allegiance for world in self.worlds if world.allegiance}
        if any(not world.allegiance for world in self.worlds):
            values.add(NO_ALLEGIANCE)
        return tuple(sorted(values))

    @property
    def options(self) -> SectorWorldOptions:
        return SectorWorldOptions(
            allegiances=self._allegiance_options(),
            remarks=self._sorted_strings(token for world in self.worlds for token in self._remark_tokens(world)),
            bases=self._sorted_strings(code for world in self.worlds for code in self._base_codes(world)),
            starports=self.sorted_uwp_codes(UWP_STARPORT_INDEX),
            sizes=self.sorted_uwp_codes(UWP_SIZE_INDEX),
            atmospheres=self.sorted_uwp_codes(UWP_ATMOSPHERE_INDEX),
            hydrographics=self.sorted_uwp_codes(UWP_HYDROGRAPHICS_INDEX),
            populations=self.sorted_uwp_codes(UWP_POPULATION_INDEX),
            governments=self.sorted_uwp_codes(UWP_GOVERNMENT_INDEX),
            law_levels=self.sorted_uwp_codes(UWP_LAW_LEVEL_INDEX),
            tech_levels=self.sorted_uwp_codes(UWP_TECH_LEVEL_INDEX),
        )

    def filter_worlds(
        self,
        *,
        allegiances: Iterable[str] | None = None,
        remarks: Iterable[str] | None = None,
        bases: Iterable[str] | None = None,
        starports: Iterable[str] | None = None,
        sizes: Iterable[str] | None = None,
        atmospheres: Iterable[str] | None = None,
        hydrographics: Iterable[str] | None = None,
        populations: Iterable[str] | None = None,
        governments: Iterable[str] | None = None,
        law_levels: Iterable[str] | None = None,
        tech_levels: Iterable[str] | None = None,
        world_query: str | None = None,
        reference_hex: str | None = None,
    ) -> list[SectorWorldEntry]:
        selected_allegiances = self._normalize_selection(allegiances)
        selected_remarks = self._normalize_selection(remarks)
        selected_bases = self._normalize_selection(bases)
        selected_starports = self._normalize_selection(starports)
        selected_sizes = self._normalize_selection(sizes)
        selected_atmospheres = self._normalize_selection(atmospheres)
        selected_hydrographics = self._normalize_selection(hydrographics)
        selected_populations = self._normalize_selection(populations)
        selected_governments = self._normalize_selection(governments)
        selected_law_levels = self._normalize_selection(law_levels)
        selected_tech_levels = self._normalize_selection(tech_levels)

        matches = [
            world
            for world in self.worlds
            if self._world_matches_filters(
                world,
                selected_allegiances=selected_allegiances,
                selected_remarks=selected_remarks,
                selected_bases=selected_bases,
                selected_starports=selected_starports,
                selected_sizes=selected_sizes,
                selected_atmospheres=selected_atmospheres,
                selected_hydrographics=selected_hydrographics,
                selected_populations=selected_populations,
                selected_governments=selected_governments,
                selected_law_levels=selected_law_levels,
                selected_tech_levels=selected_tech_levels,
                world_query=world_query,
            )
        ]

        if reference_hex is not None:
            return sorted(
                matches,
                key=lambda world: (
                    self.world_distance_parsecs(reference_hex, world),
                    world.hex,
                    world.name,
                ),
            )

        return matches
