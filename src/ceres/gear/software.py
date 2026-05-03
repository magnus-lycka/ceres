from abc import ABC, abstractmethod
from typing import ClassVar, Literal

from pydantic import field_validator

from ceres.shared import CeresModel, Note, NoteCategory


class SoftwarePackage(CeresModel, ABC):
    package: str
    model_config = {'frozen': True}

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


class RatedSoftwarePackage(SoftwarePackage):
    rating: int
    _label: ClassVar[str]
    _specs: ClassVar[dict[int, dict[str, int | float]]]

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, value: int) -> int:
        if value not in cls._specs:
            allowed = ', '.join(str(v) for v in sorted(cls._specs))
            raise ValueError(f'Unsupported {cls.__name__} rating {value}; expected one of: {allowed}')
        return value

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
    package: Literal['agent'] = 'agent'
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
    # Intellect/0 is the HG ship intellect (free, included); 1–3 are CSC packages
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'bandwidth': 0, 'tl': 11, 'cost': 0.0},
        1: {'bandwidth': 1, 'tl': 12, 'cost': 2_000.0},
        2: {'bandwidth': 2, 'tl': 13, 'cost': 50_000.0},
        3: {'bandwidth': 3, 'tl': 14, 'cost': 200_000.0},
    }


class Translator(RatedSoftwarePackage):
    package: Literal['translator'] = 'translator'
    _label = 'Translator'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'bandwidth': 0, 'tl': 9, 'cost': 50.0},
        1: {'bandwidth': 1, 'tl': 10, 'cost': 500.0},
    }


