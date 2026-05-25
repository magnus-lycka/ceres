"""Bulk NPC generation engine for the character web gallery."""

from dataclasses import dataclass
import random

from ceres.character.careers.loader import load_careers
from ceres.character.projection import AutoFillContext
from ceres.character.replay import ReplayError
from ceres.character.sophonts import SOPHONTS
from ceres.character.spec import NpcSpec, spec_from_summary
from ceres.character.store import SqliteCharacterBackend


@dataclass(frozen=True)
class CohortParams:
    career: str
    assignment: str | None
    sophont: str
    min_terms: int
    max_terms: int
    name_prefix: str


def _npc_rng() -> random.Random:
    """Return a non-cryptographic RNG for deterministic Traveller NPC generation."""
    # Game/NPC generation, not security or cryptography.
    return random.Random()  # nosec B311


def generate_npc(
    backend: SqliteCharacterBackend,
    params: CohortParams,
    *,
    name: str,
    rng: random.Random | None = None,
) -> NpcSpec:
    """Generate a single NPC by auto-piloting the character creation engine."""
    if rng is None:
        rng = _npc_rng()
    sophont = params.sophont if params.sophont in SOPHONTS else 'Humaniti'
    row = backend.start(sophont=sophont, player='NPC', name=name)
    cid = row['id']
    ctx = AutoFillContext(
        career=params.career,
        assignment=params.assignment,
        max_terms=params.max_terms,
        careers=load_careers(),
    )
    for _ in range(500):
        projection = backend.get_projection(cid)
        if projection is None or not projection.pending_inputs:
            break
        pi = projection.pending_inputs[0]
        for _retry in range(20):
            event = projection.auto_event(pi, ctx, rng)
            try:
                backend.append_event(cid, event)
                break
            except ValueError, RuntimeError, ReplayError:
                if _retry == 19:
                    raise
    else:
        raise RuntimeError(f'NPC generation did not complete after 500 steps for character {cid}')
    projection = backend.get_projection(cid)
    if projection is None:
        raise RuntimeError(f'Could not load projection for character {cid}')
    return spec_from_summary(projection.summary)


def generate_cohort(
    backend: SqliteCharacterBackend,
    params: CohortParams,
    count: int,
    rng: random.Random | None = None,
) -> list[NpcSpec]:
    """Generate a cohort of NPCs matching the given params."""
    if rng is None:
        rng = _npc_rng()
    return [generate_npc(backend, params, name=f'{params.name_prefix} {i}', rng=rng) for i in range(1, count + 1)]


__all__ = ['CohortParams', 'generate_cohort', 'generate_npc']
