"""Bulk NPC generation engine for the character web gallery."""

from dataclasses import dataclass
import random
import re
from typing import Literal, cast

from ceres.character.careers.loader import load_careers
from ceres.character.characteristics import Chars
from ceres.character.events import (
    AdvancementDmChoiceEvent,
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    AnyEvent,
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    ConnectionKindChoiceEvent,
    ConnectionsRollEvent,
    InjuryTableEvent,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.projection import AnyPending, CharacterProjection
from ceres.character.replay import ReplayError
from ceres.character.skills import AnySkill, skill_class_by_name
from ceres.character.sophonts import SOPHONTS
from ceres.character.spec import NpcSpec, spec_from_summary
from ceres.character.store import SqliteCharacterBackend

BenefitTable = Literal['cash', 'benefits']
ConnectionKind = Literal['contact', 'ally', 'rival', 'enemy']

_CONNECTION_TYPE_RE = re.compile(r'\b(contacts?|allies|ally|rivals?|enemies|enemy)\b', re.IGNORECASE)
_CONNECTION_TYPE_MAP: dict[str, ConnectionKind] = {
    'contacts': 'contact',
    'allies': 'ally',
    'rivals': 'rival',
    'enemies': 'enemy',
}
_CHOOSE_COUNT_RE = re.compile(r'Choose (\d+)')


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


def _roll2d(rng: random.Random) -> int:
    return rng.randint(1, 6) + rng.randint(1, 6)


def _roll1d(rng: random.Random) -> int:
    return rng.randint(1, 6)


def _pick_skill(
    options: list[str],
    projection: CharacterProjection,
    rng: random.Random,
    level: int | None,
) -> AnySkill | None:
    """Return a random valid AnySkill from options, or None if none are valid."""
    valid = [o for o in options if o != 'advancement_dm_4']
    rng.shuffle(valid)
    for name in valid:
        try:
            cls = skill_class_by_name(name)
        except ValueError:
            continue
        choices = projection.skill_choices([cls], level)
        if choices:
            return rng.choice(choices)
    return None


def _connection_type(instruction: str) -> str:
    m = _CONNECTION_TYPE_RE.search(instruction)
    if not m:
        return 'contact'
    word = m.group(1).lower()
    return _CONNECTION_TYPE_MAP.get(word, word)


def _connection_kind(instruction: str) -> ConnectionKind:
    candidate = _connection_type(instruction)
    if candidate in ('contact', 'ally', 'rival', 'enemy'):
        return cast('ConnectionKind', candidate)
    return 'contact'


def _auto_event(
    pi: AnyPending,
    projection: CharacterProjection,
    params: CohortParams,
    rng: random.Random,
) -> AnyEvent:
    """Generate a random event to fulfill the given pending input."""
    kind = pi.kind
    f = pi.id

    if kind == 'ucp':
        ucp = ''.join(f'{_roll2d(rng):X}' for _ in range(6))
        return UcpEvent(ucp=ucp, fulfills=f)

    if kind == 'background_skills':
        m = _CHOOSE_COUNT_RE.search(pi.instruction)
        count = int(m.group(1)) if m else 3
        shuffled = list(pi.options)
        rng.shuffle(shuffled)
        skills: list[AnySkill] = []
        for name in shuffled:
            if len(skills) >= count:
                break
            try:
                cls = skill_class_by_name(name)
                skills.append(cast('AnySkill', cls()))
            except ValueError:
                pass
        return BackgroundSkillsEvent(skills=skills, fulfills=f)

    if kind == 'career_choice':
        careers = load_careers()
        career_data = careers.get(params.career)
        if career_data is None:
            career_data = careers[rng.choice(sorted(careers.keys()))]
        if params.assignment and any(a.name == params.assignment for a in career_data.assignments):
            assignment = params.assignment
        else:
            assignment = rng.choice([a.name for a in career_data.assignments])
        return CareerEvent(
            career=career_data.name,
            assignment=assignment,
            qualification_roll=12,
            fulfills=f,
        )

    if kind == 'survive':
        return SurviveEvent(roll=_roll2d(rng), fulfills=f)

    if kind == 'term_event':
        return TermEventEvent(roll=_roll2d(rng), fulfills=f)

    if kind == 'mishap':
        return MishapEvent(roll=_roll1d(rng), fulfills=f)

    if kind == 'advancement':
        return AdvancementEvent(roll=_roll2d(rng), fulfills=f)

    if kind == 'skill_table':
        table = rng.choice(pi.options) if pi.options else 'service_skills'
        return SkillTableEvent(table=table, roll=_roll1d(rng), fulfills=f)

    if kind in ('initial_training_choice', 'skill_table_choice', 'skill_choice', 'rank_bonus_choice'):
        level_val: int | None = 0 if kind == 'initial_training_choice' else getattr(pi, 'level', None)
        skill = _pick_skill(pi.options, projection, rng, level_val)
        if skill is not None:
            return SkillChoiceEvent(skill=skill, fulfills=f)
        return AdvancementDmChoiceEvent(fulfills=f)

    if kind == 'career_skill_choice':
        skill = _pick_skill(pi.options, projection, rng, None)
        if skill is not None:
            return SkillChoiceEvent(skill=skill, fulfills=f)
        return AdvancementDmChoiceEvent(fulfills=f)

    if kind == 'reenlist':
        return ReenlistEvent(reenlist=projection.summary.term_count < params.max_terms, fulfills=f)

    if kind == 'muster_out':
        table = rng.choice(cast('list[BenefitTable]', ['cash', 'benefits']))
        return MusterOutEvent(table=table, roll=_roll1d(rng), fulfills=f)

    if kind == 'aging_roll':
        return AgingRollEvent(roll=_roll2d(rng), fulfills=f)

    if kind in ('injury_table', 'nearly_killed'):
        return InjuryTableEvent(roll=_roll1d(rng), fulfills=f)

    if kind == 'life_event':
        return LifeEventEvent(roll=_roll2d(rng), fulfills=f)

    if kind == 'life_event_unusual':
        return LifeEventUnusualEvent(roll=_roll1d(rng), fulfills=f)

    if kind == 'connections_roll':
        ctype = _connection_kind(pi.instruction)
        return ConnectionsRollEvent(
            connection_type=ctype,
            count=_roll1d(rng),
            fulfills=f,
        )

    if kind in ('characteristic_choice', 'aging_choice', 'aging_choice_mental'):
        char = rng.choice(pi.options) if pi.options else 'STR'
        return CharacteristicChoiceEvent(characteristic=Chars(char), fulfills=f)

    if kind == 'life_event_choice':
        kinds: list[ConnectionKind] = ['contact', 'ally', 'rival', 'enemy']
        return ConnectionKindChoiceEvent(connection_kind=rng.choice(kinds), fulfills=f)

    if kind == 'aging_crisis':
        return AgingCrisisEvent(paid=False, medical_roll=0, fulfills=f)

    if kind in ('career_event', 'career_mishap'):
        career_name = getattr(pi, 'career', '')
        roll = getattr(pi, 'roll', 0)
        segment = 'event' if kind == 'career_event' else 'mishap'
        context = f'{career_name.lower()}_{segment}_{roll}'
        choice = rng.choice(list(pi.options)) if pi.options else ''
        return CareerChoiceEvent(context=context, choice=choice, fulfills=f)

    if kind == 'career_skill_roll':
        context = getattr(pi, 'context', '')
        skill_str = rng.choice(pi.options) if pi.options else 'Admin'
        try:
            skill: AnySkill | Chars = Chars(skill_str)
        except ValueError:
            skill = cast('AnySkill', skill_class_by_name(skill_str)())
        return SkillRollEvent(context=context, skill=skill, modified_roll=_roll2d(rng), fulfills=f)

    raise ValueError(f'Unknown pending input kind: {kind!r}')


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
    for _ in range(500):
        projection = backend.get_projection(cid)
        if projection is None or not projection.pending_inputs:
            break
        pi = projection.pending_inputs[0]
        for _retry in range(20):
            event = _auto_event(pi, projection, params, rng)
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
