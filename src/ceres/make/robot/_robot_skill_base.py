"""Base class and infrastructure for robot skill package facades."""

from typing import ClassVar

from pydantic import ConfigDict

from ceres.character.domain import skills as _char
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Skill, level_fields, speciality_label
from ceres.gear.skill_keys import SkillCostKey, key_matches_skill
from ceres.shared import CeresModel

# Per refs/robot/35_skill_packages.md Standard Skill Packages table.
# Tuple: (min_tl, base_bandwidth, base_cost_cr). Cost at level N = base_cost × 10^N.
_SKILL_PACKAGE_PROPS: dict[SkillCostKey, tuple[int, int, float]] = {
    _char.Admin: (8, 0, 100.0),
    _char.Advocate: (10, 0, 500.0),
    _char.Animals: (9, 0, 200.0),
    _char.ArtSkill: (10, 0, 500.0),
    _char.Astrogation: (12, 1, 500.0),
    _char.Athletics: (8, 0, 100.0),
    _char.Broker: (10, 0, 200.0),
    _char.Carouse: (11, 1, 500.0),
    _char.Deception: (13, 1, 1000.0),
    _char.Diplomat: (10, 1, 500.0),
    _char.Drive: (8, 0, 100.0),
    _char.Electronics: (8, 0, 100.0),
    _char.Engineer: (9, 0, 200.0),
    _char.Explosives: (8, 0, 100.0),
    _char.Flyer: (8, 0, 100.0),
    _char.Gambler: (10, 0, 500.0),
    _char.GunCombat: (8, 0, 100.0),
    _char.Gunner: (8, 0, 100.0),
    _char.HeavyWeapons: (8, 0, 100.0),
    _char.Investigate: (11, 1, 500.0),
    _char.Languages: (9, 0, 200.0),
    _char.Leadership: (13, 1, 1000.0),
    _char.Mechanic: (8, 0, 100.0),
    _char.Medic: (9, 0, 200.0),
    _char.Melee: (8, 0, 100.0),
    _char.Navigation: (8, 0, 100.0),
    _char.Persuade: (11, 1, 500.0),
    _char.Pilot: (8, 0, 100.0),
    _char.ProfessionSkill: (9, 0, 200.0),
    _char.Recon: (10, 0, 500.0),
    _char.ScienceSkill: (9, 0, 200.0),
    _char.Seafarer: (8, 0, 100.0),
    _char.Stealth: (10, 0, 500.0),
    _char.Steward: (8, 0, 100.0),
    _char.Streetwise: (13, 1, 1000.0),
    _char.Survival: (10, 0, 200.0),
    _char.Tactics: (8, 0, 100.0),
}

_DEFAULT_PROPS: tuple[int, int, float] = (8, 0, 100.0)

# Skills whose base characteristic DM is DEX (not INT).
_DEX_SKILLS: frozenset[type[Skill]] = frozenset(
    {
        _char.Animals,
        _char.Drive,
        _char.Flyer,
        _char.GunCombat,
        _char.HeavyWeapons,
        _char.Melee,
        _char.Seafarer,
        _char.Stealth,
    }
)

_STR_SKILL_KEYS: frozenset[tuple[type[Skill], str]] = frozenset(
    {
        (_char.Athletics, 'strength'),
    }
)

_DEX_SKILL_KEYS: frozenset[tuple[type[Skill], str]] = frozenset(
    {
        (_char.Athletics, 'dexterity'),
        (_char.Gunner, 'screen'),
        (_char.Gunner, 'turret'),
        (_char.Pilot, 'small_craft'),
        (_char.Pilot, 'spacecraft'),
    }
)

_INT_SKILL_KEYS: frozenset[tuple[type[Skill], str]] = frozenset(
    {
        (_char.Animals, 'training'),
        (_char.Animals, 'veterinary'),
        (_char.Gunner, 'capital'),
        (_char.Gunner, 'ortillery'),
        (_char.Pilot, 'capital_ships'),
        (_char.Seafarer, 'ocean_ships'),
        (_char.Seafarer, 'submarine'),
    }
)

_NULL_SKILL_KEYS: frozenset[tuple[type[Skill], str]] = frozenset(
    {
        (_char.Athletics, 'endurance'),
    }
)


def _skill_props_for_class(skill_cls: type) -> tuple[int, int, float]:
    props = _SKILL_PACKAGE_PROPS.get(skill_cls)
    if props is not None:
        return props
    if issubclass(skill_cls, Skill):
        for key, props in _SKILL_PACKAGE_PROPS.items():
            if key is not skill_cls and key_matches_skill(key, skill_cls):
                return props
    return _DEFAULT_PROPS


