from typing import Any, ClassVar, cast

from pydantic import BaseModel, ConfigDict

from ceres.character.domain.career.career_data import (
    CareerEventEntry,
    CharCheck,
    GainAllyEffect,
    GainConnectionsRolledEffect,
    GainEnemyEffect,
    GainRivalEffect,
    GainSkillEffect,
    LifeEventEffect,
    SkillChoiceEffect,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.dice import DiceRoll
from ceres.character.domain.skills import AnySkill, Carouse, Level, level_fields
from ceres.character.domain.term_data import TermData


class PrecareerSkillEntry(BaseModel):
    """Skill entry used in pre-career skill lists.

    A single skill is a fixed grant/choice. A list of skills represents a broad
    category choice, matching the career skill table pattern.
    """

    skill: AnySkill | list[AnySkill] | None = None
    level: int = 0
    spec: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def skill_options(self) -> list[AnySkill]:
        if self.skill is None:
            return []
        if isinstance(self.skill, list):
            return self.skill
        return [self.skill]

    @property
    def category_label(self) -> str:
        if self.skill is None:
            return 'skill'
        if isinstance(self.skill, list):
            return 'skill'
        return type(self.skill).name()

    def grant_skill(self) -> AnySkill | None:
        if self.skill is None or isinstance(self.skill, list):
            return None
        return _skill_at_level(self.skill, self.level)


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
    events: ClassVar[dict[int, CareerEventEntry]] = {
        2: CareerEventEntry(text='Approached by an illegal psionic group.', effects=[]),
        3: CareerEventEntry(text='Your time in education is not happy and you fail to graduate.', effects=[]),
        4: CareerEventEntry(text='A prank goes wrong and someone gets hurt.', effects=[]),
        5: CareerEventEntry(
            text='Taking advantage of youth, you party as much as you study.',
            effects=[GainSkillEffect(skill=Carouse())],
        ),
        6: CareerEventEntry(
            text='You become involved in a tightly knit clique or group.',
            effects=[GainConnectionsRolledEffect(connection_type=ConnectionKind.ALLY, dice=DiceRoll.parse('d3'))],
        ),
        7: CareerEventEntry(text='Life Event.', effects=[LifeEventEffect()]),
        8: CareerEventEntry(
            text='You join a political movement.',
            effects=[GainAllyEffect(), GainEnemyEffect()],
        ),
        9: CareerEventEntry(
            text='You develop a healthy interest in a hobby or other area of study.',
            effects=[SkillChoiceEffect(options=[], level=0)],
        ),
        10: CareerEventEntry(
            text='A tutor rubs you up the wrong way and you overturn their conclusions.',
            effects=[GainRivalEffect()],
        ),
        11: CareerEventEntry(text='War comes and a wide-ranging draft is instigated.', effects=[]),
        12: CareerEventEntry(text='You gain wide-ranging recognition.', effects=[]),
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
    skill_choices: ClassVar[list[PrecareerSkillEntry]] = []
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

    def is_available(self, summary: CharacterSummary) -> bool:
        """Return True if this precareer is available for the given character."""
        return True

    def prepare_entry(self, projection: CharacterProjection, roll: int, terms_started: int) -> bool:
        """Apply pre-career-specific entry preparation and return whether entry succeeds."""
        return True

    def apply_entry(
        self,
        projection: CharacterProjection,
        event: Any,
        pending_idx: int,
    ) -> int:
        """Default: generic companion entry — auto-grant fixed skills, queue picks for categories."""
        from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice

        if self.entry_pick_count == 0:
            for entry in self.skill_choices:
                if not entry.skill:
                    continue
                if isinstance(entry.skill, list):
                    options = entry.skill_options
                    instr = f'{self.name}: choose one {entry.category_label} specialisation at level {entry.level}'
                    projection.pending_inputs.append(
                        PendingPreCareerSkillChoice(
                            pending_id=(event.id, pending_idx),
                            level=entry.level,
                            instruction=instr,
                            options=options,
                        )
                    )
                    pending_idx += 1
                elif grant := entry.grant_skill():
                    projection.grant_skill(grant)
        else:
            choice_pool: list[AnySkill] = []
            for entry in self.skill_choices:
                if not entry.skill:
                    continue
                if entry.level >= 1:
                    if isinstance(entry.skill, list):
                        options = entry.skill_options
                        instr = f'{self.name}: choose one {entry.category_label} specialisation at level {entry.level}'
                        projection.pending_inputs.append(
                            PendingPreCareerSkillChoice(
                                pending_id=(event.id, pending_idx),
                                level=entry.level,
                                instruction=instr,
                                options=options,
                            )
                        )
                        pending_idx += 1
                    elif grant := entry.grant_skill():
                        projection.grant_skill(grant)
                else:
                    choice_pool.extend(entry.skill_options)
            for i in range(self.entry_pick_count):
                instr = f'{self.name}: choose skill {i + 1} of {self.entry_pick_count} at level 0'
                projection.pending_inputs.append(
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
        event: Any,
        honours: bool,
    ) -> int:
        """Default: no graduation effects. Returns pending_idx (0)."""
        return 0

    def apply_failed_graduation(
        self,
        projection: CharacterProjection,
        event: Any,
    ) -> None:
        """Default: no effects on failed graduation."""
