"""HTML routes for the character web UI."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ceres.character.careers.loader import load_careers, selectable_careers
from ceres.character.events import (
    AnyEvent,
    PreCareerEntryEvent,
)
from ceres.character.input_specs import form_int, form_str
from ceres.character.precareers import load_precareers
from ceres.character.projection import (
    CharacterProjection,
    CharacterSummary,
)
from ceres.character.replay import ReplayError
from ceres.character.report import render_npc_gallery_pdf
from ceres.character.sophonts import SOPHONT_NAMES, get_sophont
from ceres.character.spec import spec_from_summary
from ceres.character.store import SqliteCharacterBackend
from ceres.character.web.bulk import _NPC_DEFAULT_HOMEWORLD

_TEMPLATES_DIR = Path(__file__).parent / 'templates'


def _diff_summaries(before: CharacterSummary, after: CharacterSummary) -> list[str]:
    """Return human-readable strings describing mechanical changes between two summaries."""
    changes: list[str] = []

    # Narrative (story events: survive result, mishaps, life events)
    changes.extend(after.narrative[len(before.narrative) :])

    # Career/assignment joined
    if after.current_career != before.current_career and after.current_career:
        line = f'Joined {after.current_career}'
        if after.current_assignment:
            line += f' ({after.current_assignment})'
        changes.append(line)

    # Rank
    if after.rank is not None and after.rank != before.rank:
        changes.append(f'Rank {before.rank or 0} → {after.rank}')

    # Characteristics
    all_chars = set(before.characteristics) | set(after.characteristics)
    for char in sorted(all_chars, key=lambda c: c.value):
        b_val = before.characteristics.get(char, 0)
        a_val = after.characteristics.get(char, 0)
        if a_val != b_val:
            changes.append(f'{char.value} {b_val} → {a_val}')

    # Skills
    before_by_name = {type(s).name(): s for s in before.skills}
    after_by_name = {type(s).name(): s for s in after.skills}
    for name in sorted(set(after_by_name) - set(before_by_name)):
        level = after.skill_level(name, 0)
        changes.append(f'Gained {name} {level}')
    for name in sorted(set(after_by_name) & set(before_by_name)):
        b_lvl = before.skill_level(name, 0)
        a_lvl = after.skill_level(name, 0)
        if a_lvl != b_lvl:
            changes.append(f'{name} {b_lvl} → {a_lvl}')

    # Cash
    if after.cash != before.cash:
        delta = after.cash - before.cash
        sign = '+' if delta > 0 else ''
        changes.append(f'Cash {sign}Cr{delta:,}')

    # Benefits
    changes.extend(f'Benefit: {b.display_label}' for b in after.benefits[len(before.benefits) :])

    # Connections
    changes.extend(f'New {c.kind}: {c.source or "unknown"}' for c in after.connections[len(before.connections) :])

    # Problems
    changes.extend(f'Problem: {p}' for p in after.problems[len(before.problems) :])

    return changes


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
        return templates.TemplateResponse(
            request=request,
            name='character_new.html',
            context={'sophonts': SOPHONT_NAMES},
        )

    @router.post('/characters/new')
    def create_character(
        request: Request,
        name: str = Form(...),
        sophont: str = Form(...),
        player: str = Form('NPC'),
    ) -> Any:
        name = name.strip()
        if not name:
            return templates.TemplateResponse(
                request=request,
                name='character_new.html',
                context={'sophonts': SOPHONT_NAMES, 'error': 'Name is required'},
                status_code=422,
            )
        sophont_obj = get_sophont(sophont) or get_sophont(SOPHONT_NAMES[0])
        if sophont_obj is None:
            raise RuntimeError(f'No fallback sophont available: {sophont!r}')
        row = backend.start(
            sophont=sophont_obj,
            homeworld=_NPC_DEFAULT_HOMEWORLD,
            player=player.strip() or 'NPC',
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
        kind = str(form.get('kind', ''))
        fulfills = str(form.get('fulfills', ''))

        try:
            event = _build_event_from_form(kind, fulfills, form, projection)
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

        changes = _diff_summaries(before_summary, projection.summary)
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

    @router.get('/gallery/new', response_class=HTMLResponse)
    def gallery_form(request: Request) -> Any:
        careers = selectable_careers()
        return templates.TemplateResponse(
            request=request,
            name='gallery_form.html',
            context={'careers': careers, 'sophonts': SOPHONT_NAMES},
        )

    @router.post('/gallery/generate', response_class=HTMLResponse)
    async def gallery_generate(request: Request) -> Any:
        from ceres.character.web.bulk import CohortParams, generate_cohort

        form = await request.form()
        career_name = form_str(form, 'career')
        assignment = form_str(form, 'assignment') or None
        sophont = form_str(form, 'sophont', SOPHONT_NAMES[0])
        min_terms = max(1, form_int(form, 'min_terms', 2))
        max_terms = max(min_terms, form_int(form, 'max_terms', 4))
        count = min(20, max(1, form_int(form, 'count', 4)))
        name_prefix = form_str(form, 'name_prefix', 'NPC').strip() or 'NPC'

        params = CohortParams(
            career=career_name,
            assignment=assignment,
            sophont=sophont,
            min_terms=min_terms,
            max_terms=max_terms,
            name_prefix=name_prefix,
        )
        specs = generate_cohort(backend, params, count)
        return templates.TemplateResponse(
            request=request,
            name='gallery.html',
            context={'specs': specs, 'params': params},
        )

    @router.post('/gallery/pdf')
    async def gallery_pdf(request: Request) -> Any:
        from ceres.character.web.bulk import CohortParams, generate_cohort

        form = await request.form()
        career_name = form_str(form, 'career')
        assignment = form_str(form, 'assignment') or None
        sophont = form_str(form, 'sophont', SOPHONT_NAMES[0])
        min_terms = max(1, form_int(form, 'min_terms', 2))
        max_terms = max(min_terms, form_int(form, 'max_terms', 4))
        count = min(20, max(1, form_int(form, 'count', 4)))
        name_prefix = form_str(form, 'name_prefix', 'NPC').strip() or 'NPC'

        params = CohortParams(
            career=career_name,
            assignment=assignment,
            sophont=sophont,
            min_terms=min_terms,
            max_terms=max_terms,
            name_prefix=name_prefix,
        )
        specs = generate_cohort(backend, params, count)
        pdf = render_npc_gallery_pdf(specs)
        safe = (career_name or 'npcs').replace(' ', '_').lower()
        return Response(
            content=pdf,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{safe}_gallery.pdf"'},
        )

    return router


def _build_event_from_form(kind: str, fulfills: str, form: Any, projection: CharacterProjection) -> AnyEvent:
    """Construct the correct AnyEvent from form data, routing via the pending input."""
    if kind == 'precareer_entry':
        precareer = form_str(form, 'precareer', 'University')
        roll = form_int(form, 'roll', 7)
        return PreCareerEntryEvent(precareer=precareer, roll=roll, fulfills=fulfills or None)

    pending = next((p for p in projection.pending_inputs if p.id == fulfills), None)
    if pending is None:
        raise ValueError(f'No pending input with id={fulfills!r}')
    return pending.event_from_form(form)
