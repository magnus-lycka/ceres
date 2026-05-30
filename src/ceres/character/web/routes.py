"""HTML routes for the character web UI."""

from pathlib import Path
import re
from typing import Any, Literal, cast

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import TypeAdapter

from ceres.character.careers.loader import load_careers, selectable_careers
from ceres.character.characteristics import UCP_STATS, Chars, ConnectionKind
from ceres.character.events import (
    AdvancementDmChoiceEvent,
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    AnyEvent,
    AssignmentChangeChoiceEvent,
    BackgroundSkillsEvent,
    BenefitChoiceEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CommissionEvent,
    ConnectionKindChoiceEvent,
    ConnectionsRollEvent,
    DraftAssignmentEvent,
    DraftEvent,
    FinishCreationEvent,
    InjuryTableEvent,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
    PreCareerEntryEvent,
    PreCareerEventEvent,
    PreCareerGraduationEvent,
    PreCareerSkillChoiceEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.precareers import load_precareers
from ceres.character.projection import (
    CharacterProjection,
    CharacterSummary,
    PendingConnectionsRoll,
    PendingInputBase,
    _level_fields,
)
from ceres.character.replay import ReplayError
from ceres.character.report import render_npc_gallery_pdf
from ceres.character.skills import AnySkill, skill_class_by_name
from ceres.character.sophonts import SOPHONT_NAMES, get_sophont
from ceres.character.spec import spec_from_summary
from ceres.character.store import SqliteCharacterBackend
from ceres.character.web.bulk import _NPC_DEFAULT_HOMEWORLD

_TEMPLATES_DIR = Path(__file__).parent / 'templates'
_skill_adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)

# kind values that produce SkillChoiceEvent
_SKILL_CHOICE_KINDS = frozenset(
    {
        'initial_training_choice',
        'skill_table_choice',
        'skill_choice',
        'rank_bonus_choice',
    }
)

MusterOutTable = Literal['cash', 'benefits']


def _form_str(form: Any, key: str, default: str = '') -> str:
    value = form.get(key, default)
    if not isinstance(value, str):
        return default
    return value


def _form_int(form: Any, key: str, default: int) -> int:
    value = _form_str(form, key, str(default))
    return int(value or default)


def _literal(value: str, allowed: tuple[str, ...], default: str) -> str:
    if value in allowed:
        return value
    return default


def _skill_class_or_none(name: str) -> type[AnySkill] | None:
    try:
        return cast(type[AnySkill], skill_class_by_name(name))
    except ValueError:
        return None


_DRAFT_TABLE: dict[int, str] = {
    1: 'Navy',
    2: 'Army',
    3: 'Marines',
    4: 'Merchant',
    5: 'Scout',
    6: 'Agent',
}

_NON_SKILL_OPTION_LABELS: dict[str, str] = {
    'advancement_dm_4': 'DM+4 to next advancement roll',
}


def _compute_skill_choices_for_pending(pi: PendingInputBase, projection: CharacterProjection) -> list[tuple[str, str]]:
    """Return (display_label, json_value) pairs for skill-choice pending inputs."""
    kind = pi.kind
    results: list[tuple[str, str]] = []

    if kind == 'background_skills':
        for opt in pi.options:
            skill_cls = _skill_class_or_none(opt)
            if skill_cls is None:
                continue
            skill = skill_cls()
            results.append((opt, _skill_adapter.dump_json(skill).decode()))
        return results

    if kind == 'initial_training_choice':
        level: int | None = 0
    elif kind == 'rank_bonus_choice':
        level = getattr(pi, 'level', None)
    else:
        # skill_choice, skill_table_choice, career_skill_choice: increment
        level = None

    for opt in pi.options:
        if opt in _NON_SKILL_OPTION_LABELS:
            results.append((_NON_SKILL_OPTION_LABELS[opt], opt))
            continue

        skill_cls = _skill_class_or_none(opt)
        if skill_cls is None:
            continue

        if level == 0:
            skill = skill_cls()
            results.append((opt, _skill_adapter.dump_json(skill).decode()))
        else:
            choices = projection.skill_choices([skill_cls], level)
            for skill in choices:
                label = opt
                fields = _level_fields(skill_cls)
                if len(fields) > 1:
                    for fname, sname in zip(fields, skill_cls.specialities(), strict=False):
                        given = getattr(skill, fname).value
                        if given > 0:
                            label = f'{opt} ({sname})'
                            break
                results.append((label, _skill_adapter.dump_json(skill).decode()))

    return results


