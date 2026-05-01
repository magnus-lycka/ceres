from typing import ClassVar, Literal

from pydantic import field_validator, model_validator

from ceres.make.ship.base import CeresModel, Note, NoteCategory


class SoftwarePackage(CeresModel):
    package: str
    model_config = {'frozen': True}

    @property
    def description(self) -> str:
        raise NotImplementedError

    @property
    def bandwidth(self) -> int:
        raise NotImplementedError

    @property
    def tl(self) -> int:
        raise NotImplementedError

    @property
    def cost(self) -> float:
        raise NotImplementedError


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

    def __init__(self, rating: int | None = None, /, **data):
        if rating is not None and 'rating' not in data:
            data['rating'] = rating
        super().__init__(**data)

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


class Intellect(RatedSoftwarePackage):
    package: Literal['intellect'] = 'intellect'
    _label = 'Intellect'
    # Note that Intellect/0 it High Guard Intellect, 1-3 i CSC
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'bandwidth': 0, 'tl': 11, 'cost': 0.0},
        1: {'bandwidth': 1, 'tl': 12, 'cost': 2_000.0},
        2: {'bandwidth': 2, 'tl': 13, 'cost': 50_000.0},
        3: {'bandwidth': 3, 'tl': 14, 'cost': 200_000.0},
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
    }
    BROAD_SKILL_ROOTS: ClassVar[set[str]] = {'Art', 'Profession', 'Science'}
    FALLBACK_TL: ClassVar[int] = 11
    FALLBACK_COST: ClassVar[float] = 1_000.0

    def __init__(self, rating: int | None = None, /, *, skill: str, **data):
        if rating is not None and 'rating' not in data:
            data['rating'] = rating
        super().__init__(skill=skill, **data)

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, value: int) -> int:
        if value not in {1, 2, 3}:
            raise ValueError('Unsupported Expert rating; expected one of: 1, 2, 3')
        return value

    @field_validator('skill')
    @classmethod
    def validate_skill(cls, value: str) -> str:
        skill = ' '.join(value.strip().split())
        if not skill:
            raise ValueError('Expert skill cannot be blank')
        return skill

    @model_validator(mode='after')
    def validate_known_shape(self):
        if self.skill in type(self).BROAD_SKILL_ROOTS:
            raise ValueError(f'{self.skill} is a broad skill; use a specialised form')
        return self

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
        if self.skill in type(self).KNOWN_SKILLS:
            return []
        return [
            Note(
                category=NoteCategory.WARNING, message=f'Unfamiliar Expert skill {self.skill} uses CSC fallback values'
            )
        ]

    @property
    def _resolved_spec(self) -> dict[str, int | float]:
        cls = type(self)
        return cls.KNOWN_SKILLS.get(self.skill, {'tl': cls.FALLBACK_TL, 'cost': cls.FALLBACK_COST})

    @property
    def _resolved_skill_name(self) -> str:
        return self.skill
