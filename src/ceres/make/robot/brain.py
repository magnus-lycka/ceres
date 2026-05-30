"""Robot brain types.

Brain table values from refs/robot/33_brain.md.
"""

from dataclasses import dataclass
from typing import Annotated, Any, ClassVar, Literal, cast

from pydantic import ConfigDict, Field, model_validator

from ceres.shared import CeresModel

from .skills import (
    BrainSoftware,
    SkillGrant,
    SkillPackage,
    primitive_package_skills,
)


@dataclass(frozen=True)
class _BrainEntry:
    tl: int
    bandwidth: int
    computer_x: int
    cost: float
    base_int: int
    skill_dm: int


_PRIMITIVE_TABLE: tuple[_BrainEntry, ...] = (
    _BrainEntry(tl=7, bandwidth=0, computer_x=0, cost=10000.0, base_int=1, skill_dm=-2),
    _BrainEntry(tl=8, bandwidth=0, computer_x=0, cost=100.0, base_int=1, skill_dm=-2),
)

_BASIC_TABLE: tuple[_BrainEntry, ...] = (
    _BrainEntry(tl=8, bandwidth=1, computer_x=1, cost=20000.0, base_int=3, skill_dm=-1),
    _BrainEntry(tl=10, bandwidth=1, computer_x=1, cost=4000.0, base_int=4, skill_dm=-1),
)

_ADVANCED_TABLE: tuple[_BrainEntry, ...] = (
    _BrainEntry(tl=10, bandwidth=2, computer_x=2, cost=100000.0, base_int=6, skill_dm=0),
    _BrainEntry(tl=11, bandwidth=2, computer_x=2, cost=50000.0, base_int=7, skill_dm=0),
    _BrainEntry(tl=12, bandwidth=2, computer_x=2, cost=10000.0, base_int=8, skill_dm=0),
)

_VERY_ADVANCED_TABLE: tuple[_BrainEntry, ...] = (
    _BrainEntry(tl=12, bandwidth=3, computer_x=3, cost=500000.0, base_int=9, skill_dm=1),
    _BrainEntry(tl=13, bandwidth=4, computer_x=4, cost=500000.0, base_int=10, skill_dm=1),
    _BrainEntry(tl=14, bandwidth=5, computer_x=5, cost=500000.0, base_int=11, skill_dm=1),
)

_SELF_AWARE_TABLE: tuple[_BrainEntry, ...] = (
    _BrainEntry(tl=15, bandwidth=10, computer_x=10, cost=1_000_000.0, base_int=12, skill_dm=2),
    _BrainEntry(tl=16, bandwidth=15, computer_x=15, cost=1_000_000.0, base_int=13, skill_dm=2),
)


@dataclass(frozen=True)
class _BwUpgradeEntry:
    min_tl: int
    delta_bw: int
    cost: float


_ADVANCED_BW_UPGRADES: tuple[_BwUpgradeEntry, ...] = (
    _BwUpgradeEntry(min_tl=10, delta_bw=2, cost=5_000.0),
    _BwUpgradeEntry(min_tl=11, delta_bw=3, cost=10_000.0),
    _BwUpgradeEntry(min_tl=12, delta_bw=4, cost=20_000.0),
)

_VERY_ADVANCED_BW_UPGRADES: tuple[_BwUpgradeEntry, ...] = (
    _BwUpgradeEntry(min_tl=12, delta_bw=6, cost=50_000.0),
    _BwUpgradeEntry(min_tl=12, delta_bw=8, cost=100_000.0),
)

_SELF_AWARE_BW_UPGRADES: tuple[_BwUpgradeEntry, ...] = (
    _BwUpgradeEntry(min_tl=15, delta_bw=8, cost=100_000.0),
    _BwUpgradeEntry(min_tl=15, delta_bw=10, cost=500_000.0),
    _BwUpgradeEntry(min_tl=15, delta_bw=15, cost=1_000_000.0),
    _BwUpgradeEntry(min_tl=15, delta_bw=20, cost=2_500_000.0),
    _BwUpgradeEntry(min_tl=15, delta_bw=25, cost=5_000_000.0),
)


