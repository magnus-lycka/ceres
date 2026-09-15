"""Client-facing character views; domain objects stop at this boundary."""

from dataclasses import asdict

from pydantic import BaseModel, Field, JsonValue
from pydantic_core import to_jsonable_python

from ceres.character.domain.career.career_events import PendingCareerChoice
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.precareer.precareer_data import PreCareerTerm
from ceres.character.domain.precareer.precareer_events import PendingPreCareerGraduation
from ceres.character.domain.spec import format_stat_block_skills


class PendingView(BaseModel):
    id: str
    instruction: str
    inputs: list[dict[str, JsonValue]]


class CharacterView(BaseModel):
    id: int
    name: str
    age: int
    age_display: str
    term_status: str | None
    rank_display: str | None
    sophont: str
    homeworld: str
    ucp: str
    characteristics: dict[str, int]
    skills: str
    cash: int
    benefits: list[str]
    history: list[str]
    connections: list[str]
    problems: list[str]
    finished: bool
    pending: PendingView | None
    changes: list[str] = Field(default_factory=list)


def character_view(character_id: int, projection: CharacterProjection) -> CharacterView:
    summary = projection.summary
    pending = projection.pending_inputs[0] if projection.pending_inputs else None
    term_status, age_display = _term_progress(projection)
    return CharacterView(
        id=character_id,
        name=summary.name,
        age=summary.age,
        age_display=age_display,
        term_status=term_status,
        rank_display=('Rank ' + ' · '.join(part for part in summary.rank_title if part))
        if summary.rank is not None
        else None,
        sophont=summary.sophont.name if summary.sophont else '',
        homeworld=summary.homeworld.name if summary.homeworld else '',
        ucp=summary.ucp or '',
        characteristics={str(key): value for key, value in summary.characteristics.items()},
        skills=format_stat_block_skills(summary.skills),
        cash=summary.cash,
        benefits=[benefit.display_label for benefit in summary.benefits],
        history=list(summary.narrative),
        connections=[
            f'{connection.display_name}: {connection.name or connection.origin or ""}'
            + (f' — {connection.note}' if connection.note else '')
            for connection in summary.connections
        ],
        problems=summary.problems,
        finished=pending is None,
        pending=PendingView(
            id=pending.id,
            instruction=pending.instruction,
            inputs=[
                {'kind': type(spec).__name__, **to_jsonable_python(asdict(spec))}
                for spec in pending.input_specs(projection)
            ],
        )
        if pending
        else None,
    )


def _term_progress(projection: CharacterProjection) -> tuple[str | None, str]:
    summary = projection.summary
    if not projection.pending_inputs:
        return None, str(summary.age)
    pending = projection.pending_inputs[0]
    number = len(summary.terms)
    if not summary.terms or isinstance(pending, PendingCareerChoice):
        return f'Starting term {number + 1}', str(summary.age)
    term = summary.terms[-1]
    end_age = term.start_age + 4
    if isinstance(term, PreCareerTerm):
        ending = term.completed or isinstance(pending, PendingPreCareerGraduation)
    else:
        ending = summary.age >= end_age
    if ending:
        return f'Ending term {number}', str(summary.age)
    return f'In term {number}', f'{term.start_age}–{end_age}'
