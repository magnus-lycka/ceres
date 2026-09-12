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


# Skills the rules let you resolve with more than one characteristic. Melee is the only
# one for a robot: refs/core/03_combat.md gives the melee attack as
# '2D + Melee (appropriate speciality) + STR or DEX DM', the attacker's choice, and the
# grapple rules repeat it. Every other multi-characteristic skill in the core rules
# chooses among INT, EDU and SOC, which are one characteristic for a robot
# (refs/robot/35_skill_packages.md).
_MULTI_CHARACTERISTIC_SKILLS: dict[type[Skill], tuple[Chars, ...]] = {
    _char.Melee: (Chars.STR, Chars.DEX),
}


def _skill_characteristics(skill_cls: type[Skill]) -> tuple[Chars, ...]:
    multi = _MULTI_CHARACTERISTIC_SKILLS.get(skill_cls)
    if multi is not None:
        return multi
    return (Chars.DEX,) if skill_cls in _DEX_SKILLS else (Chars.INT,)


def _field_characteristics(skill_cls: type[Skill], field_name: str) -> tuple[Chars, ...]:
    """Characteristics this speciality may use; empty when it takes none."""
    key = (skill_cls, field_name)
    if key in _NULL_SKILL_KEYS:
        return ()
    if key in _STR_SKILL_KEYS:
        return (Chars.STR,)
    if key in _INT_SKILL_KEYS:
        return (Chars.INT,)
    if key in _DEX_SKILL_KEYS:
        return (Chars.DEX,)
    return _skill_characteristics(skill_cls)


def _best_dm(characteristics: tuple[Chars, ...], dms: dict[Chars, int]) -> int:
    """Best DM among the applicable characteristics — the check taker picks."""
    return max((dms.get(char, 0) for char in characteristics), default=0)


# A robot's skill level is one reading per applicable characteristic DM. Most skills
# have a single reading; a DEX skill on a robot whose manipulators differ in DEX has
# one per manipulator group, since refs/robot/09_manipulators.md leaves the choice of
# manipulator — and therefore the DM — to the Referee.
Readings = tuple[int, ...]

# (skill class, characteristic label, speciality). The characteristic label is set only
# for skills the rules let you resolve with more than one characteristic, where each
# gets its own row — the choice is the check taker's and the levels genuinely differ.
SpecKey = tuple[type[Skill], str | None, str | None]


def _format_readings(readings: Readings) -> str:
    """Render usable readings highest first — the best, and usually typical, case leads.

    A reading below zero means the manipulator in question is worse than useless for the
    task; it is left out rather than shown or clamped, since clamping would claim a
    competence the robot does not have.
    """
    distinct = sorted({r for r in readings if r >= 0}, reverse=True)
    return '/'.join(str(r) for r in distinct)


def _entry_name(skill_cls: type[Skill], char_label: str | None, suffix: str | None) -> str:
    parts = [p for p in (char_label, suffix) if p]
    return f'{skill_cls.name()} ({", ".join(parts)})' if parts else skill_cls.name()


def _compact_specs(
    per_spec: dict[SpecKey, Readings],
) -> dict[str, Readings]:
    """Compact per-speciality readings to a display dict.

    All specialities at the same reading, non-zero → 'Skill (All)'.
    All at zero → 'Skill'.
    Mixed, with two or more specialities sharing a non-zero baseline →
    'Skill (Other)' for the baseline plus 'Skill (Spec)' for each outlier.
    Mixed otherwise → individual 'Skill (Spec)' for each non-zero reading.
    No-speciality entry (spec=None) → 'Skill'.
    """
    groups: dict[tuple[type[Skill], str | None], dict[str | None, Readings]] = {}
    for (skill_cls, char_label, spec), readings in per_spec.items():
        groups.setdefault((skill_cls, char_label), {})[spec] = readings

    result: dict[str, Readings] = {}
    for (skill_cls, char_label), spec_levels in groups.items():
        if None in spec_levels:
            readings = spec_levels[None]
            if max(readings) >= 0:
                result[_entry_name(skill_cls, char_label, None)] = readings
            continue
        all_specs = skill_cls.specialities()
        named = {s: r for s, r in spec_levels.items() if s is not None}
        if all_specs and set(named) == set(all_specs) and len(set(named.values())) == 1:
            readings = next(iter(named.values()))
            if max(readings) > 0:
                result[_entry_name(skill_cls, char_label, 'All')] = readings
            elif max(readings) == 0:
                result[_entry_name(skill_cls, char_label, None)] = readings
        else:
            baseline = _baseline_readings(named, all_specs)
            for spec, readings in named.items():
                if max(readings) > 0 and readings != baseline:
                    result[_entry_name(skill_cls, char_label, spec)] = readings
            if baseline is not None:
                result[_entry_name(skill_cls, char_label, 'Other')] = baseline
    return result


