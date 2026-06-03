"""HTML routes for the character web UI."""

from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ceres.adapters.travellermap import TravellerMapWorld, fetch_world
from ceres.character.careers.loader import load_careers
from ceres.character.events import AnyEvent
from ceres.character.precareers import load_precareers
from ceres.character.replay import ReplayError
from ceres.character.report import render_npc_gallery_pdf
from ceres.character.sophonts import SOPHONT_NAMES, get_sophont
from ceres.character.spec import spec_from_summary
from ceres.character.state import (
    CharacterProjection,
    diff_summaries,
)
from ceres.character.store import SqliteCharacterBackend
from ceres.worlds import SectorWorldFilters, search_sectors

_TEMPLATES_DIR = Path(__file__).parent / 'templates'
_STRING_FILTER_GROUPS = ('allegiances', 'remarks', 'bases', 'starports')
_INT_FILTER_GROUPS = (
    'sizes',
    'atmospheres',
    'hydrographics',
    'populations',
    'governments',
    'law_levels',
    'tech_levels',
)


def _character_form_defaults(
    *,
    name: str = '',
    sophont: str = SOPHONT_NAMES[0],
    player: str = 'NPC',
    homeworld_sector: str = '',
    homeworld_hex: str = '',
) -> dict[str, str]:
    return {
        'name': name,
        'sophont': sophont,
        'player': player,
        'homeworld_sector': homeworld_sector,
        'homeworld_hex': homeworld_hex,
    }


def _character_form_defaults_from_request(request: Request) -> dict[str, str]:
    sophont = request.query_params.get('sophont', SOPHONT_NAMES[0]) or SOPHONT_NAMES[0]
    return _character_form_defaults(
        name=request.query_params.get('name', ''),
        sophont=sophont if sophont in SOPHONT_NAMES else SOPHONT_NAMES[0],
        player=request.query_params.get('player', 'NPC') or 'NPC',
        homeworld_sector=request.query_params.get('homeworld_sector', ''),
        homeworld_hex=request.query_params.get('homeworld_hex', ''),
    )


def _character_form_query_string(form_defaults: dict[str, str]) -> str:
    return urlencode({key: value for key, value in form_defaults.items() if value})


def _selected_homeworld(form_defaults: dict[str, str]) -> TravellerMapWorld | None:
    sector = form_defaults['homeworld_sector'].strip()
    hex_code = form_defaults['homeworld_hex'].strip()
    if not sector or not hex_code:
        return None
    return fetch_world(sector, hex_code)


def _projection_context(projection: CharacterProjection, character_id: int) -> dict[str, Any]:
    careers = load_careers()
    enriched_inputs = []
    for pi in projection.pending_inputs[:1]:
        input_specs = pi.input_specs(projection)
        extra: dict[str, Any] = {'careers': careers} if pi.kind == 'career_choice' else {}
        enriched_inputs.append({'input': pi, 'input_specs': input_specs, 'extra': extra})

    return {
        'projection': projection,
        'summary': projection.summary,
        'character_id': character_id,
        'enriched_inputs': enriched_inputs,
        'careers': careers,
        'precareers': {name: pc for name, pc in load_precareers().items() if pc.is_available(projection.summary)},
    }


def _selected_world_filters(request: Request) -> tuple[dict[str, set[str]], dict[str, set[str]], bool]:
    filters_active = request.query_params.get('filters') == '1'
    selected_strings: dict[str, set[str]] = {}
    selected_uwp_codes: dict[str, set[str]] = {}
    for group in _STRING_FILTER_GROUPS:
        values = [value for value in request.query_params.getlist(group) if value]
        if values:
            selected_strings[group] = set(values)
        elif not filters_active:
            selected_strings[group] = set()
    for group in _INT_FILTER_GROUPS:
        values = [value for value in request.query_params.getlist(group) if value]
        if values:
            selected_uwp_codes[group] = set(values)
        elif not filters_active:
            selected_uwp_codes[group] = set()
    return selected_strings, selected_uwp_codes, filters_active


