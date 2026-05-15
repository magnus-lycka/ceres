from dataclasses import dataclass
from enum import IntEnum
from math import ceil


class RobotSize(IntEnum):
    SIZE_1 = 1
    SIZE_2 = 2
    SIZE_3 = 3
    SIZE_4 = 4
    SIZE_5 = 5
    SIZE_6 = 6
    SIZE_7 = 7
    SIZE_8 = 8


@dataclass(frozen=True)
class Trait:
    name: str
    value: int | str | None = None

    def __str__(self) -> str:
        if self.value is None:
            return self.name
        if isinstance(self.value, int):
            return f'{self.name} ({self.value:+d})'
        return f'{self.name} ({self.value})'


@dataclass(frozen=True)
class _ChassisEntry:
    base_slots: int
    base_hits: int
    attack_dm: int
    basic_cost: int


# refs/robot/04_chassis.md — Robot Size table
_CHASSIS: dict[RobotSize, _ChassisEntry] = {
    RobotSize.SIZE_1: _ChassisEntry(base_slots=1, base_hits=1, attack_dm=-4, basic_cost=100),
    RobotSize.SIZE_2: _ChassisEntry(base_slots=2, base_hits=4, attack_dm=-3, basic_cost=200),
    RobotSize.SIZE_3: _ChassisEntry(base_slots=4, base_hits=8, attack_dm=-2, basic_cost=400),
    RobotSize.SIZE_4: _ChassisEntry(base_slots=8, base_hits=12, attack_dm=-1, basic_cost=800),
    RobotSize.SIZE_5: _ChassisEntry(base_slots=16, base_hits=20, attack_dm=0, basic_cost=1000),
    RobotSize.SIZE_6: _ChassisEntry(base_slots=32, base_hits=32, attack_dm=1, basic_cost=2000),
    RobotSize.SIZE_7: _ChassisEntry(base_slots=64, base_hits=50, attack_dm=2, basic_cost=4000),
    RobotSize.SIZE_8: _ChassisEntry(base_slots=128, base_hits=72, attack_dm=3, basic_cost=8000),
}


def chassis_entry(size: RobotSize) -> _ChassisEntry:
    return _CHASSIS[size]


# refs/robot/07_chassis_options.md — Robot Armour table
_ARMOUR_TL_BANDS: list[tuple[int, int, int]] = [
    (6, 8, 2),
    (9, 11, 3),
    (12, 14, 4),
    (15, 17, 4),
    (18, 999, 5),
]


def base_armour(tl: int) -> int:
    for tl_min, tl_max, protection in _ARMOUR_TL_BANDS:
        if tl_min <= tl <= tl_max:
            return protection
    return 2  # below TL6: treated as TL6–8


# refs/robot/07_chassis_options.md — Endurance Modifier table
def base_endurance_multiplier(tl: int) -> float:
    if tl >= 15:
        return 2.0
    if tl >= 12:
        return 1.5
    return 1.0


def size_trait(size: RobotSize) -> Trait | None:
    dm = chassis_entry(size).attack_dm
    if dm < 0:
        return Trait('Small', dm)
    if dm > 0:
        return Trait('Large', dm)
    return None


def base_available_slots(size: RobotSize, *, none_locomotion: bool) -> int:
    base = chassis_entry(size).base_slots
    if none_locomotion:
        return ceil(base * 1.25)
    return base


__all__ = [
    'RobotSize',
    'Trait',
    'chassis_entry',
    'base_armour',
    'base_endurance_multiplier',
    'size_trait',
    'base_available_slots',
]