def _field_characteristic(skill_cls: type[Skill], field_name: str) -> Chars | None:
    key = (skill_cls, field_name)
    if key in _NULL_SKILL_KEYS:
        return None
    if key in _STR_SKILL_KEYS:
        return Chars.STR
    if key in _INT_SKILL_KEYS:
        return Chars.INT
    if key in _DEX_SKILL_KEYS:
        return Chars.DEX
    return Chars.DEX if skill_cls in _DEX_SKILLS else Chars.INT


def _specs_to_display_dict(
    per_spec: dict[tuple[type[Skill], str | None], int],
) -> dict[str, int]:
    """Compact per-speciality levels to display dict.

    All specialities at same level N > 0 → 'Skill (All) N'.
    All at 0 → 'Skill 0'.
    Mixed → individual 'Skill (Spec) N' for each N > 0.
    No-speciality entry (spec=None) → 'Skill N'.
    """
    groups: dict[type[Skill], dict[str | None, int]] = {}
    for (skill_cls, spec), lvl in per_spec.items():
        groups.setdefault(skill_cls, {})[spec] = lvl

    result: dict[str, int] = {}
    for skill_cls, spec_levels in groups.items():
        if None in spec_levels:
            result[skill_cls.name()] = spec_levels[None]
            continue
        all_specs = skill_cls.specialities()
        named = {s: lvl for s, lvl in spec_levels.items() if s is not None}
        if all_specs and set(named) == set(all_specs) and len(set(named.values())) == 1:
            lvl = next(iter(named.values()))
            if lvl == 0:
                result[skill_cls.name()] = 0
            else:
                result[f'{skill_cls.name()} (All)'] = lvl
        else:
            for spec, lvl in named.items():
                if lvl > 0:
                    result[f'{skill_cls.name()} ({spec})'] = lvl
    return result


class _RobotSkill(CeresModel):
    """Base for robot skill package facades. Fields are int levels (default 0).

    Level 0 = no specialisation (one base package).
    Each field > 0 = one purchased specialisation package.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    _char_cls: ClassVar[type[Skill] | None]

    @classmethod
    def skill_name(cls) -> str:
        char_cls = cls._char_cls
        if char_cls is None:
            raise NotImplementedError(f'{cls.__name__} must override skill_name()')
        return char_cls.name()

    def _active_fields(self) -> list[tuple[str, int]]:
        return [
            (name, getattr(self, name))
            for name, fi in type(self).model_fields.items()
            if name not in {'type', 'display_label'} and fi.annotation is int and getattr(self, name) > 0
        ]

    @property
    def bandwidth(self) -> int:
        _, base_bw, _ = _skill_props_for_class(type(self)._char_cls or type(self))
        active = self._active_fields()
        return sum(base_bw + lvl for _, lvl in active) if active else base_bw

    @property
    def cost(self) -> float:
        _, _, base_cost = _skill_props_for_class(type(self)._char_cls or type(self))
        active = self._active_fields()
        return sum(base_cost * (10.0**lvl) for _, lvl in active) if active else base_cost

    @property
    def tl(self) -> int:
        return _skill_props_for_class(type(self)._char_cls or type(self))[0]

    def _per_spec_raw(self, dms: dict[Chars, int]) -> dict[tuple[type[Skill], str | None], int] | None:
        """Raw per-speciality entries keyed by (char_cls, spec_label) for cross-package compaction.

        Returns None for skills that manage their own display (e.g. when _char_cls is None).
        """
        char_cls = type(self)._char_cls
        if char_cls is None:
            return None
        if not char_cls.specialities():
            dm = dms.get(Chars.DEX if char_cls in _DEX_SKILLS else Chars.INT, 0)
            level = getattr(self, 'level', 0)
            return {(char_cls, None): max(0, level + dm)}
        skill_level = getattr(self, 'level', 0)
        instance = char_cls()
        result: dict[tuple[type[Skill], str | None], int] = {}
        for field_name in level_fields(char_cls):
            char = _field_characteristic(char_cls, field_name)
            if char is None:
                continue
            raw = skill_level if skill_level > 0 else getattr(self, field_name, 0)
            label = speciality_label(instance, field_name)
            result[(char_cls, label)] = max(0, raw + dms.get(char, 0))
        return result

    def display_entries(self, dms: dict[Chars, int]) -> dict[str, int]:
        """Effective skill display after applying characteristic DMs."""
        raw = self._per_spec_raw(dms)
        if raw is None:
            return {type(self).skill_name(): 0}
        return _specs_to_display_dict(raw)