def _normalize_world_filters_for_matching(
    selected_strings: dict[str, set[str]],
    selected_ints: dict[str, set[str]],
    sector: SectorWorldFilters,
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    normalized_strings = dict(selected_strings)
    normalized_ints = dict(selected_ints)

    for group in _STRING_FILTER_GROUPS:
        option_values = set(getattr(sector.options, group))
        if group in normalized_strings and normalized_strings[group] == option_values:
            normalized_strings.pop(group)

    for group in _INT_FILTER_GROUPS:
        option_values = set(getattr(sector.options, group))
        if group in normalized_ints and normalized_ints[group] == option_values:
            normalized_ints.pop(group)

    return normalized_strings, normalized_ints


def build_web_router(backend: SqliteCharacterBackend) -> APIRouter:
    from ceres.character.spec import format_npc_skills

    router = APIRouter()
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    templates.env.filters['format_skills'] = format_npc_skills

    @router.get('/', response_class=HTMLResponse)
    def list_characters(request: Request) -> Any:
        characters = backend.list_characters()
        return templates.TemplateResponse(
            request=request,
            name='characters.html',
            context={'characters': characters},
        )

    @router.get('/characters/new', response_class=HTMLResponse)
    def new_character_form(request: Request) -> Any:
        form_defaults = _character_form_defaults_from_request(request)
        try:
            homeworld = _selected_homeworld(form_defaults)
        except ValueError as exc:
            return templates.TemplateResponse(
                request=request,
                name='character_new.html',
                context={
                    'sophonts': SOPHONT_NAMES,
                    'error': str(exc),
                    'form_defaults': form_defaults,
                    'homeworld': None,
                    'homeworld_picker_query': _character_form_query_string(form_defaults),
                },
                status_code=422,
            )
        return templates.TemplateResponse(
            request=request,
            name='character_new.html',
            context={
                'sophonts': SOPHONT_NAMES,
                'form_defaults': form_defaults,
                'homeworld': homeworld,
                'homeworld_picker_query': _character_form_query_string(form_defaults),
            },
        )

    @router.get('/worlds/sectors', response_class=HTMLResponse)
    def sector_picker(request: Request) -> Any:
        form_defaults = _character_form_defaults_from_request(request)
        return templates.TemplateResponse(
            request=request,
            name='sector_picker.html',
            context={
                'form_defaults': form_defaults,
                'picker_query': _character_form_query_string(form_defaults),
            },
        )

    @router.get('/worlds/sectors/search', response_class=HTMLResponse)
    def sector_search(request: Request, q: str = '') -> Any:
        form_defaults = _character_form_defaults_from_request(request)
        matches = search_sectors(q)
        return templates.TemplateResponse(
            request=request,
            name='partials/sector_search_results.html',
            context={
                'matches': matches,
                'query': q,
                'picker_query': _character_form_query_string(form_defaults),
            },
        )

    @router.get('/worlds/sectors/{sector_abbreviation}', response_class=HTMLResponse)
    def sector_filters(request: Request, sector_abbreviation: str) -> Any:
        form_defaults = _character_form_defaults_from_request(request)
        sector = SectorWorldFilters.from_travellermap(sector_abbreviation)
        selected_strings, selected_ints, filters_active = _selected_world_filters(request)
        applied_strings, applied_ints = _normalize_world_filters_for_matching(selected_strings, selected_ints, sector)
        world_query = request.query_params.get('world_query', '').strip()
        filtered_worlds = sector.filter_worlds(
            allegiances=applied_strings.get('allegiances'),
            remarks=applied_strings.get('remarks'),
            bases=applied_strings.get('bases'),
            starports=applied_strings.get('starports'),
            sizes=applied_ints.get('sizes'),
            atmospheres=applied_ints.get('atmospheres'),
            hydrographics=applied_ints.get('hydrographics'),
            populations=applied_ints.get('populations'),
            governments=applied_ints.get('governments'),
            law_levels=applied_ints.get('law_levels'),
            tech_levels=applied_ints.get('tech_levels'),
            world_query=world_query,
        )
        selected: dict[str, set[str]] = {**selected_strings, **selected_ints}
        picker_query = _character_form_query_string(form_defaults)
        return templates.TemplateResponse(
            request=request,
            name='sector_filters.html',
            context={
                'sector': sector,
                'sector_name': sector.sector_name or sector_abbreviation,
                'options': sector.options,
                'filtered_worlds': filtered_worlds,
                'filtered_world_count': len(filtered_worlds),
                'selected': selected,
                'filters_active': filters_active,
                'world_query': world_query,
                'form_defaults': form_defaults,
                'picker_query': picker_query,
                'select_homeworld_base': f'/ui/characters/new?{picker_query}' if picker_query else '/ui/characters/new',
                'back_to_picker_url': f'/ui/worlds/sectors?{picker_query}' if picker_query else '/ui/worlds/sectors',
                'reset_filters_url': (
                    f'/ui/worlds/sectors/{sector.sector_abbreviation}?{picker_query}'
                    if picker_query
                    else f'/ui/worlds/sectors/{sector.sector_abbreviation}'
                ),
            },
        )

    @router.post('/characters/new')
    def create_character(
        request: Request,
        name: str = Form(...),
        sophont: str = Form(...),
        player: str = Form('NPC'),
        homeworld_sector: str = Form(''),
        homeworld_hex: str = Form(''),
    ) -> Any:
        name = name.strip()
        form_defaults = _character_form_defaults(
            name=name,
            sophont=sophont,
            player=player.strip() or 'NPC',
            homeworld_sector=homeworld_sector.strip(),
            homeworld_hex=homeworld_hex.strip(),
        )
        if not name:
            return templates.TemplateResponse(
                request=request,
                name='character_new.html',
                context={
                    'sophonts': SOPHONT_NAMES,
                    'error': 'Name is required',
                    'form_defaults': form_defaults,
                    'homeworld': None,
                    'homeworld_picker_query': _character_form_query_string(form_defaults),
                },
                status_code=422,
            )
        sophont_obj = get_sophont(sophont) or get_sophont(SOPHONT_NAMES[0])
        if sophont_obj is None:
            raise RuntimeError(f'No fallback sophont available: {sophont!r}')
        try:
            homeworld = _selected_homeworld(form_defaults)
        except ValueError as exc:
            return templates.TemplateResponse(
                request=request,
                name='character_new.html',
                context={
                    'sophonts': SOPHONT_NAMES,
                    'error': str(exc),
                    'form_defaults': form_defaults,
                    'homeworld': None,
                    'homeworld_picker_query': _character_form_query_string(form_defaults),
                },
                status_code=422,
            )
        if homeworld is None:
            return templates.TemplateResponse(
                request=request,
                name='character_new.html',
                context={
                    'sophonts': SOPHONT_NAMES,
                    'error': 'Homeworld is required',
                    'form_defaults': form_defaults,
                    'homeworld': None,
                    'homeworld_picker_query': _character_form_query_string(form_defaults),
                },
                status_code=422,
            )
        row = backend.start(
            sophont=sophont_obj,
            homeworld=homeworld,
            player=form_defaults['player'],
            name=name,
        )
        return RedirectResponse(url=f'/ui/characters/{row["id"]}/wizard', status_code=303)

    @router.get('/characters/{character_id}', response_class=HTMLResponse)
    def character_sheet(request: Request, character_id: int) -> Any:
        projection = backend.get_projection(character_id)
        if projection is None:
            return Response(status_code=404)
        ctx = _projection_context(projection, character_id)
        return templates.TemplateResponse(request=request, name='character.html', context=ctx)

    @router.get('/characters/{character_id}/wizard', response_class=HTMLResponse)
    def character_wizard(request: Request, character_id: int) -> Any:
        projection = backend.get_projection(character_id)
        if projection is None:
            return Response(status_code=404)
        ctx = {**_projection_context(projection, character_id), 'is_htmx': False}
        return templates.TemplateResponse(request=request, name='wizard.html', context=ctx)

    @router.post('/characters/delete')
    async def delete_characters(request: Request) -> Any:
        form = await request.form()
        for character_id in form.getlist('character_ids'):
            if isinstance(character_id, str):
                backend.delete_character(int(character_id))
        return RedirectResponse(url='/ui/', status_code=303)

    @router.post('/characters/{character_id}/delete')
    def delete_character(character_id: int) -> Any:
        backend.delete_character(character_id)
        return RedirectResponse(url='/ui/', status_code=303)

    @router.post('/characters/{character_id}/events', response_class=HTMLResponse)
    async def post_event(request: Request, character_id: int) -> Any:
        projection = backend.get_projection(character_id)
        if projection is None:
            return HTMLResponse('<p class="text-red-400">Character not found</p>', status_code=404)

        form = await request.form()
        fulfills = str(form.get('fulfills', ''))

        try:
            event = _build_event_from_form(fulfills, form, projection)
        except Exception as exc:
            ctx = {**_projection_context(projection, character_id), 'error': str(exc), 'changes': [], 'is_htmx': True}
            return templates.TemplateResponse(request=request, name='partials/pending_inputs.html', context=ctx)

        before_summary = projection.summary.model_copy(deep=True)

        try:
            backend.append_event(character_id, event)
        except ReplayError as exc:
            projection = backend.get_projection(character_id) or projection
            ctx = {**_projection_context(projection, character_id), 'error': str(exc), 'changes': [], 'is_htmx': True}
            return templates.TemplateResponse(request=request, name='partials/pending_inputs.html', context=ctx)

        projection = backend.get_projection(character_id)
        if projection is None:
            return HTMLResponse('<p class="text-red-400">Projection unavailable</p>', status_code=500)

        changes = diff_summaries(before_summary, projection.summary)
        ctx = {**_projection_context(projection, character_id), 'changes': changes, 'is_htmx': True}
        return templates.TemplateResponse(
            request=request,
            name='partials/pending_inputs.html',
            context=ctx,
        )

    @router.get('/characters/{character_id}/pdf')
    def character_pdf(character_id: int) -> Any:
        projection = backend.get_projection(character_id)
        if projection is None:
            return Response(status_code=404)
        spec = spec_from_summary(projection.summary)
        pdf = render_npc_gallery_pdf([spec])
        safe_name = (spec.name or 'character').replace(' ', '_')
        return Response(
            content=pdf,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{safe_name}.pdf"'},
        )

    @router.get('/careers/{career_name}/assignments', response_class=HTMLResponse)
    def get_career_assignments(request: Request, career_name: str) -> Any:
        careers = load_careers()
        career = careers.get(career_name)
        if career is None:
            return HTMLResponse('')
        assignments = [a.name for a in career.assignments]
        return templates.TemplateResponse(
            request=request,
            name='partials/assignments.html',
            context={'assignments': assignments},
        )

    return router


def _build_event_from_form(fulfills: str, form: Any, projection: CharacterProjection) -> AnyEvent:
    pending = next((p for p in projection.pending_inputs if p.id == fulfills), None)
    if pending is None:
        raise ValueError(f'No pending input with id={fulfills!r}')
    return pending.event_from_form(form)
