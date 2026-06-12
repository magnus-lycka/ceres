from math import ceil
from typing import Any

from pydantic import Field

from ceres.character.domain.characteristics import Chars, characteristic_dm
from ceres.shared import _Note

from .base import RobotBase
from .brain import AdvancedBrain, BasicBrain, PrimitiveBrain, RobotBrainUnion, SelfAwareBrain, VeryAdvancedBrain
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
from .locomotion import LocomotionUnion, ThrusterLocomotion, WalkerLocomotion
from .manipulators import LegOrManipulator, Manipulator
from .options import AgilityEnhancement, Efficiency, VehicleSpeedModification, default_suite
from .parts import RobotPartMixin
from .skills import skill_name
from .spec import RobotDetailRow, RobotDetailSection, RobotSpec, RobotSpecRow, RobotSpecSection
from .text import format_credits, format_traits


def _robot_dex(tl: int) -> int:
    return ceil(tl / 2) + 1


def _robot_str(size: int) -> int:
    return 2 * size - 1


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
        return sum(m.slots for m in self.manipulators) - 2 * std_slots

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
        # Chassis mods (item_message is None, or Efficiency/AgilityEnhancement) excluded from quota.
        # The 5 default suite items in options are covered by the +5 term in the quota.
        zero_slot_count = sum(
            1
            for o in self.options
            if isinstance(o, RobotPartMixin)
            and o.slots == 0
            and o.notes.item_message is not None
            and not isinstance(o, (AgilityEnhancement, Efficiency))
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
        result: list[Trait] = []
        armour_val = self.base_armour + sum(opt.armour_delta for opt in self.options if isinstance(opt, RobotPartMixin))
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
        result.extend(self.brain.brain_traits)
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
    def locomotion_label(self) -> str:
        label = self.locomotion.label()
        if any(isinstance(o, VehicleSpeedModification) for o in self.options):
            return f'{label} (VSM)'
        return label

    @property
    def speed_label(self) -> str:
        if any(isinstance(o, VehicleSpeedModification) for o in self.options):
            if isinstance(self.locomotion, ThrusterLocomotion):
                return f'{self.locomotion.thrust_g:g}G'
            speed_bonus = sum(opt.speed_bonus for opt in self.options if isinstance(opt, RobotPartMixin))
            tactical = self.locomotion.effective_speed + (self.locomotion.agility or 0) + speed_bonus
            for t in self.traits:
                if t.name == 'Flyer':
                    return f'{tactical}m ({t.value})'
            band = self.locomotion._vehicle_speed_band
            if band:
                return f'{tactical}m ({band})'
            return f'{tactical}m'
        speed_bonus = sum(opt.speed_bonus for opt in self.options if isinstance(opt, RobotPartMixin))
        return f'{self.locomotion.effective_speed + (self.locomotion.agility or 0) + speed_bonus}m'

    @property
    def endurance_label(self) -> str:
        base = int(self.base_endurance)
        for opt in self.options:
            if isinstance(opt, VehicleSpeedModification):
                vehicle_end = int(self.base_endurance / 4)
                return f'{base} ({vehicle_end}) hours'
        return f'{base} hours'

    @property
    def skills_display(self) -> str:
        base_str = _robot_str(int(self.size))
        str_for_dm = max(
            base_str,
            max((m.effective_str(self.size) for m in self.manipulators), default=base_str),
        )
        dms = {Chars.DEX: characteristic_dm(_robot_dex(self.tl)), Chars.STR: characteristic_dm(str_for_dm)}
        merged = self.brain.display_labels(dms)
        for opt in self.options:
            if isinstance(opt, RobotPartMixin):
                for name, lvl in opt.skill_grants.items():
                    merged[name] = max(merged.get(name, 0), lvl)
        # Basic/Primitive (locomotion) grants Vehicle (type) X where X = agility (locomotion base + enhancement).
        # refs/robot/35_skill_packages.md — Basic (locomotion) skill table.
        if isinstance(self.brain, (BasicBrain, PrimitiveBrain)) and self.brain.function == 'locomotion':
            agility_enh = sum(opt.level for opt in self.options if isinstance(opt, AgilityEnhancement))
            effective_agility = (self.locomotion.agility or 0) + agility_enh
            vehicle_skill = self.locomotion.vehicle_skill
            if vehicle_skill is not None:
                vehicle_name = skill_name(vehicle_skill)
                merged[vehicle_name] = max(merged.get(vehicle_name, 0), effective_agility)
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

    def _build_detail_sections(self) -> list:  # noqa: PLR0912, PLR0915
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
        for opt in self.options:
            if isinstance(opt, AgilityEnhancement):
                cs.rows.append(
                    RobotDetailRow(
                        name=f'Agility Enhancement ({opt.level})',
                        cost=format_credits(opt.cost),
                    )
                )
        for opt in self.options:
            if isinstance(opt, Efficiency):
                cs.rows.append(
                    RobotDetailRow(
                        name='Efficiency',
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
                entries = pkg.display_entries({})
                pkg_name = ', '.join(f'{k} {v}' for k, v in entries.items()) or type(pkg).skill_name()
                ss.rows.append(
                    RobotDetailRow(
                        name=pkg_name,
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
        remaining_credit = -min(0.0, self._manipulator_cost_effect)
        # Build (name, slots_freed, cost_effect) rows; group consecutive identical ones.
        manip_rows: list[tuple[str, int, float]] = []
        for i in range(2):
            if i < len(self.manipulators):
                m = self.manipulators[i]
                label = m.stat_label(self.size, self.tl)
                manip_rows.append((label, std_slots - m.slots, m.cost - std_cost))
            else:
                allocated = min(std_cost, remaining_credit)
                remaining_credit -= allocated
                manip_rows.append(('Removed manipulator', std_slots, -allocated))
        manip_rows.extend((m.stat_label(self.size, self.tl), -m.slots, m.cost) for m in self.manipulators[2:])
        for m in self._leg_manipulators:
            label = f'Manipulator leg {m.stat_label(self.size, self.tl)}'
            manip_rows.append((label, 0, m.cost))
        j = 0
        while j < len(manip_rows):
            name, slots_freed, cost_effect = manip_rows[j]
            count = 1
            while j + count < len(manip_rows) and manip_rows[j + count] == manip_rows[j]:
                count += 1
            grouped_name = f'{name} × {count}' if count > 1 else name
            total_slots = slots_freed * count
            total_cost = cost_effect * count
            slot_str = f'+{total_slots}' if total_slots > 0 else (f'−{-total_slots}' if total_slots < 0 else '—')
            cost_str = (
                format_credits(total_cost)
                if total_cost > 0
                else (f'−{format_credits(-total_cost)}' if total_cost < 0 else '—')
            )
            ms.rows.append(RobotDetailRow(name=grouped_name, col2=slot_str, cost=cost_str))
            j += count
        sections.append(ms)

        # ── Options ───────────────────────────────────────────────────────
        opts = [
            o
            for o in self.options
            if isinstance(o, RobotPartMixin)
            and o.notes.item_message
            and not isinstance(o, (AgilityEnhancement, Efficiency))
        ]
        if opts:
            os_ = RobotDetailSection(title='Options')
            # Group consecutive identical option labels; sum slots and cost within each run.
            i = 0
            while i < len(opts):
                label = opts[i].notes.item_message
                slots = opts[i].slots
                cost = opts[i].cost
                count = 1
                while i + count < len(opts) and opts[i + count].notes.item_message == label:
                    slots += opts[i + count].slots
                    cost += opts[i + count].cost
                    count += 1
                name = f'{label} × {count}' if count > 1 else label
                os_.rows.append(
                    RobotDetailRow(
                        name=name,
                        col2=f'−{slots}' if slots > 0 else '—',
                        cost=format_credits(cost) if cost > 0 else '—',
                    )
                )
                i += count
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
        # Zero-slot option quota (chassis mods AgilityEnhancement/Efficiency excluded)
        zero_slot_count = sum(
            1
            for o in self.options
            if isinstance(o, RobotPartMixin)
            and o.slots == 0
            and o.notes.item_message is not None
            and not isinstance(o, (AgilityEnhancement, Efficiency))
        )
        zero_slot_quota = 5 + int(self.size) + self.tl
        zero_bw_str = '—'
        if isinstance(self.brain, (AdvancedBrain, VeryAdvancedBrain, SelfAwareBrain)):
            zero_bw_pkgs = sum(1 for pkg in self.brain.installed_skills if pkg.bandwidth == 0)
            brain_computer_x = self.brain._entry().computer_x
            zero_bw_str = f'{zero_bw_pkgs}/{brain_computer_x}'
        fin.rows.append(
            RobotDetailRow(
                name='Zero-slot options and Zero-BW skill packages',
                col2=f'{zero_slot_count}/{zero_slot_quota}',
                col3=zero_bw_str,
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
                    ('Locomotion', self.locomotion_label),
                    ('Speed', self.speed_label),
                    ('TL', str(self.tl)),
                    ('Cost', format_credits(self.total_cost)),
                ],
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
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.PROGRAMMING,
                label='Programming',
                value=self.brain.programming_label(),
            )
        )
        spec.add_row(
            RobotSpecRow(
                section=RobotSpecSection.SKILLS,
                label='Skills',
                value=self.skills_display,
            )
        )
        spec.detail_sections = self._build_detail_sections()
        return spec
