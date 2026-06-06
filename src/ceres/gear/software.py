from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, ClassVar, Literal

from pydantic import ConfigDict, Field, PrivateAttr, field_validator

from ceres.character.domain import skills as character_skills
from ceres.character.domain.skills import AnySkill, Skill, active_speciality_field, active_speciality_label
from ceres.gear.skill_keys import SkillCostKey, key_matches_skill
from ceres.shared import CeresModel, NoteList, _Note

if TYPE_CHECKING:
    from ceres.gear.computer import ComputerPart


class SoftwarePackage(CeresModel, ABC):
    package: str
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def bandwidth(self) -> int: ...

    @property
    @abstractmethod
    def tl(self) -> int: ...

    @property
    @abstractmethod
    def cost(self) -> float: ...

    def _computer_effective_tl(self, computer: ComputerPart) -> int:
        return getattr(computer, 'effective_tl', computer.assembly.tl - computer.retro_levels)

    def _validate_tl_on_computer(self, computer: ComputerPart) -> bool:
        effective_tl = self._computer_effective_tl(computer)
        if self.tl > effective_tl:
            self.warning(f'{self.description} requires TL{self.tl}, but computer effective TL is {effective_tl}')
        return True

    def validate_on_computer(self, computer: ComputerPart) -> None:
        self._validate_tl_on_computer(computer)


class FixedSoftwarePackage(SoftwarePackage):
    label: ClassVar[str]
    _bandwidth: ClassVar[int]
    _tl: ClassVar[int]
    _cost: ClassVar[float]

    @property
    def description(self) -> str:
        return self.label

    @property
    def bandwidth(self) -> int:
        return self._bandwidth

    @property
    def tl(self) -> int:
        return self._tl

    @property
    def cost(self) -> float:
        return self._cost

    def validate_on_computer(self, computer: ComputerPart) -> None:
        super().validate_on_computer(computer)
        if computer.processing < self.bandwidth:
            self.error(f'{computer.description} cannot run {self.description}')


class RatedSoftwarePackage(SoftwarePackage):
    rating: int
    _label: ClassVar[str]
    _specs: ClassVar[dict[int, dict[str, int | float]]]
    _effective_rating: int | None = PrivateAttr(default=None)

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, value: int) -> int:
        if value not in cls._specs:
            allowed = ', '.join(str(v) for v in sorted(cls._specs))
            raise ValueError(f'Unsupported {cls.__name__} rating {value}; expected one of: {allowed}')
        return value

    @classmethod
    def maximum_rating(cls) -> int:
        return max(cls._specs)

    @classmethod
    def maximum_rating_at_tl(cls, tl: int) -> int | None:
        supported = [rating for rating, spec in cls._specs.items() if int(spec['tl']) <= tl]
        return max(supported, default=None)

    @property
    def description(self) -> str:
        return f'{self._label}/{self.rating}'

    @property
    def bandwidth(self) -> int:
        return int(self._specs[self.rating]['bandwidth'])

    @property
    def tl(self) -> int:
        return int(self._specs[self.rating]['tl'])

    @property
    def cost(self) -> float:
        return float(self._specs[self.rating]['cost'])

    @property
    def effective_rating(self) -> int | None:
        return self._effective_rating

    def validate_on_computer(self, computer: ComputerPart) -> None:
        super().validate_on_computer(computer)
        if computer.processing < self.bandwidth:
            self.error(f'{computer.description} cannot run {self.description}')
            return
        self._effective_rating = self.rating


class Interface(FixedSoftwarePackage):
    package: Literal['interface'] = 'interface'
    label = 'Interface'
    _bandwidth = 0
    _tl = 7
    _cost = 0.0


class IntelligentInterface(FixedSoftwarePackage):
    package: Literal['intelligent_interface'] = 'intelligent_interface'
    label = 'Intelligent Interface'
    _bandwidth = 1
    _tl = 11
    _cost = 100.0


class Security(RatedSoftwarePackage):
    package: Literal['security'] = 'security'
    _label = 'Security'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'bandwidth': 0, 'tl': 8, 'cost': 0.0},
        1: {'bandwidth': 1, 'tl': 10, 'cost': 200.0},
        2: {'bandwidth': 2, 'tl': 11, 'cost': 1_000.0},
        3: {'bandwidth': 3, 'tl': 12, 'cost': 20_000.0},
    }


class Agent(RatedSoftwarePackage):
    package: Literal['agent_sw'] = 'agent_sw'
    _label = 'Agent'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'bandwidth': 0, 'tl': 11, 'cost': 500.0},
        1: {'bandwidth': 1, 'tl': 12, 'cost': 2_000.0},
        2: {'bandwidth': 2, 'tl': 13, 'cost': 100_000.0},
        3: {'bandwidth': 3, 'tl': 14, 'cost': 250_000.0},
    }