class Expert(SoftwarePackage):
    package: Literal['expert'] = 'expert'
    rating: int
    skill: str

    KNOWN_SKILLS: ClassVar[dict[str, dict[str, int | float]]] = {
        'Admin': {'tl': 8, 'cost': 100.0},
        'Advocate': {'tl': 10, 'cost': 500.0},
        'Animals (Veterinary)': {'tl': 9, 'cost': 200.0},
        'Astrogation': {'tl': 12, 'cost': 500.0},
        'Broker': {'tl': 10, 'cost': 200.0},
        'Electronics (Computers)': {'tl': 8, 'cost': 100.0},
        'Electronics (Comms)': {'tl': 8, 'cost': 100.0},
        'Electronics (Remote Ops)': {'tl': 8, 'cost': 100.0},
        'Electronics (Sensors)': {'tl': 8, 'cost': 100.0},
        'Engineer (J-Drive)': {'tl': 9, 'cost': 200.0},
        'Engineer (Life Support)': {'tl': 9, 'cost': 200.0},
        'Engineer (M-Drive)': {'tl': 9, 'cost': 200.0},
        'Engineer (Power)': {'tl': 9, 'cost': 200.0},
        'Explosives': {'tl': 8, 'cost': 100.0},
        'Gambler': {'tl': 10, 'cost': 500.0},
        'Language Galanglic': {'tl': 9, 'cost': 200.0},
        'Language Gvegh': {'tl': 9, 'cost': 200.0},
        'Language Oynprith': {'tl': 9, 'cost': 200.0},
        'Language Trokh': {'tl': 9, 'cost': 200.0},
        'Language Vilani': {'tl': 9, 'cost': 200.0},
        'Language Zdetl': {'tl': 9, 'cost': 200.0},
        'Mechanic': {'tl': 8, 'cost': 100.0},
        'Medic': {'tl': 9, 'cost': 200.0},
        'Navigation': {'tl': 8, 'cost': 100.0},
        'Colonist Profession (Farming)': {'tl': 9, 'cost': 200.0},
        'Colonist Profession (Ranching)': {'tl': 9, 'cost': 200.0},
        'Freeloader Profession (Scrounging)': {'tl': 9, 'cost': 200.0},
        'Freeloader Profession (Security)': {'tl': 9, 'cost': 200.0},
        'Hostile Environment Profession (Contaminant)': {'tl': 9, 'cost': 200.0},
        'Hostile Environment Profession (High-G)': {'tl': 9, 'cost': 200.0},
        'Hostile Environment Profession (Low-G)': {'tl': 9, 'cost': 200.0},
        'Hostile Environment Profession (Underwater)': {'tl': 9, 'cost': 200.0},
        'Spacer Profession (Belter)': {'tl': 9, 'cost': 200.0},
        'Spacer Profession (Crewmember)': {'tl': 9, 'cost': 200.0},
        'Sport Profession (Atmosphere Surfing)': {'tl': 9, 'cost': 200.0},
        'Sport Profession (Golf)': {'tl': 9, 'cost': 200.0},
        'Sport Profession (Motorsports)': {'tl': 9, 'cost': 200.0},
        'Sport Profession (Racquet Sports)': {'tl': 9, 'cost': 200.0},
        'Sport Profession (Team Ball Sports)': {'tl': 9, 'cost': 200.0},
        'Sport Profession (Track & Field)': {'tl': 9, 'cost': 200.0},
        'Worker Profession (Armourer)': {'tl': 9, 'cost': 200.0},
        'Worker Profession (Biologicals)': {'tl': 9, 'cost': 200.0},
        'Worker Profession (Civil Engineering)': {'tl': 9, 'cost': 200.0},
        'Worker Profession (Construction)': {'tl': 9, 'cost': 200.0},
        'Worker Profession (Hydroponics)': {'tl': 9, 'cost': 200.0},
        'Worker Profession (Metalworking)': {'tl': 9, 'cost': 200.0},
        'Worker Profession (Polymers)': {'tl': 9, 'cost': 200.0},
        'Life Sciences (Biology)': {'tl': 9, 'cost': 200.0},
        'Life Sciences (Genetics)': {'tl': 9, 'cost': 200.0},
        'Life Sciences (Psionicology)': {'tl': 9, 'cost': 200.0},
        'Life Sciences (Xenology)': {'tl': 9, 'cost': 200.0},
        'Physical Sciences (Chemistry)': {'tl': 9, 'cost': 200.0},
        'Physical Sciences (Physics)': {'tl': 9, 'cost': 200.0},
        'Physical Sciences (Jumpspace Physics)': {'tl': 9, 'cost': 200.0},
        'Robotic Sciences (Cybernetics)': {'tl': 9, 'cost': 200.0},
        'Robotic Sciences (Robotics)': {'tl': 9, 'cost': 200.0},
        'Social Sciences (Archaeology)': {'tl': 9, 'cost': 200.0},
        'Social Sciences (Economics)': {'tl': 9, 'cost': 200.0},
        'Social Sciences (History)': {'tl': 9, 'cost': 200.0},
        'Social Sciences (Linguistics)': {'tl': 9, 'cost': 200.0},
        'Social Sciences (Philosophy)': {'tl': 9, 'cost': 200.0},
        'Social Sciences (Psychology)': {'tl': 9, 'cost': 200.0},
        'Social Sciences (Sophontology)': {'tl': 9, 'cost': 200.0},
        'Space Sciences (Astronomy)': {'tl': 9, 'cost': 200.0},
        'Space Sciences (Cosmology)': {'tl': 9, 'cost': 200.0},
        'Space Sciences (Planetology)': {'tl': 9, 'cost': 200.0},
        'Steward': {'tl': 8, 'cost': 100.0},
        'Survival': {'tl': 10, 'cost': 200.0},
        'Tactics (Military)': {'tl': 8, 'cost': 100.0},
        'Tactics (Naval)': {'tl': 8, 'cost': 100.0},
    }
    FALLBACK_TL: ClassVar[int] = 11
    FALLBACK_COST: ClassVar[float] = 1_000.0

    @field_validator('skill')
    @classmethod
    def validate_skill(cls, value: str) -> str:
        return ' '.join(value.strip().split())

    @property
    def description(self) -> str:
        return f'Expert ({self._resolved_skill_name})/{self.rating}'

    @property
    def bandwidth(self) -> int:
        return self.rating

    @property
    def tl(self) -> int:
        return int(self._resolved_spec['tl']) + self.rating - 1

    @property
    def cost(self) -> float:
        return float(self._resolved_spec['cost']) * (10 ** (self.rating - 1))

    def build_notes(self) -> list[Note]:
        notes = []
        if self.rating not in {1, 2, 3}:
            notes.append(
                Note(
                    category=NoteCategory.ERROR,
                    message=f'Invalid Expert rating {self.rating}; expected one of: 1, 2, 3',
                )
            )
        if not self.skill:
            notes.append(Note(category=NoteCategory.ERROR, message='Expert skill cannot be blank'))
        elif self.skill not in type(self).KNOWN_SKILLS:
            notes.append(
                Note(
                    category=NoteCategory.WARNING,
                    message=f'Unfamiliar Expert skill {self.skill} uses CSC fallback values',
                )
            )
        return notes

    @property
    def _resolved_spec(self) -> dict[str, int | float]:
        cls = type(self)
        return cls.KNOWN_SKILLS.get(self.skill, {'tl': cls.FALLBACK_TL, 'cost': cls.FALLBACK_COST})

    @property
    def _resolved_skill_name(self) -> str:
        return self.skill
