from typing import Any

from pydantic import Field

from .base import RobotBase
from .brain import RobotBrainUnion
from .chassis import (
    RobotSize,
    Trait,
    base_armour,
    base_available_slots,
    base_endurance_multiplier,
    chassis_entry,
    size_trait,
)
from .locomotion import LocomotionUnion
from .parts import RobotPartMixin
from .skills import SkillGrant
from .spec import RobotSpec, RobotSpecRow, RobotSpecSection
from .text import format_credits, format_traits


class Robot(RobotBase):
    name: str
    tl: int
    size: RobotSize
    locomotion: LocomotionUnion
    brain: RobotBrainUnion
    options: list[Any] = Field(default_factory=list)
    manipulators: list[str] = Field(default_factory=list)
    attacks: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        if self.locomotion.required_tl > self.tl:
            self.error(f'Locomotion requires TL{self.locomotion.required_tl}, robot is TL{self.tl}')
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                opt.bind(self)

    def parts_of_type(self, part_cls: type) -> list:
        return [o for o in self.options if isinstance(o, part_cls)]

    @property
    def base_slots(self) -> int:
        return chassis_entry(self.size).base_slots

    @property
    def available_slots(self) -> int:
        return base_available_slots(self.size, none_locomotion=self.locomotion.is_none_locomotion)

    @property
    def used_slots(self) -> int:
        return sum(o.slots for o in self.options if isinstance(o, RobotPartMixin) and o.slots > 0)

    @property
    def remaining_slots(self) -> int:
        return self.available_slots - self.used_slots

    @property
    def base_hits(self) -> int:
        return chassis_entry(self.size).base_hits

    @property
    def hits(self) -> int:
        return self.base_hits

    @property
    def base_chassis_cost(self) -> float:
        return chassis_entry(self.size).basic_cost * self.locomotion.cost_multiplier

    @property
    def base_armour(self) -> int:
        return base_armour(self.tl)

    @property
    def base_endurance(self) -> float:
        return self.locomotion.base_endurance * base_endurance_multiplier(self.tl)

    @property
    def traits(self) -> list[Trait]:
        result: list[Trait] = []
        armour_val = self.base_armour
        if armour_val:
            result.append(Trait('Armour', f'+{armour_val}'))
        size_t = size_trait(self.size)
        if size_t:
            result.append(size_t)
        result.extend(self.locomotion.locomotion_traits)
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                result.extend(opt.robot_traits)
        return result

    @property
    def skills_display(self) -> str:
        skills: list[SkillGrant] = list(self.brain.skill_grants)
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                skills.extend(opt.skill_grants)
        parts = [str(s) for s in skills]
        rem = self.brain.remaining_bandwidth
        if rem is not None and rem > 0:
            parts.append(f'+{rem} Bandwidth available')
        return ', '.join(parts) if parts else '—'

    def build_notes(self) -> list:
        from ceres.shared import _Note

        notes = []
        if self.used_slots > self.available_slots:
            notes.append(_Note.error(f'Slot overload: {self.used_slots} used, {self.available_slots} available'))
        return notes

    def build_spec(self) -> RobotSpec:
        spec = RobotSpec(name=self.name, tl=self.tl, robot_notes=self.notes)
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.ROBOT,
                label='Robot',
                value=(
                    f'Hits {self.hits}, Locomotion {self.locomotion.label()}, '
                    f'Speed {self.locomotion.speed_label()}, '
                    f'TL {self.tl}, Cost {format_credits(self.base_chassis_cost)}'
                ),
            )
        )
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.SKILLS,
                label='Skills',
                value=self.skills_display,
            )
        )
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.TRAITS,
                label='Traits',
                value=format_traits(self.traits),
            )
        )
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.PROGRAMMING,
                label='Programming',
                value=self.brain.programming_label(),
            )
        )
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.ENDURANCE,
                label='Endurance',
                value=f'{int(self.base_endurance)} hours',
            )
        )
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.ATTACKS,
                label='Attacks',
                value=', '.join(self.attacks) if self.attacks else '—',
            )
        )
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.MANIPULATORS,
                label='Manipulators',
                value=', '.join(self.manipulators) if self.manipulators else '—',
            )
        )
        return spec


__all__ = ['Robot']