class Intellect(RatedSoftwarePackage):
    package: Literal['intellect'] = 'intellect'
    _label = 'Intellect'
    # rating=0 is the HG ship-included intellect (free, no bandwidth cost); 1–3 are CSC packages
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'bandwidth': 0, 'tl': 11, 'cost': 0.0},
        1: {'bandwidth': 1, 'tl': 12, 'cost': 2_000.0},
        2: {'bandwidth': 2, 'tl': 13, 'cost': 50_000.0},
        3: {'bandwidth': 3, 'tl': 14, 'cost': 200_000.0},
    }

    @property
    def description(self) -> str:
        if self.rating == 0:
            return self._label
        return f'{self._label}/{self.rating}'


class Translator(RatedSoftwarePackage):
    package: Literal['translator'] = 'translator'
    _label = 'Translator'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'bandwidth': 0, 'tl': 9, 'cost': 50.0},
        1: {'bandwidth': 1, 'tl': 10, 'cost': 500.0},
    }


type _SkillSpecKey = SkillCostKey


def _skill_spec(skill_cls: type[Skill], speciality: str) -> tuple[type[Skill], str]:
    return skill_cls, speciality


_EXPERT_SKILL_SPECS: dict[_SkillSpecKey, dict[str, int | float]] = {
    character_skills.Admin: {'tl': 8, 'cost': 100.0},
    character_skills.Advocate: {'tl': 10, 'cost': 500.0},
    _skill_spec(character_skills.Animals, 'veterinary'): {'tl': 9, 'cost': 200.0},
    character_skills.ArtSkill: {'tl': 9, 'cost': 200.0},
    character_skills.Astrogation: {'tl': 12, 'cost': 500.0},
    character_skills.Broker: {'tl': 10, 'cost': 200.0},
    character_skills.Electronics: {'tl': 8, 'cost': 100.0},
    character_skills.Engineer: {'tl': 9, 'cost': 200.0},
    character_skills.Explosives: {'tl': 8, 'cost': 100.0},
    character_skills.Gambler: {'tl': 10, 'cost': 500.0},
    character_skills.Languages: {'tl': 9, 'cost': 200.0},
    character_skills.Mechanic: {'tl': 8, 'cost': 100.0},
    character_skills.Medic: {'tl': 9, 'cost': 200.0},
    character_skills.Navigation: {'tl': 8, 'cost': 100.0},
    character_skills.ProfessionSkill: {'tl': 9, 'cost': 200.0},
    character_skills.ScienceSkill: {'tl': 9, 'cost': 200.0},
    character_skills.Steward: {'tl': 8, 'cost': 100.0},
    character_skills.Survival: {'tl': 10, 'cost': 200.0},
    character_skills.Tactics: {'tl': 8, 'cost': 100.0},
}


class Expert(SoftwarePackage):
    package: Literal['expert'] = 'expert'
    rating: int
    skill: AnySkill

    KNOWN_SKILLS: ClassVar[dict[_SkillSpecKey, dict[str, int | float]]] = _EXPERT_SKILL_SPECS
    FALLBACK_TL: ClassVar[int] = 11
    FALLBACK_COST: ClassVar[float] = 1_000.0

    @property
    def description(self) -> str:
        return f'Expert ({self.skill_name})/{self.rating}'

    @property
    def bandwidth(self) -> int:
        return self.rating

    @property
    def tl(self) -> int:
        return int(self._resolved_spec['tl']) + self.rating - 1

    @property
    def cost(self) -> float:
        return float(self._resolved_spec['cost']) * (10 ** (self.rating - 1))

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        if self.rating not in {1, 2, 3}:
            notes.error(f'Invalid Expert rating {self.rating}; expected one of: 1, 2, 3')
        if not self._has_known_skill_spec:
            notes.warning(f'Unfamiliar Expert skill {self.skill_name} uses CSC fallback values')
        return notes

    @property
    def _resolved_spec(self) -> dict[str, int | float]:
        cls = type(self)
        spec = cls.KNOWN_SKILLS.get(self._skill_key)
        if spec is not None:
            return spec
        spec = cls.KNOWN_SKILLS.get(self._skill_type_key)
        if spec is not None:
            return spec
        if group_spec := self._skill_group_spec:
            return group_spec
        return {'tl': cls.FALLBACK_TL, 'cost': cls.FALLBACK_COST}

    @property
    def _has_known_skill_spec(self) -> bool:
        return (
            self._skill_key in type(self).KNOWN_SKILLS
            or self._skill_type_key in type(self).KNOWN_SKILLS
            or self._skill_group_spec is not None
        )

    @property
    def _skill_key(self) -> tuple[type[Skill], str | None]:
        return type(self.skill), active_speciality_field(self.skill)

    @property
    def _skill_type_key(self) -> type[Skill]:
        return type(self.skill)

    @property
    def _skill_group_spec(self) -> dict[str, int | float] | None:
        skill_cls = type(self.skill)
        for key, spec in type(self).KNOWN_SKILLS.items():
            if isinstance(key, tuple):
                continue
            if key is skill_cls:
                continue
            if key_matches_skill(key, skill_cls):
                return spec
        return None

    @property
    def skill_name(self) -> str:
        skill_type = self.skill.name()
        speciality = active_speciality_label(self.skill)
        if speciality is None:
            return skill_type
        return f'{skill_type} ({speciality})'


type AnySoftware = Annotated[
    Agent | Expert | Intellect | IntelligentInterface | Interface | Security | Translator,
    Field(discriminator='package'),
]
