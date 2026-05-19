from math import ceil
from typing import Any

from pydantic import Field

from .base import RobotBase
from .brain import AdvancedBrain, RobotBrainUnion, SelfAwareBrain, VeryAdvancedBrain
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
from .locomotion import LocomotionUnion, WalkerLocomotion
from .manipulators import LegOrManipulator, Manipulator
from .options import default_suite
from .parts import RobotPartMixin
from .skills import SkillGrant
from .spec import RobotSpec, RobotSpecRow, RobotSpecSection
from .text import format_credits, format_traits


def _characteristic_dm(char: int) -> int:
    if char <= 1:
        return -2
    if char <= 5:
        return -1
    if char <= 8:
        return 0
    if char <= 11:
        return 1
    if char <= 14:
        return 2
    return 3


def _robot_dex(tl: int) -> int:
    return ceil(tl / 2) + 1


def _collapse(labels: list[str]) -> list[str]:
    parts: list[str] = []
    i = 0
    while i < len(labels):
        count = 1
        while i + count < len(labels) and labels[i + count] == labels[i]:
            count += 1
        parts.append(f'{labels[i]} × {count}' if count > 1 else labels[i])
        i += count
    return parts


class Robot(RobotBase):
    name: str
    tl: int
    size: RobotSize
    locomotion: LocomotionUnion
    brain: RobotBrainUnion
    options: list[Any] = Field(default_factory=default_suite)
    manipulators: list[Manipulator] = Field(default_factory=lambda: [Manipulator(), Manipulator()])
    legs: list[LegOrManipulator] = Field(default_factory=list)
    attacks: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        if self.locomotion.required_tl > self.tl:
            self.error(f'Locomotion requires TL{self.locomotion.required_tl}, robot is TL{self.tl}')
        for m in self.manipulators:
            m.bind(self)
        for m in self._leg_manipulators:
            m.bind(self)
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                opt.bind(self)

    def parts_of_type(self, part_cls: type) -> list:
        return [o for o in self.options if isinstance(o, part_cls)]

    @property
    def base_slots(self) -> int:
        return chassis_entry(self.size).base_slots

    @property
    def _leg_manipulators(self) -> list[Manipulator]:
        if isinstance(self.locomotion, WalkerLocomotion):
            return [m for m in self.legs if isinstance(m, Manipulator)]
        return []

    @property
    def _std_manip_slots(self) -> int:
        base_slots = chassis_entry(self.size).base_slots
        return max(1, ceil(0.10 * base_slots))

    @property
    def _manipulator_slot_effect(self) -> int:
        std_slots = self._std_manip_slots
        arm_effect = sum(m.slots for m in self.manipulators) - 2 * std_slots
        return arm_effect

    @property
    def _manipulator_cost_effect(self) -> float:
        std_cost = 100.0 * int(self.size)
        arm_net = sum(m.cost for m in self.manipulators) - 2 * std_cost
        leg_cost = sum(m.cost for m in self._leg_manipulators)
        net = arm_net + leg_cost
        return max(net, -0.20 * self.base_chassis_cost)

    @property
    def available_slots(self) -> int:
        base = base_available_slots(self.size, none_locomotion=self.locomotion.is_none_locomotion)
        effect = self._manipulator_slot_effect
        if effect < 0:
            base += -effect
        return base

    @property
    def used_slots(self) -> int:
        brain_slot = self.brain.brain_slots(self.tl, int(self.size))
        option_slots = sum(o.slots for o in self.options if isinstance(o, RobotPartMixin) and o.slots > 0)
        # Chassis modifications (item_message is None) are excluded from the zero-slot quota.
        # The 5 default suite items in options are covered by the +5 term in the quota.
        zero_slot_count = sum(
            1
            for o in self.options
            if isinstance(o, RobotPartMixin) and o.slots == 0 and o.notes.item_message is not None
        )
        excess_zero_slots = max(0, zero_slot_count - (5 + int(self.size) + self.tl))
        extra_manip_slots = max(0, self._manipulator_slot_effect)
        return brain_slot + option_slots + excess_zero_slots + extra_manip_slots

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
        cost += self._manipulator_cost_effect
        return cost

    @property
    def total_cost(self) -> float:
        return max(self._raw_cost, chassis_entry(self.size).basic_cost)

    @property
    def base_armour(self) -> int:
        return base_armour(self.tl)

    @property
    def base_endurance(self) -> float:
        base = self.locomotion.base_endurance * base_endurance_multiplier(self.tl)
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                base *= opt.endurance_multiplier
        return base

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
        for t in self.brain.brain_traits:
            result.append(t)
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
            for t in self.traits:
                if t.name == 'Flyer':
                    return str(t.value)
            return 'Vehicle speed'
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
        dex_dm = _characteristic_dm(_robot_dex(self.tl))
        grants: list[SkillGrant] = list(self.brain.skill_grants_for_robot(dex_dm))
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                grants.extend(opt.skill_grants)
        merged: dict[str, int] = {}
        for g in grants:
            if g.name not in merged or g.level > merged[g.name]:
                merged[g.name] = g.level
        parts = sorted(f'{name} {level}' for name, level in merged.items())
        rem = self.brain.remaining_bandwidth
        if rem is not None and rem > 0:
            parts.append(f'+{rem} Bandwidth available')
        return ', '.join(parts) if parts else '—'

    @property
    def _manipulators_display(self) -> str:
        arm_labels = [m.stat_label(self.size, self.tl) for m in self.manipulators]
        leg_labels = [f'Manipulator leg {m.stat_label(self.size, self.tl)}' for m in self._leg_manipulators]
        parts = _collapse(arm_labels) + _collapse(leg_labels)
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
        from .options import VehicleSpeedModification
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
            cs.rows.append(
                RobotDetailRow(
                    name=f'Speed modification (+{self.locomotion.speed_increase})',
                    cost=format_credits(speed_cost),
                )
            )
        for opt in self.options:
            if isinstance(opt, VehicleSpeedModification):
                cs.rows.append(
                    RobotDetailRow(
                        name='Vehicle Speed Modification',
                        col2=f'−{opt.slots}',
                        cost=format_credits(opt.cost),
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
        has_software = isinstance(self.brain, SelfAwareBrain) and bool(self.brain.installed_software)
        has_skills = isinstance(self.brain, (AdvancedBrain, VeryAdvancedBrain, SelfAwareBrain))
        if has_skills and (self.brain.installed_skills or has_software):
            ss = RobotDetailSection(title='Skills')
            for pkg in self.brain.installed_skills:
                ss.rows.append(
                    RobotDetailRow(
                        name=f'{pkg.name} {pkg.level}',
                        col3=f'−{pkg.bandwidth}',
                        cost=format_credits(pkg.cost),
                    )
                )
            if isinstance(self.brain, SelfAwareBrain):
                for sw in self.brain.installed_software:
                    ss.rows.append(
                        RobotDetailRow(
                            name=sw.name,
                            col3=f'−{sw.bandwidth}',
                            cost=format_credits(sw.cost),
                        )
                    )
            sections.append(ss)

        # ── Manipulators ──────────────────────────────────────────────────
        ms = RobotDetailSection(title='Manipulators')
        std_slots = self._std_manip_slots
        std_cost = 100.0 * int(self.size)
        # Credit available for removed/downsized rows (already reflects 20% cap)
        remaining_credit = -min(0.0, self._manipulator_cost_effect)
        for i in range(2):
            if i < len(self.manipulators):
                m = self.manipulators[i]
                label = m.stat_label(self.size, self.tl)
                slot_delta = m.slots - std_slots
                cost_delta = m.cost - std_cost
                slot_str = f'−{slot_delta}' if slot_delta > 0 else (f'+{-slot_delta}' if slot_delta < 0 else '—')
                cost_str = (
                    format_credits(cost_delta)
                    if cost_delta > 0
                    else (f'−{format_credits(-cost_delta)}' if cost_delta < 0 else '—')
                )
                ms.rows.append(RobotDetailRow(name=label, col2=slot_str, cost=cost_str))
            else:
                allocated = min(std_cost, remaining_credit)
                remaining_credit -= allocated
                cost_str = f'−{format_credits(allocated)}' if allocated > 0 else '—'
                ms.rows.append(RobotDetailRow(name='Removed manipulator', col2=f'+{std_slots}', cost=cost_str))
        for m in self.manipulators[2:]:
            label = m.stat_label(self.size, self.tl)
            ms.rows.append(
                RobotDetailRow(
                    name=label,
                    col2=f'−{m.slots}',
                    cost=format_credits(m.cost),
                )
            )
        for m in self._leg_manipulators:
            label = f'Manipulator leg {m.stat_label(self.size, self.tl)}'
            ms.rows.append(
                RobotDetailRow(
                    name=label,
                    col2='—',
                    cost=format_credits(m.cost),
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
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.MANIPULATORS,
                label='Manipulators',
                value=self._manipulators_display,
            )
        )
        option_labels = []
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                label = opt.notes.item_message
                if label:
                    option_labels.append(label)
        spare = self.remaining_slots
        if spare > 0:
            option_labels.append(f'Spare Slots ×{spare}')
        option_labels.sort()
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.OPTIONS,
                label='Options',
                value=', '.join(_collapse(option_labels)) if option_labels else '—',
            )
        )
        spec.detail_sections = self._build_detail_sections()
        return spec


__all__ = ['Robot']