def _specs_to_display_dict(
    per_spec: dict[SpecKey, int],
) -> dict[str, int]:
    """Single-reading display dict — see _compact_specs."""
    compacted = _compact_specs({key: (lvl,) for key, lvl in per_spec.items()})
    return {name: readings[0] for name, readings in compacted.items()}


def _specs_to_multi_display_dict(per_specs: list[dict[SpecKey, int]]) -> dict[str, str]:
    """Display dict carrying one reading per manipulator profile, 'a/b/c', highest first.

    Readings are gathered before compaction: the zero-level exclusion means they can
    compact to different shapes, so compacting each separately and matching keys
    afterwards would misalign them.
    """
    first = per_specs[0]
    combined: dict[SpecKey, Readings] = {
        key: tuple(per_spec.get(key, lvl) for per_spec in per_specs) for key, lvl in first.items()
    }
    return {name: _format_readings(readings) for name, readings in _compact_specs(combined).items()}


# A '(Other)' group must stand for at least two specialities; one is just named.
_MIN_OTHER_GROUP = 2


def _baseline_readings(named: dict[str, Readings], all_specs: tuple[str, ...]) -> Readings | None:
    """Readings shared by the '(Other)' group, or None when there is nothing to compact.

    Only a complete speciality set can be compacted — with a partial set '(Other)'
    would claim coverage the robot has not been given. The baseline is the reading held
    by the largest group of two or more; ties resolve to the lower reading, since the
    lower is the safer one to attribute to unnamed specialities.
    """
    if not all_specs or set(named) != set(all_specs):
        return None
    counts: dict[Readings, int] = {}
    for readings in named.values():
        if max(readings) > 0:
            counts[readings] = counts.get(readings, 0) + 1
    candidates = [
        (count, tuple(-r for r in readings)) for readings, count in counts.items() if count >= _MIN_OTHER_GROUP
    ]
    if not candidates:
        return None
    return tuple(-r for r in max(candidates)[1])


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

    def _per_spec_raw(self, dms: dict[Chars, int], *, split_characteristics: bool = True) -> dict[SpecKey, int] | None:
        """Raw per-speciality entries keyed by (char_cls, char_label, spec_label).

        Returns None for skills that manage their own display (e.g. when _char_cls is None).
        With split_characteristics=False a multi-characteristic skill stays a single entry,
        which is what the purchased package is — see package_entries.
        """
        char_cls = type(self)._char_cls
        if char_cls is None:
            return None
        level = getattr(self, 'level', 0)
        if not char_cls.specialities():
            characteristics = _skill_characteristics(char_cls)
            if len(characteristics) > 1 and split_characteristics:
                return {(char_cls, char.value, None): level + dms.get(char, 0) for char in characteristics}
            return {(char_cls, None, None): level + _best_dm(characteristics, dms)}
        skill_level = level
        instance = char_cls()
        result: dict[SpecKey, int] = {}
        for field_name in level_fields(char_cls):
            characteristics = _field_characteristics(char_cls, field_name)
            if not characteristics:
                continue
            raw = skill_level if skill_level > 0 else getattr(self, field_name, 0)
            label = speciality_label(instance, field_name)
            if len(characteristics) > 1 and split_characteristics:
                for char in characteristics:
                    result[(char_cls, char.value, label)] = raw + dms.get(char, 0)
            else:
                result[(char_cls, None, label)] = raw + _best_dm(characteristics, dms)
        return result

    def display_entries(self, dms: dict[Chars, int]) -> dict[str, int]:
        """Effective skill display after applying characteristic DMs."""
        raw = self._per_spec_raw(dms)
        if raw is None:
            return {type(self).skill_name(): 0}
        return _specs_to_display_dict(raw)

    def package_entries(self) -> dict[str, int]:
        """The package as purchased: levels with no characteristic DMs applied.

        A Melee package is one purchase however many characteristics it may later be
        resolved with, so the build ledger names it once and without a characteristic.
        """
        raw = self._per_spec_raw({}, split_characteristics=False)
        if raw is None:
            # A facade that manages its own display: with no DMs that display is the
            # purchased package.
            return self.display_entries({})
        return _specs_to_display_dict(raw)
