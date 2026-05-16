from math import ceil
from typing import Any

from pydantic import Field

from .base import RobotBase
from .brain import AdvancedBrain, RobotBrainUnion, VeryAdvancedBrain
from .chassis import (
    RobotSize,
    Trait,
    base_armour,
    base_available_slots,
    base_endurance_multiplier,
    chassis_entry,
    size_label,
    size_trait,
)
from .locomotion import LocomotionUnion
from .options import default_suite_item_cost
from .parts import RobotPartMixin
from .skills import SkillGrant
from .spec import RobotSpec, RobotSpecRow, RobotSpecSection
from .text import format_credits, format_traits

_DEFAULT_MANIPULATORS: tuple[str, ...] = ('Standard', 'Standard')

_DEFAULT_SUITE: tuple[str, ...] = (
    'Auditory Sensor',
    'Transceiver 5km (improved)',
    'Visual Spectrum Sensor',
    'Voder Speaker',
    'Wireless Data Link',
)


class Robot(RobotBase):
    name: str
    tl: int
    size: RobotSize
    locomotion: LocomotionUnion
    brain: RobotBrainUnion
    options: list[Any] = Field(default_factory=list)
    default_suite: list[str] = Field(default_factory=lambda: list(_DEFAULT_SUITE))
    manipulators: list[str] = Field(default_factory=lambda: list(_DEFAULT_MANIPULATORS))
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
        base = base_available_slots(self.size, none_locomotion=self.locomotion.is_none_locomotion)
        removed = max(0, 2 - len(self.manipulators))
        if removed:
            base_slots = chassis_entry(self.size).base_slots
            base += max(1, ceil(0.1 * base_slots)) * removed
        return base

    @property
    def used_slots(self) -> int:
        brain_slot = self.brain.brain_slots(self.tl, int(self.size))
        option_slots = sum(o.slots for o in self.options if isinstance(o, RobotPartMixin) and o.slots > 0)
        # Chassis modifications (item_message is None) are excluded from the zero-slot quota.
        # Beyond Default(5) + Size + TL free zero-slot options each cost 1 slot.
        zero_slot_count = sum(
            1
            for o in self.options
            if isinstance(o, RobotPartMixin) and o.slots == 0 and o.notes.item_message is not None
        )
        excess_zero_slots = max(0, zero_slot_count - (int(self.size) + self.tl))
        return brain_slot + option_slots + excess_zero_slots

    @property
    def remaining_slots(self) -> int:
        return self.available_slots - self.used_slots

    @property
    def base_hits(self) -> int:
        return chassis_entry(self.size).base_hits

    @property
    def hits(self) -> int:
        return self.base_hits + sum(opt.hits_delta for opt in self.options if isinstance(opt, RobotPartMixin))

    @property
    def base_chassis_cost(self) -> float:
        return chassis_entry(self.size).basic_cost * self.locomotion.cost_multiplier

    @property
    def _raw_cost(self) -> float:
        cost = self.base_chassis_cost
        cost += self.base_chassis_cost * self.locomotion.speed_cost_fraction
        cost += self.brain.brain_cost
        cost += sum(opt.cost for opt in self.options if isinstance(opt, RobotPartMixin))
        removed = max(0, 2 - len(self.manipulators))
        cost -= 100.0 * int(self.size) * removed
        cost += sum(default_suite_item_cost(item) for item in self.default_suite)
        return cost

    @property
    def total_cost(self) -> float:
        return max(self._raw_cost, chassis_entry(self.size).basic_cost)

    @property
    def base_armour(self) -> int:
        return base_armour(self.tl)

    @property
    def base_endurance(self) -> float:
        return self.locomotion.base_endurance * base_endurance_multiplier(self.tl)

    @property
    def traits(self) -> list[Trait]:
        from .options import VehicleSpeedModification

        result: list[Trait] = []
        armour_val = self.base_armour
        if armour_val:
            result.append(Trait('Armour', f'+{armour_val}'))
        size_t = size_trait(self.size)
        if size_t:
            result.append(size_t)
        has_vsm = any(isinstance(o, VehicleSpeedModification) for o in self.options)
        for t in self.locomotion.locomotion_traits:
            if has_vsm and t.name == 'Flyer':
                continue  # replaced by VehicleSpeedModification's vehicle-speed-band trait
            result.append(t)
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                result.extend(opt.robot_traits)
        # Deduplicate preserving first-seen order, then sort case-insensitively
        seen: set[tuple] = set()
        unique: list[Trait] = []
        for t in result:
            key = (t.name, t.value)
            if key not in seen:
                seen.add(key)
                unique.append(t)
        return sorted(unique, key=lambda t: str(t).lower())

    @property
    def speed_label(self) -> str:
        from .options import VehicleSpeedModification

        if any(isinstance(o, VehicleSpeedModification) for o in self.options):
            return '—'
        return self.locomotion.speed_label()

    @property
    def endurance_label(self) -> str:
        from .options import VehicleSpeedModification

        base = int(self.base_endurance)
        for opt in self.options:
            if isinstance(opt, VehicleSpeedModification):
                vehicle_end = int(self.base_endurance / 4)
                return f'{base} ({vehicle_end}) hours'
        return f'{base} hours'

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
        rem_slots = self.remaining_slots
        if rem_slots < 0:
            notes.append(_Note.error(f'Slot overload: {self.used_slots} used, {self.available_slots} available'))
        rem_bw = self.brain.remaining_bandwidth
        if rem_bw is not None and rem_bw < 0:
            notes.append(_Note.error(f'Bandwidth overload: {-rem_bw} over capacity'))
        basic = chassis_entry(self.size).basic_cost
        if self._raw_cost < basic:
            notes.append(_Note.info(f'Cost raised to Basic Cost minimum ({format_credits(basic)})'))
        return notes

    def _build_detail_sections(self) -> list:
        from .options import AdditionalManipulator, VehicleSpeedModification
        from .spec import RobotDetailRow, RobotDetailSection

        sections = []
        entry = chassis_entry(self.size)
        base_slots = entry.base_slots

        # ── Chassis ───────────────────────────────────────────────────────
        cs = RobotDetailSection(title='Chassis')
        cs.rows.append(
            RobotDetailRow(
                name=f'Size {size_label(self.size)}',
                col2=f'+{base_slots}',
                cost=format_credits(entry.basic_cost),
            )
        )
        if self.locomotion.is_none_locomotion:
            none_bonus = ceil(base_slots * 1.25) - base_slots
            cs.rows.append(
                RobotDetailRow(
                    name='No Locomotion',
                    col2=f'+{none_bonus}' if none_bonus else '—',
                )
            )
        else:
            loco_extra = entry.basic_cost * (self.locomotion.cost_multiplier - 1)
            cs.rows.append(
                RobotDetailRow(
                    name=f'{self.locomotion.label()} chassis',
                    cost=format_credits(loco_extra) if loco_extra > 0 else '—',
                )
            )
        speed_cost = self.base_chassis_cost * self.locomotion.speed_cost_fraction
        if speed_cost > 0:
            cs.rows.append(RobotDetailRow(name='Speed modification', cost=format_credits(speed_cost)))
        for opt in self.options:
            if isinstance(opt, VehicleSpeedModification):
                cs.rows.append(
                    RobotDetailRow(
                        name='Vehicle Speed Modification',
                        col2=f'−{opt.slots}',
                        cost=format_credits(opt.cost),
                    )
                )
        removed = max(0, 2 - len(self.manipulators))
        if removed:
            manip_slot_bonus = max(1, ceil(0.1 * base_slots)) * removed
            discount = 100.0 * int(self.size) * removed
            cs.rows.append(
                RobotDetailRow(
                    name=f'Removed manipulator ×{removed}',
                    col2=f'+{manip_slot_bonus}',
                    cost=f'−{format_credits(discount)}',
                )
            )
        sections.append(cs)

        # ── Brain ─────────────────────────────────────────────────────────
        bs = RobotDetailSection(title='Brain')
        total_brain_slots = self.brain.brain_slots(self.tl, int(self.size))
        brain_label = self.brain.programming_label()
        if isinstance(self.brain, (AdvancedBrain, VeryAdvancedBrain)):
            if self.brain._bw_upgrade_delta > 0:
                brain_label = brain_label[:-1] + f', Bandwidth {self.brain.bandwidth})'
            brain_base_cost = self.brain._entry().cost + self.brain._bw_upgrade_cost
            bs.rows.append(
                RobotDetailRow(
                    name=brain_label,
                    col2=f'−{total_brain_slots}' if total_brain_slots else '—',
                    col3=f'+{self.brain.bandwidth}',
                    cost=format_credits(brain_base_cost),
                )
            )
            if self.brain.int_upgrade > 0:
                bs.rows.append(
                    RobotDetailRow(
                        name=f'INT +{self.brain.int_upgrade}',
                        col3=f'−{self.brain._int_upgrade_bw}',
                        cost=format_credits(self.brain._int_upgrade_cost),
                    )
                )
        else:
            bs.rows.append(
                RobotDetailRow(
                    name=brain_label,
                    col2=f'−{total_brain_slots}' if total_brain_slots else '—',
                    cost=format_credits(self.brain.hardware_cost),
                )
            )
        sections.append(bs)

        # ── Installed Skills ──────────────────────────────────────────────
        if isinstance(self.brain, (AdvancedBrain, VeryAdvancedBrain)) and self.brain.installed_skills:
            ss = RobotDetailSection(title='Skills')
            for pkg in self.brain.installed_skills:
                ss.rows.append(
                    RobotDetailRow(
                        name=f'{pkg.name} {pkg.level}',
                        col3=f'−{pkg.bandwidth}',
                        cost=format_credits(pkg.cost),
                    )
                )
            sections.append(ss)

        # ── Manipulators ──────────────────────────────────────────────────
        additional_manips = [o for o in self.options if isinstance(o, AdditionalManipulator)]
        if self.manipulators or additional_manips:
            ms = RobotDetailSection(title='Manipulators')
            for m in self.manipulators:
                ms.rows.append(RobotDetailRow(name=m))
            for am in additional_manips:
                ms.rows.append(
                    RobotDetailRow(
                        name=am.description,
                        col2=f'−{am.slots}',
                        cost=format_credits(am.cost),
                    )
                )
            sections.append(ms)

        # ── Options ───────────────────────────────────────────────────────
        opts = [o for o in self.options if isinstance(o, RobotPartMixin) and o.notes.item_message]
        if opts:
            os_ = RobotDetailSection(title='Options')
            for o in opts:
                os_.rows.append(
                    RobotDetailRow(
                        name=o.notes.item_message,
                        col2=f'−{o.slots}' if o.slots > 0 else '—',
                        cost=format_credits(o.cost) if o.cost > 0 else '—',
                    )
                )
            sections.append(os_)

        # ── Default Suite ─────────────────────────────────────────────────
        if self.default_suite:
            ds = RobotDetailSection(title='Default Suite')
            for item in sorted(self.default_suite):
                item_cost = default_suite_item_cost(item)
                ds.rows.append(
                    RobotDetailRow(
                        name=item,
                        cost=format_credits(item_cost) if item_cost > 0 else '—',
                    )
                )
            sections.append(ds)

        # ── Finalisation ──────────────────────────────────────────────────
        fin = RobotDetailSection(title='Finalisation')
        rem_bw = self.brain.remaining_bandwidth
        fin.rows.append(
            RobotDetailRow(
                name='Remaining',
                col2=str(self.remaining_slots),
                col3=str(rem_bw) if rem_bw is not None else '—',
            )
        )
        if self._raw_cost < entry.basic_cost:
            fin.rows.append(
                RobotDetailRow(
                    name='Cost raised to Basic Cost',
                    cost=format_credits(entry.basic_cost),
                )
            )
        fin.rows.append(RobotDetailRow(name='Total', cost=format_credits(self.total_cost)))
        sections.append(fin)

        return sections

    def build_spec(self) -> RobotSpec:
        spec = RobotSpec(name=self.name, tl=self.tl, robot_notes=self.notes)
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.ROBOT,
                label='Robot',
                columns=[
                    ('Robot', self.name),
                    ('Size', str(int(self.size))),
                    ('Hits', str(self.hits)),
                    ('Locomotion', self.locomotion.label()),
                    ('Speed', self.speed_label),
                    ('TL', str(self.tl)),
                    ('Cost', format_credits(self.total_cost)),
                ],
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
                value=self.endurance_label,
            )
        )
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.ATTACKS,
                label='Attacks',
                value=', '.join(self.attacks) if self.attacks else '—',
            )
        )
        from .options import AdditionalManipulator

        manip_parts = list(self.manipulators)
        for opt in self.options:
            if isinstance(opt, AdditionalManipulator):
                manip_parts.append(opt.description)
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.MANIPULATORS,
                label='Manipulators',
                value=', '.join(manip_parts) if manip_parts else '—',
            )
        )
        option_labels = list(self.default_suite)
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                label = opt.notes.item_message
                if label:
                    option_labels.append(label)
        spare = self.remaining_slots
        if spare > 0:
            option_labels.append(f'Spare Slots x{spare}')
        option_labels.sort()
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.OPTIONS,
                label='Options',
                value=', '.join(option_labels) if option_labels else '—',
            )
        )
        spec.detail_sections = self._build_detail_sections()
        return spec


__all__ = ['Robot']
