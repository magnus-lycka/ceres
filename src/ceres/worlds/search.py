"""World search areas with locations preserved across sector boundaries."""

from ceres.adapters import travellermap
from ceres.worlds.sector_filters import SectorWorldFilters

REFERENCE_SEARCH_RADIUS = 12


class LocatedWorld(travellermap.SectorWorldEntry):
    sector: str
    sector_abbreviation: str
    distance: int | None = None


def world_search_area(reference_sector: str, reference_hex: str | None) -> SectorWorldFilters:
    if not reference_hex:
        sector = SectorWorldFilters.from_travellermap(reference_sector)
        return SectorWorldFilters(
            sector_name=sector.sector_name,
            worlds=[
                LocatedWorld(
                    **world.model_dump(),
                    sector=sector.sector_name or reference_sector,
                    sector_abbreviation=sector.sector_abbreviation or reference_sector,
                )
                for world in sector.worlds
            ],
        )
    origin_x, origin_y = travellermap.fetch_sector_coordinates(reference_sector)
    worlds = travellermap.fetch_jump_worlds(reference_sector, reference_hex, REFERENCE_SEARCH_RADIUS)
    coordinates = {
        abbreviation: travellermap.fetch_sector_coordinates(abbreviation)
        for abbreviation in {world.sector_abbreviation for world in worlds}
    }
    located = []
    for world in worlds:
        x, y = coordinates[world.sector_abbreviation]
        located.append(
            LocatedWorld(
                **world.model_dump(),
                world_count=str(world.worlds),
                distance=SectorWorldFilters.sector_hex_distance_parsecs(
                    origin_sector_x=origin_x,
                    origin_sector_y=origin_y,
                    origin_hex=reference_hex,
                    destination_sector_x=x,
                    destination_sector_y=y,
                    destination_hex=world.hex,
                ),
            )
        )
    located.sort(key=lambda world: (world.distance, world.sector_abbreviation, world.hex))
    return SectorWorldFilters(
        sector_name=f'{REFERENCE_SEARCH_RADIUS} pc of {reference_sector} {reference_hex}',
        worlds=list(located),
    )