def _build_event_from_form(kind: str, fulfills: str, form: Any) -> AnyEvent:
    """Construct the correct AnyEvent from form data."""
    f = fulfills or None

    if kind == 'ucp':
        ucp = ''.join(f'{_form_int(form, stat, 0):X}' for stat in UCP_STATS)
        return UcpEvent(ucp=ucp, fulfills=f)

    if kind == 'background_skills':
        raw = form.getlist('skill')
        skills = [_skill_adapter.validate_json(j) for j in raw]
        return BackgroundSkillsEvent(skills=skills, fulfills=f)

    if kind == 'finish_creation':
        return FinishCreationEvent(fulfills=f)

    if kind == 'precareer_entry':
        precareer = _form_str(form, 'precareer', 'University')
        roll = _form_int(form, 'roll', 7)
        return PreCareerEntryEvent(precareer=precareer, roll=roll, fulfills=f)

    if kind == 'precareer_skill_choice':
        skill = _form_str(form, 'skill')
        return PreCareerSkillChoiceEvent(skill=skill, fulfills=f)

    if kind == 'precareer_event':
        return PreCareerEventEvent(roll=_form_int(form, 'roll', 7), fulfills=f)

    if kind == 'precareer_graduation':
        return PreCareerGraduationEvent(roll=_form_int(form, 'roll', 7), fulfills=f)

    if kind == 'career_choice':
        career = _form_str(form, 'career')
        assignment = _form_str(form, 'assignment')
        roll = _form_int(form, 'roll', 2)
        return CareerEvent(career=career, assignment=assignment, qualification_roll=roll, fulfills=f)

    if kind == 'draft_choice':
        choice = _form_str(form, 'choice', 'drifter')
        if choice == 'draft':
            roll = _form_int(form, 'roll', 1)
            career = _DRAFT_TABLE.get(roll, 'Navy')
            return DraftEvent(career=career, fulfills=f)
        assignment = _form_str(form, 'assignment', 'Wanderer')
        return CareerEvent(career='Drifter', assignment=assignment, qualification_roll=2, fulfills=f)

    if kind == 'draft_assignment_choice':
        return DraftAssignmentEvent(
            career=_form_str(form, 'career'),
            assignment=_form_str(form, 'assignment'),
            fulfills=f,
        )

    if kind == 'commission_choice':
        choice = _form_str(form, 'choice', 'skip')
        if choice == 'attempt':
            return CommissionEvent(attempt=True, roll=_form_int(form, 'roll', 7), fulfills=f)
        return CommissionEvent(attempt=False, fulfills=f)

    if kind == 'assignment_change_choice':
        choice = _form_str(form, 'choice', 'muster_out')
        roll = _form_int(form, 'roll', 7) if choice not in ('same', 'muster_out') else None
        return AssignmentChangeChoiceEvent(choice=choice, qualification_roll=roll, fulfills=f)

    if kind == 'career_skill_choice':
        skill_str = _form_str(form, 'skill', '{}')
        if skill_str == 'advancement_dm_4':
            return AdvancementDmChoiceEvent(fulfills=f)
        skill = _skill_adapter.validate_json(skill_str)
        return SkillChoiceEvent(skill=skill, fulfills=f)

    if kind in _SKILL_CHOICE_KINDS:
        skill_json = _form_str(form, 'skill', '{}')
        skill = _skill_adapter.validate_json(skill_json)
        return SkillChoiceEvent(skill=skill, fulfills=f)

    if kind == 'survive':
        return SurviveEvent(roll=_form_int(form, 'roll', 2), fulfills=f)

    if kind == 'term_event':
        return TermEventEvent(roll=_form_int(form, 'roll', 2), fulfills=f)

    if kind == 'mishap':
        return MishapEvent(roll=_form_int(form, 'roll', 1), fulfills=f)

    if kind == 'skill_table':
        table = _form_str(form, 'table')
        roll = _form_int(form, 'roll', 1)
        return SkillTableEvent(table=table, roll=roll, fulfills=f)

    if kind == 'advancement':
        return AdvancementEvent(roll=_form_int(form, 'roll', 2), fulfills=f)

    if kind == 'advancement_dm_choice':
        return AdvancementDmChoiceEvent(fulfills=f)

    if kind == 'reenlist':
        reenlist = _form_str(form, 'reenlist', 'false').lower() in ('true', '1', 'yes')
        return ReenlistEvent(reenlist=reenlist, fulfills=f)

    if kind == 'muster_out':
        table = cast(MusterOutTable, _literal(_form_str(form, 'table', 'benefits'), ('cash', 'benefits'), 'benefits'))
        roll = _form_int(form, 'roll', 1)
        return MusterOutEvent(table=table, roll=roll, fulfills=f)

    if kind == 'aging_roll':
        return AgingRollEvent(roll=_form_int(form, 'roll', 2), fulfills=f)

    if kind in ('injury_table', 'nearly_killed'):
        return InjuryTableEvent(roll=_form_int(form, 'roll', 1), fulfills=f)

    if kind == 'life_event':
        return LifeEventEvent(roll=_form_int(form, 'roll', 2), fulfills=f)

    if kind == 'life_event_unusual':
        return LifeEventUnusualEvent(roll=_form_int(form, 'roll', 1), fulfills=f)

    if kind == 'connections_roll':
        raw_ct = _literal(_form_str(form, 'connection_type', 'contact'), tuple(ConnectionKind), 'contact')
        count = _form_int(form, 'count', 1)
        return ConnectionsRollEvent(connection_type=ConnectionKind(raw_ct), count=count, fulfills=f)

    if kind in ('characteristic_choice', 'aging_choice', 'aging_choice_mental'):
        characteristic = Chars(_form_str(form, 'characteristic', Chars.STR))
        return CharacteristicChoiceEvent(characteristic=characteristic, fulfills=f)

    if kind == 'life_event_choice':
        raw_ck = _literal(_form_str(form, 'connection_kind', 'rival'), tuple(ConnectionKind), 'rival')
        return ConnectionKindChoiceEvent(connection_kind=ConnectionKind(raw_ck), fulfills=f)

    if kind == 'aging_crisis':
        paid = _form_str(form, 'paid', 'false').lower() in ('true', '1', 'yes')
        medical_roll = _form_int(form, 'medical_roll', 0)
        return AgingCrisisEvent(paid=paid, medical_roll=medical_roll, fulfills=f)

    if kind == 'benefit_choice_pending':
        choice_index = _form_int(form, 'choice_index', 0)
        return BenefitChoiceEvent(choice_index=choice_index, fulfills=f)

    if kind in ('career_event', 'career_mishap'):
        career = _form_str(form, 'career')
        roll = _form_int(form, 'roll', 0)
        segment = 'event' if kind == 'career_event' else 'mishap'
        context = f'{career.lower()}_{segment}_{roll}'
        choice = _form_str(form, 'choice', '')
        return CareerChoiceEvent(context=context, choice=choice, fulfills=f)

    if kind == 'career_skill_roll':
        context = _form_str(form, 'context')
        skill_str = _form_str(form, 'skill')
        modified_roll = _form_int(form, 'modified_roll', 8)
        try:
            skill: AnySkill | Chars = Chars(skill_str)
        except ValueError:
            skill = _skill_adapter.validate_python({'type': skill_str})
        return SkillRollEvent(context=context, skill=skill, modified_roll=modified_roll, fulfills=f)

    raise ValueError(f'Unknown pending input kind: {kind!r}')


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
        extra: dict[str, Any] = {}
        kind = pi.kind

        if kind in _SKILL_CHOICE_KINDS:
            extra['skill_choices'] = _compute_skill_choices_for_pending(pi, projection)

        elif kind == 'background_skills':
            extra['skill_choices'] = _compute_skill_choices_for_pending(pi, projection)
            # Parse count from instruction: "Choose N background skill(s)"
            m = re.search(r'Choose (\d+)', pi.instruction)
            extra['bg_count'] = int(m.group(1)) if m else 1

        elif kind == 'career_choice':
            extra['careers'] = careers

        elif kind == 'draft_choice':
            drifter = careers.get('Drifter')
            extra['drifter_assignments'] = [a.name for a in drifter.assignments] if drifter else ['Wanderer']

        elif kind == 'connections_roll':
            extra['connection_type'] = cast(PendingConnectionsRoll, pi).connection_type

        elif kind == 'life_event_choice':
            # roll 4 → rival/enemy, roll 8 → rival/enemy (same options)
            extra['connection_options'] = ['rival', 'enemy']

        elif kind == 'career_skill_choice':
            extra['skill_choices'] = _compute_skill_choices_for_pending(pi, projection)

        enriched_inputs.append({'input': pi, 'extra': extra})

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
            event = _build_event_from_form(kind, fulfills, form)
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
        career_name = _form_str(form, 'career')
        assignment = _form_str(form, 'assignment') or None
        sophont = _form_str(form, 'sophont', SOPHONT_NAMES[0])
        min_terms = max(1, _form_int(form, 'min_terms', 2))
        max_terms = max(min_terms, _form_int(form, 'max_terms', 4))
        count = min(20, max(1, _form_int(form, 'count', 4)))
        name_prefix = _form_str(form, 'name_prefix', 'NPC').strip() or 'NPC'

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
        career_name = _form_str(form, 'career')
        assignment = _form_str(form, 'assignment') or None
        sophont = _form_str(form, 'sophont', SOPHONT_NAMES[0])
        min_terms = max(1, _form_int(form, 'min_terms', 2))
        max_terms = max(min_terms, _form_int(form, 'max_terms', 4))
        count = min(20, max(1, _form_int(form, 'count', 4)))
        name_prefix = _form_str(form, 'name_prefix', 'NPC').strip() or 'NPC'

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
