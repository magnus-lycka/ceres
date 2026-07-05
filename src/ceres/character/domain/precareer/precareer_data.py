from typing import Annotated, Any, ClassVar, cast

from pydantic import BaseModel, BeforeValidator, ConfigDict, PlainSerializer

from ceres.character.domain.career.career_data import (
    CareerTableEntry,
    CharCheck,
    GainConnectionEntry,
    GainConnectionsEntry,
    GainSkillEntry,
    LifeEventEntry,
    NoEffectEntry,
    RolledConnectionsEntry,
    SkillChoiceEntry,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.dice import DiceRoll
from ceres.character.domain.skills import AnySkill, Carouse, Level, level_fields
from ceres.character.domain.term_data import Term, TermData
from ceres.character.mechanism.event_base import Event


class PrecareerEntryBase(BaseModel):
    """A skill entry in a pre-career skill list. Knows how to grant or offer itself."""

    level: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def skill_options(self) -> list[AnySkill]:
        raise NotImplementedError

    def apply(self, precareer_name: str, projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        """Grant this entry directly or queue a choice; return the next pending index."""
        raise NotImplementedError


class PrecareerSkill(PrecareerEntryBase):
    """A single fixed skill granted at the entry's level."""

    skill: AnySkill

    @property
    def skill_options(self) -> list[AnySkill]:
        return [self.skill]

    def apply(self, precareer_name: str, projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.grant_skill(_skill_at_level(self.skill, self.level))
        return pending_idx


class PrecareerSkillChoice(PrecareerEntryBase):
    """A choice among several skills, gained at the entry's level."""

    skills: tuple[AnySkill, ...]

    @property
    def skill_options(self) -> list[AnySkill]:
        return list(self.skills)

    def apply(self, precareer_name: str, projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice

        projection.queue_deferred(
            PendingPreCareerSkillChoice(
                pending_id=(event_id, pending_idx),
                level=self.level,
                instruction=f'{precareer_name}: choose one skill specialisation at level {self.level}',
                options=self.skill_options,
            )
        )
        return pending_idx + 1


def _skill_at_level(skill: AnySkill, level: int) -> AnySkill:
    skill_cls = type(skill)
    cls = cast(type[Any], skill_cls)
    fields = level_fields(skill_cls)
    if level == 0:
        return cast(AnySkill, cls())
    if len(fields) == 1 and fields[0] == 'level':
        return cast(AnySkill, cls(level=Level(value=level)))
    active = [field for field in fields if getattr(skill, field).value > 0]
    selected = active or fields
    values = {field: Level(value=level if field in selected else 0) for field in fields}
    return cast(AnySkill, cls(**values))


class PreCareerData(TermData):
    events: ClassVar[dict[int, CareerTableEntry]] = {
        2: NoEffectEntry(text='Approached by an illegal psionic group.'),
        3: NoEffectEntry(text='Your time in education is not happy and you fail to graduate.'),
        4: NoEffectEntry(text='A prank goes wrong and someone gets hurt.'),
        5: GainSkillEntry(
            text='Taking advantage of youth, you party as much as you study.',
            skill=Carouse(),
        ),
        6: RolledConnectionsEntry(
            text='You become involved in a tightly knit clique or group.',
            connection=ConnectionKind.ALLY,
            dice=DiceRoll.parse('d3'),
        ),
        7: LifeEventEntry(text='Life Event.'),
        8: GainConnectionsEntry(
            text='You join a political movement.',
            connections=[ConnectionKind.ALLY, ConnectionKind.ENEMY],
        ),
        9: SkillChoiceEntry(
            text='You develop a healthy interest in a hobby or other area of study.',
            level=0,
        ),
        10: GainConnectionEntry(
            text='A tutor rubs you up the wrong way and you overturn their conclusions.',
            connection=ConnectionKind.RIVAL,
        ),
        11: NoEffectEntry(text='War comes and a wide-ranging draft is instigated.'),
        12: NoEffectEntry(text='You gain wide-ranging recognition.'),
    }
    name: ClassVar[str]
    source: ClassVar[str]
    duration_years: ClassVar[int] = 4
    entry: ClassVar[CharCheck | None] = None
    entry_requirement: ClassVar[str | None] = None
    entry_dms: ClassVar[dict[str, int]] = {}
    entry_term_dms: ClassVar[dict[int, int]] = {}
    entry_soc_bonus_min: ClassVar[int | None] = None
    entry_soc_bonus: ClassVar[int] = 0
    curriculum_table: ClassVar[str | None] = None
    skill_choices: ClassVar[list[PrecareerEntryBase]] = []
    # entry_pick_count > 0: level>=1 skills in skill_choices are auto-granted; player
    # picks entry_pick_count from the level==0 skills. If 0, all skill_choices are auto-granted.
    # University and military academies handle their own entry logic separately.
    entry_pick_count: ClassVar[int] = 0
    tied_career: ClassVar[str | None] = None
    graduation: ClassVar[CharCheck | None] = None
    graduation_requirement: ClassVar[str | None] = None
    graduation_dms: ClassVar[dict[str, int]] = {}
    honours_target: ClassVar[int | None] = None
    graduation_benefits: ClassVar[list[str]] = []

    term_class: ClassVar[type[PreCareerTerm]]

    def make_term(self) -> PreCareerTerm:
        return type(self).term_class(precareer=self)

    def is_available(self, summary: CharacterSummary) -> bool:
        """Return True if this precareer is available for the given character."""
        return True

    def prepare_entry(self, projection: CharacterProjection, roll: int, terms_started: int) -> bool:
        """Apply pre-career-specific entry preparation and return whether entry succeeds."""
        return True

    def apply_entry(
        self,
        projection: CharacterProjection,
        event: Event,
        pending_idx: int,
    ) -> int:
        """Default: generic companion entry — auto-grant fixed skills, queue picks for categories."""
        from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice

        if self.entry_pick_count == 0:
            for entry in self.skill_choices:
                pending_idx = entry.apply(self.name, projection, event.id, pending_idx)
        else:
            choice_pool: list[AnySkill] = []
            for entry in self.skill_choices:
                if entry.level >= 1:
                    pending_idx = entry.apply(self.name, projection, event.id, pending_idx)
                else:
                    choice_pool.extend(entry.skill_options)
            for i in range(self.entry_pick_count):
                instr = f'{self.name}: choose skill {i + 1} of {self.entry_pick_count} at level 0'
                projection.queue_deferred(
                    PendingPreCareerSkillChoice(
                        pending_id=(event.id, pending_idx),
                        level=0,
                        instruction=instr,
                        options=choice_pool,
                    )
                )
                pending_idx += 1
        return pending_idx

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: Event,
        honours: bool,
    ) -> int:
        """Default: no graduation effects. Returns pending_idx (0)."""
        return 0

    def apply_failed_graduation(
        self,
        projection: CharacterProjection,
        event: Event,
    ) -> None:
        """Default: no effects on failed graduation."""


def _deserialise_precareer(v: object) -> object:
    if isinstance(v, PreCareerData):
        return v
    from ceres.character.domain.precareer.loader import precareer_from_user_input_name

    pc = precareer_from_user_input_name(str(v))
    if pc is None:
        raise ValueError(f'Unknown pre-career: {v!r}')
    return pc


_PreCareerField = Annotated[Any, BeforeValidator(_deserialise_precareer), PlainSerializer(lambda pc: pc.name)]


class PreCareerTerm(Term):
    kind: str = ''  # discriminator; concrete subclasses set to a Literal
    precareer: _PreCareerField
    completed: bool = False
    graduated: bool = False
    honours: bool = False

    def apply_entry(self, projection: CharacterProjection, event: Event, pending_idx: int) -> int:
        return self.precareer.apply_entry(projection, event, pending_idx)

    def apply_graduation(self, projection: CharacterProjection, event: Event, honours: bool) -> int:
        return self.precareer.apply_graduation(projection, event, honours)

    def apply_failed_graduation(self, projection: CharacterProjection, event: Event) -> None:
        self.precareer.apply_failed_graduation(projection, event)
