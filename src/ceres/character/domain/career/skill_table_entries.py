"""Skill table entry types. Each entry knows how to apply itself to a character."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast, get_args, get_origin

from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, model_validator

from ceres.character.domain.characteristics import Chars
from ceres.character.domain.psionics_data import (
    PsionicTalentSkillClass,
    psionic_talent_classes,
)
from ceres.character.domain.skills import AnySkill, Level, Skill as SkillModel, SpecRef, level_fields
from ceres.character.mechanism.event_base import Event, EventHandlerBase

if TYPE_CHECKING:
    from ceres.character.domain.character_state import CharacterProjection


def skill_with_levels(skill_cls: type[AnySkill], fields: Iterable[str], level: int = 1) -> AnySkill:
    """Build a skill instance with runtime-chosen specialisation fields set.

    The field names are decided at runtime, so the mapping is genuinely dynamic.
    Saying so once, here, keeps a type checker from matching every key against
    every parameter of all 60+ classes in the skill union — which it otherwise
    reports as one error per variant, per call site.
    """
    levels: dict[str, Any] = {field: Level(value=level) for field in fields}
    return skill_cls(**levels)


def expand_skill_classes(skills: object) -> tuple[type[AnySkill], ...]:
    """Expand a skill class, TypeAliasType alias, or union to a tuple of concrete skill classes."""
    if hasattr(skills, '__value__'):
        skills = skills.__value__
    if get_origin(skills) is Annotated:
        skills = get_args(skills)[0]
    args = get_args(skills)
    if args:
        return tuple(args)
    if isinstance(skills, type) and issubclass(skills, SkillModel):
        # issubclass has established this at runtime; AnySkill is the union of
        # concrete Skill subclasses, which a checker cannot infer from the base.
        return (cast(type[AnySkill], skills),)
    raise ValueError(f'Cannot expand {skills!r} to skill classes')


def expand_talent_classes(talents: object) -> tuple[PsionicTalentSkillClass, ...]:
    """Expand a union of psionic talent classes to a tuple of concrete talent classes."""
    if hasattr(talents, '__value__'):
        talents = talents.__value__
    if get_origin(talents) is Annotated:
        talents = get_args(talents)[0]
    args = get_args(talents)
    if args:
        classes = psionic_talent_classes()
        result = tuple(a for a in args if a in classes)
        if result:
            return result
    raise ValueError(f'Cannot expand {talents!r} to psionic talent classes')


def _skill_class_by_kind(kind: str) -> type[AnySkill]:
    cls: Any = AnySkill
    if hasattr(cls, '__value__'):
        cls = cls.__value__
    if get_origin(cls) is Annotated:
        cls = get_args(cls)[0]
    for skill_cls in get_args(cls):
        if skill_cls.model_fields['kind'].default == kind:
            return skill_cls
    raise ValueError(f'No skill class with kind {kind!r}')


def _validate_skill_class(v: object) -> type[AnySkill]:
    if isinstance(v, str):
        return _skill_class_by_kind(v)
    if isinstance(v, type) and issubclass(v, SkillModel):
        return cast(type[AnySkill], v)
    raise ValueError(f'Expected a skill class or kind string, got {v!r}')


SkillClassRef = Annotated[
    type[AnySkill],
    BeforeValidator(_validate_skill_class),
    PlainSerializer(lambda cls: cls.model_fields['kind'].default, return_type=str),
]


def _validate_spec_ref(v: object) -> SpecRef:
    if isinstance(v, SpecRef):
        return v
    if isinstance(v, dict):
        data = cast(dict[str, str], v)
        return SpecRef(_skill_class_by_kind(data['skill']), data['field'])
    raise ValueError(f'Expected a SpecRef or mapping, got {v!r}')


SpecRefField = Annotated[
    SpecRef,
    BeforeValidator(_validate_spec_ref),
    PlainSerializer(lambda ref: {'skill': ref.kind(), 'field': ref.field}, return_type=dict),
]


@dataclass
class SkillTableApplyContext:
    """Carries the event and application mode for a skill table entry apply() call."""

    event: Event
    level: int | None = None
    _idx: int = field(default=0, init=False)

    def next_pending_id(self) -> tuple[int, int]:
        result = (self.event.id, self._idx)
        self._idx += 1
        return result


class SkillTableEntryBase(BaseModel):
    """A cell in a career skill table. Knows how to apply itself to a character."""

    def apply(self, projection: CharacterProjection, ctx: SkillTableApplyContext) -> None:
        raise NotImplementedError

    def label(self) -> str:
        raise NotImplementedError

    def basic_training_candidates(self, projection: CharacterProjection) -> tuple[AnySkill, ...]:
        """Skills this entry contributes to basic training (unknown skills only)."""
        return ()

    def select_options(self, projection: CharacterProjection, level: int | None) -> list[tuple[str, str]]:
        """(label, form_value) pairs for offering this entry on a choice form."""
        return [(self.label(), self.model_dump_json())]

    def is_available(self, projection: CharacterProjection, level: int | None) -> bool:
        """Whether offering this entry would still benefit the character."""
        return True

    def chosen_handler(self) -> EventHandlerBase:
        """The event handler that applies this entry when it is chosen on a form."""
        from ceres.character.domain.career.career_events import SkillTableEntryChosenHandler

        return SkillTableEntryChosenHandler(entry=cast('SkillTableItem', self))


class Char(SkillTableEntryBase):
    kind: Literal['ste_char'] = 'ste_char'
    characteristic: Chars

    def __init__(self, characteristic: Chars, **kwargs: object) -> None:
        super().__init__(characteristic=characteristic, **kwargs)

    def apply(self, projection: CharacterProjection, ctx: SkillTableApplyContext) -> None:
        chars = projection.summary.characteristics
        chars[self.characteristic] = chars.get(self.characteristic, 0) + 1

    def label(self) -> str:
        return f'{self.characteristic} +1'


class Skill(SkillTableEntryBase):
    kind: Literal['ste_skill'] = 'ste_skill'
    skill: SkillClassRef
    level: int | None = None
    specs: tuple[SpecRefField, ...] | None = None

    model_config = {'arbitrary_types_allowed': True}

    def __init__(self, skill: type[AnySkill], level: int | None = None, specs: object = None, **kwargs: object) -> None:
        super().__init__(skill=skill, level=level, specs=specs, **kwargs)

    @model_validator(mode='after')
    def _specs_belong_to_skill(self) -> Skill:
        for ref in self.specs or ():
            if ref.skill_cls is not self.skill:
                raise ValueError(f'Specialization {ref!r} does not belong to {self.skill.name()}')
            if ref.field not in level_fields(self.skill):
                raise ValueError(f'{self.skill.name()} has no specialization {ref.field!r}')
        return self

    def _allowed_fields(self) -> list[str]:
        if self.specs:
            return [ref.field for ref in self.specs]
        return level_fields(self.skill)

    def _marker_instance(self) -> AnySkill:
        """Instance with each allowed specialization set — marks the restriction for option building.

        The field names are chosen at runtime, so the mapping is genuinely
        dynamic: `dict[str, Any]` states that, rather than inviting a type
        checker to match every key against every parameter of all 60+ skill
        classes in the union.
        """
        return skill_with_levels(self.skill, self._allowed_fields())

    def apply(self, projection: CharacterProjection, ctx: SkillTableApplyContext) -> None:
        effective_level = ctx.level if ctx.level is not None else self.level
        allowed = self._allowed_fields()
        if effective_level == 0:
            projection.grant_skill(self.skill())
        elif len(allowed) > 1:
            self._queue_specialization_choice(projection, ctx, effective_level)
        elif effective_level is None:
            projection.increment_skill(self._marker_instance() if self.specs else self.skill())
        else:
            instance = skill_with_levels(self.skill, allowed[:1], effective_level) if allowed else self.skill()
            projection.grant_skill(instance)

    def _queue_specialization_choice(
        self, projection: CharacterProjection, ctx: SkillTableApplyContext, level: int | None
    ) -> None:
        from ceres.character.domain.career.career_events import PendingSkillTableChoice

        projection.queue_immediate(
            PendingSkillTableChoice(
                pending_id=ctx.next_pending_id(),
                instruction=f'Choose a specialization for {self.skill.name()}',
                options=[self._marker_instance() if self.specs else self.skill()],
                level=level,
            )
        )

    def basic_training_candidates(self, projection: CharacterProjection) -> tuple[AnySkill, ...]:
        if projection.summary.skill_level(self.skill) is None:
            return (self.skill(),)
        return ()

    def label(self) -> str:
        return self.skill.name()


def _validate_talent_class(v: object) -> PsionicTalentSkillClass:
    classes = psionic_talent_classes()
    if isinstance(v, str):
        for cls in classes:
            if cls.model_fields['kind'].default == v:
                return cls
        raise ValueError(f'No psionic talent class with kind {v!r}')
    if isinstance(v, type) and any(v is cls for cls in classes):
        return v  # ty: ignore[invalid-return-type]
    raise ValueError(f'Expected a psionic talent class or kind string, got {v!r}')


PsionicTalentSkillClassRef = Annotated[
    PsionicTalentSkillClass,
    BeforeValidator(_validate_talent_class),
    PlainSerializer(lambda cls: cls.model_fields['kind'].default, return_type=str),
]


class Psi(SkillTableEntryBase):
    kind: Literal['ste_psi'] = 'ste_psi'
    talent: PsionicTalentSkillClassRef
    level: int | None = None
    allow_acquisition: bool = False

    def __init__(
        self,
        talent: PsionicTalentSkillClass,
        level: int | None = None,
        allow_acquisition: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(talent=talent, level=level, allow_acquisition=allow_acquisition, **kwargs)

    def apply(self, projection: CharacterProjection, ctx: SkillTableApplyContext) -> None:
        psionics = projection.summary.psionics
        if psionics is None:
            projection.not_gained(self.talent())
            return
        if psionics.talent_level(self.talent) is not None:
            psionics.increment_talent(self.talent)
            return
        if self.allow_acquisition:
            from ceres.character.domain.psionics import PendingPsionicInstituteTraining

            projection.queue_immediate(
                PendingPsionicInstituteTraining(
                    pending_id=ctx.next_pending_id(),
                    instruction=f'You rolled {self.talent.name()} on the skill table. Attempt to learn this talent?',
                    remaining_talents=[self.talent()],
                )
            )
        else:
            projection.not_gained(self.talent())

    def label(self) -> str:
        return self.talent.name()


class SkillChoice(SkillTableEntryBase):
    kind: Literal['ste_skill_choice'] = 'ste_skill_choice'
    skills: tuple[type[AnySkill], ...]
    level: int | None = None
    specs: tuple[SpecRefField, ...] | None = None

    model_config = {'arbitrary_types_allowed': True}

    def __init__(self, skills: object, level: int | None = None, specs: object = None, **kwargs: object) -> None:
        super().__init__(skills=expand_skill_classes(skills), level=level, specs=specs, **kwargs)

    @model_validator(mode='after')
    def _specs_belong_to_choice(self) -> SkillChoice:
        for ref in self.specs or ():
            if ref.skill_cls not in self.skills:
                raise ValueError(f'Specialization {ref!r} does not belong to any skill in this choice')
        return self

    def _specs_for(self, cls: type[AnySkill]) -> tuple[SpecRef, ...] | None:
        refs = tuple(ref for ref in self.specs or () if ref.skill_cls is cls)
        return refs or None

    def restricted_options(self) -> list[AnySkill]:
        """One instance per skill class, with any spec restriction marked on its Level fields."""
        return [skill_with_levels(cls, [ref.field for ref in self._specs_for(cls) or ()]) for cls in self.skills]

    def apply(self, projection: CharacterProjection, ctx: SkillTableApplyContext) -> None:
        from ceres.character.domain.career.career_events import PendingSkillTableChoice

        options = [Skill(cls, level=self.level, specs=self._specs_for(cls)) for cls in self.skills]
        projection.queue_immediate(
            PendingSkillTableChoice(
                pending_id=ctx.next_pending_id(),
                instruction='Choose a skill',
                options=options,
            )
        )

    def basic_training_candidates(self, projection: CharacterProjection) -> tuple[AnySkill, ...]:
        return tuple(cls() for cls in self.skills if projection.summary.skill_level(cls) is None)

    def label(self) -> str:
        return ' / '.join(cls.name() for cls in self.skills)


class PsiChoice(SkillTableEntryBase):
    kind: Literal['ste_psi_choice'] = 'ste_psi_choice'
    talents: tuple[PsionicTalentSkillClass, ...]
    allow_acquisition: bool = False

    model_config = {'arbitrary_types_allowed': True}

    def __init__(
        self,
        talents: object,
        allow_acquisition: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(talents=expand_talent_classes(talents), allow_acquisition=allow_acquisition, **kwargs)

    def apply(self, projection: CharacterProjection, ctx: SkillTableApplyContext) -> None:
        from ceres.character.domain.career.career_events import PendingSkillTableChoice

        psionics = projection.summary.psionics
        if psionics is None:
            return
        options = []
        for cls in self.talents:
            if not self.allow_acquisition and psionics.talent_level(cls) is None:
                continue
            options.append(Psi(cls, allow_acquisition=self.allow_acquisition))
        if not options:
            return
        projection.queue_immediate(
            PendingSkillTableChoice(
                pending_id=ctx.next_pending_id(),
                instruction='Choose a psionic talent',
                options=options,
            )
        )

    def label(self) -> str:
        return ' / '.join(cls.name() for cls in self.talents)


type SkillTableItem = Annotated[Char | Skill | Psi | SkillChoice | PsiChoice, Field(discriminator='kind')]
