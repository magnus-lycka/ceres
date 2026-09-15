"""World search and filter HTTP endpoints shared by character input widgets."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
import httpx2
from pydantic import JsonValue

from ceres.worlds import search_sectors
from ceres.worlds.search import world_search_area

router = APIRouter()


@router.get('/sectors')
def sectors(q: str = '') -> list[dict[str, JsonValue]]:
    try:
        return [sector.model_dump(mode='json') for sector in search_sectors(q)]
    except httpx2.HTTPError as exc:
        raise HTTPException(503, 'TravellerMap unavailable. Please retry.') from exc


@router.get('/worlds/{abbreviation}')
def worlds(
    abbreviation: str,
    request: Request,
    reference_hex: str | None = Query(
        default=None, pattern=r'^(?:|(?:0[1-9]|[12][0-9]|3[0-2])(?:0[1-9]|[123][0-9]|40))$'
    ),
) -> dict[str, JsonValue]:
    try:
        area = world_search_area(abbreviation, reference_hex or None)
        options = asdict(area.options)
        selected = area.filter_worlds(
            **{name: request.query_params.getlist(name) for name in options},
            world_query=request.query_params.get('q'),
            reference_hex=None,
            reference_sector_x=None,
            reference_sector_y=None,
        )
        return jsonable_encoder(
            {
                'name': area.sector_name,
                'options': options,
                'worlds': [world.model_dump(mode='json') for world in selected],
            }
        )
    except httpx2.HTTPError as exc:
        raise HTTPException(503, 'TravellerMap unavailable. Please retry.') from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