def _lookup(table: tuple[_BrainEntry, ...], tl: int) -> _BrainEntry:
    """Return the highest table entry whose TL is ≤ tl; fall back to lowest."""
    entry = table[0]
    for e in table:
        if e.tl <= tl:
            entry = e
    return entry


class _BrainBase(CeresModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    brain_tl: int = 0  # subclasses override with their default

    def _entry(self) -> _BrainEntry:
        raise NotImplementedError

    @property
    def base_int(self) -> int:
        raise NotImplementedError

    @property
    def brain_cost(self) -> float:
        raise NotImplementedError

    @property
    def skill_dm(self) -> int:
        raise NotImplementedError

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        return ()

    def skill_grants_for_robot(self, dex_dm: int, str_dm: int = 0) -> tuple[SkillGrant, ...]:
        return self.skill_grants

    @property
    def hardware_cost(self) -> float:
        return self.brain_cost

    @property
    def remaining_bandwidth(self) -> int | None:
        return None

    @property
    def brain_traits(self) -> tuple:
        return ()

    def brain_slots(self, robot_tl: int, robot_size: int) -> int:
        raise NotImplementedError

    def programming_label(self) -> str:
        raise NotImplementedError


class _SimpleBrain(_BrainBase):
    """Shared base for PrimitiveBrain and BasicBrain."""

    _table: ClassVar[tuple[_BrainEntry, ...]]
    _label: ClassVar[str]

    function: str = 'none'

    def _entry(self) -> _BrainEntry:
        return _lookup(self._table, self.brain_tl)

    @property
    def base_int(self) -> int:
        return self._entry().base_int

    @property
    def bandwidth(self) -> int:
        return self._entry().bandwidth

    @property
    def brain_cost(self) -> float:
        return self._entry().cost

    @property
    def skill_dm(self) -> int:
        return self._entry().skill_dm

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        return primitive_package_skills(self.function)

    def brain_slots(self, robot_tl: int, robot_size: int) -> int:
        entry = self._entry()
        min_free = max(0, entry.computer_x - (robot_tl - entry.tl))
        return 1 if robot_size < min_free else 0

    def programming_label(self) -> str:
        int_val = self._entry().base_int
        if self.function and self.function != 'none':
            return f'{self._label} ({self.function}) (INT {int_val})'
        return f'{self._label} (INT {int_val})'


class PrimitiveBrain(_SimpleBrain):
    type: Literal['PRIMITIVE'] = 'PRIMITIVE'
    brain_tl: int = 8
    _table: ClassVar[tuple[_BrainEntry, ...]] = _PRIMITIVE_TABLE
    _label: ClassVar[str] = 'Primitive'


class BasicBrain(_SimpleBrain):
    type: Literal['BASIC'] = 'BASIC'
    brain_tl: int = 10
    _table: ClassVar[tuple[_BrainEntry, ...]] = _BASIC_TABLE
    _label: ClassVar[str] = 'Basic'


class _AdvancedBrainBase(_BrainBase):
    """Shared base for AdvancedBrain, VeryAdvancedBrain, and SelfAwareBrain."""

    _table: ClassVar[tuple[_BrainEntry, ...]]
    _bw_upgrades: ClassVar[tuple[_BwUpgradeEntry, ...]]

    installed_skills: tuple[SkillPackage, ...] = ()
    # refs/robot/34_retrotech.md — INT upgrade: INT+n costs n(n+1)/2 BW and
    # product(base_int+1 … base_int+n) × Cr1000. Max INT+3 per rules.
    int_upgrade: int = Field(default=0, ge=0, le=3)
    # 0 = sentinel meaning "use base bandwidth"; validated and replaced in _resolve_bandwidth.
    # Non-zero values must match base + a valid Brain Bandwidth Upgrade delta for brain_tl.
    bandwidth: int = Field(default=0, ge=0)

    @model_validator(mode='before')
    @classmethod
    def _resolve_bandwidth(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        d = cast(dict[str, Any], data)
        field_info = cls.model_fields.get('brain_tl')
        default_tl = field_info.default if field_info is not None else 12
        brain_tl = d.get('brain_tl', default_tl)
        entry = _lookup(cls._table, brain_tl)
        base = entry.bandwidth
        bw = d.get('bandwidth') or 0
        if bw == 0:
            return {**d, 'bandwidth': base}
        if bw != base:
            valid = {base + e.delta_bw for e in cls._bw_upgrades if brain_tl >= e.min_tl}
            if bw not in valid:
                raise ValueError(
                    f'bandwidth {bw} is not valid for {cls.__name__} at TL{brain_tl}; '
                    f'valid values: {sorted({base} | valid)}'
                )
        return d

    def _entry(self) -> _BrainEntry:
        return _lookup(self._table, self.brain_tl)

    @property
    def _int_upgrade_bw(self) -> int:
        n = self.int_upgrade
        return n * (n + 1) // 2

    @property
    def _int_upgrade_cost(self) -> float:
        if self.int_upgrade == 0:
            return 0.0
        base_int = self._entry().base_int
        product = 1
        for i in range(1, self.int_upgrade + 1):
            product *= base_int + i
        # Cost ×2 when the upgrade brings INT to 12 or above (refs/robot/34_retrotech.md)
        multiplier = 2 if base_int + self.int_upgrade >= 12 else 1
        return float(product * 1000 * multiplier)

    @property
    def _bw_upgrade_delta(self) -> int:
        return self.bandwidth - self._entry().bandwidth

    @property
    def _bw_upgrade_cost(self) -> float:
        delta = self._bw_upgrade_delta
        if delta == 0:
            return 0.0
        for e in self._bw_upgrades:
            if self.brain_tl >= e.min_tl and e.delta_bw == delta:
                return e.cost
        return 0.0

    @property
    def base_int(self) -> int:
        return self._entry().base_int + self.int_upgrade

    @property
    def skill_dm(self) -> int:
        return self._entry().skill_dm + self.int_upgrade

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        dm = self.skill_dm
        return tuple(pkg.skill_grant(max(0, pkg.level + dm)) for pkg in self.installed_skills)

    def skill_grants_for_robot(self, dex_dm: int, str_dm: int = 0) -> tuple[SkillGrant, ...]:
        int_dm = self.skill_dm
        result = []
        for pkg in self.installed_skills:
            if pkg.uses_str_dm:
                dm = str_dm
            elif pkg.uses_dex_dm:
                dm = dex_dm
            else:
                dm = int_dm
            result.append(
                pkg.skill_grant(
                    max(0, pkg.level + dm),
                    exact_speciality=pkg.uses_exact_speciality_dm,
                )
            )
        return tuple(result)

    @property
    def used_bandwidth(self) -> int:
        return self._int_upgrade_bw + sum(pkg.bandwidth for pkg in self.installed_skills)

    @property
    def remaining_bandwidth(self) -> int | None:
        return self.bandwidth - self.used_bandwidth

    def brain_slots(self, robot_tl: int, robot_size: int) -> int:
        entry = self._entry()
        min_free = max(0, entry.computer_x - (robot_tl - entry.tl))
        base = 1 if robot_size < min_free else 0
        return base + (1 if self._bw_upgrade_delta > 0 else 0)

    def _harden_cost(self, base: float, bw_cost: float) -> float:
        """Apply +50% surcharge to brain hardware and BW upgrade costs."""
        brain_hardware = self._entry().cost + self._int_upgrade_cost
        return base - bw_cost + brain_hardware * 0.5 + bw_cost * 1.5


class AdvancedBrain(_AdvancedBrainBase):
    type: Literal['ADVANCED'] = 'ADVANCED'
    brain_tl: int = 12
    _table: ClassVar[tuple[_BrainEntry, ...]] = _ADVANCED_TABLE
    _bw_upgrades: ClassVar[tuple[_BwUpgradeEntry, ...]] = _ADVANCED_BW_UPGRADES
    # refs/robot/34_retrotech.md — Brain Hardening: +50% cost on brain hardware and BW upgrade.
    hardened: bool = False

    @property
    def brain_cost(self) -> float:
        bw_cost = self._bw_upgrade_cost
        base = self._entry().cost + self._int_upgrade_cost + bw_cost + sum(pkg.cost for pkg in self.installed_skills)
        if self.hardened:
            base = self._harden_cost(base, bw_cost)
        return base

    @property
    def hardware_cost(self) -> float:
        bw_cost = self._bw_upgrade_cost
        base = self._entry().cost + self._int_upgrade_cost + bw_cost
        if self.hardened:
            base = self._harden_cost(base, bw_cost)
        return base

    @property
    def brain_traits(self) -> tuple:
        from .chassis import Trait

        if self.hardened:
            return (Trait('Hardened'),)
        return ()

    def programming_label(self) -> str:
        return f'Advanced (INT {self.base_int})'


class VeryAdvancedBrain(_AdvancedBrainBase):
    type: Literal['VERY_ADVANCED'] = 'VERY_ADVANCED'
    brain_tl: int = 12
    _table: ClassVar[tuple[_BrainEntry, ...]] = _VERY_ADVANCED_TABLE
    _bw_upgrades: ClassVar[tuple[_BwUpgradeEntry, ...]] = _VERY_ADVANCED_BW_UPGRADES

    @property
    def brain_cost(self) -> float:
        return (
            self._entry().cost
            + self._int_upgrade_cost
            + self._bw_upgrade_cost
            + sum(pkg.cost for pkg in self.installed_skills)
        )

    @property
    def hardware_cost(self) -> float:
        return self._entry().cost + self._int_upgrade_cost + self._bw_upgrade_cost

    def programming_label(self) -> str:
        return f'Very Advanced (INT {self.base_int})'


class SelfAwareBrain(_AdvancedBrainBase):
    type: Literal['SELF_AWARE'] = 'SELF_AWARE'
    brain_tl: int = 15
    _table: ClassVar[tuple[_BrainEntry, ...]] = _SELF_AWARE_TABLE
    _bw_upgrades: ClassVar[tuple[_BwUpgradeEntry, ...]] = _SELF_AWARE_BW_UPGRADES
    installed_software: tuple[BrainSoftware, ...] = ()
    # refs/robot/34_retrotech.md — Brain Hardening: +50% cost on brain hardware and BW upgrade.
    hardened: bool = False

    @property
    def brain_cost(self) -> float:
        bw_cost = self._bw_upgrade_cost
        base = (
            self._entry().cost
            + self._int_upgrade_cost
            + bw_cost
            + sum(pkg.cost for pkg in self.installed_skills)
            + sum(sw.cost for sw in self.installed_software)
        )
        if self.hardened:
            base = self._harden_cost(base, bw_cost)
        return base

    @property
    def hardware_cost(self) -> float:
        bw_cost = self._bw_upgrade_cost
        base = self._entry().cost + self._int_upgrade_cost + bw_cost
        if self.hardened:
            base = self._harden_cost(base, bw_cost)
        return base

    @property
    def brain_traits(self) -> tuple:
        from .chassis import Trait

        if self.hardened:
            return (Trait('Hardened'),)
        return ()

    @property
    def used_bandwidth(self) -> int:
        return (
            self._int_upgrade_bw
            + sum(pkg.bandwidth for pkg in self.installed_skills)
            + sum(sw.bandwidth for sw in self.installed_software)
        )

    def programming_label(self) -> str:
        return f'Self-Aware (INT {self.base_int})'


RobotBrainUnion = Annotated[
    PrimitiveBrain | BasicBrain | AdvancedBrain | VeryAdvancedBrain | SelfAwareBrain,
    Field(discriminator='type'),
]


def UniversalTranslator() -> BrainSoftware:
    """refs/csc/06_computers_and_software.md — Universal Translator software package.

    Bandwidth 3, TL12, Cr25,000. Installed in a robot brain's software suite.
    """
    return BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25_000.0)


__all__ = [
    'AdvancedBrain',
    'BasicBrain',
    'PrimitiveBrain',
    'RobotBrainUnion',
    'SelfAwareBrain',
    'UniversalTranslator',
    'VeryAdvancedBrain',
]
