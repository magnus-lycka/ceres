"""
Only Computer Hardware Parts and Equipment in this file.
All software in software.py
"""

from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field, field_validator, model_validator

from ceres.gear.software import Expert
from ceres.shared import CeresPart, Equipment, NoteList, _Note

MAX_PROTO_LEVELS = 2


class ComputerPart(CeresPart):
    processing: int
    retro_levels: int = 0

    @property
    def description(self) -> str:
        return f'Computer/{self.processing}'


class ComputerEquipment(Equipment):
    processing: int | None = Field(default=None, exclude=True)
    parts: list[ComputerPart] = Field(default_factory=list)
    _label: ClassVar[str]
    _specs: ClassVar[dict[int, dict[str, int | float]]]
    _allow_retro: ClassVar[bool] = True
    _allow_proto: ClassVar[bool] = True

    @model_validator(mode='before')
    @classmethod
    def _resolve_processing(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        processing = data.get('processing')
        if processing is None or 'parts' in data:
            return data
        specs = cls._specs
        if processing not in specs:
            allowed = ', '.join(str(v) for v in sorted(specs))
            raise ValueError(f'Unsupported {cls.__name__} processing {processing}; expected one of: {allowed}')
        spec = specs[processing]
        given_tl = data.get('tl')
        if given_tl and given_tl > spec['tl']:
            if not cls._allow_retro:
                raise ValueError(f'Retro-tech not supported for {cls.__name__}')
            return cls.retro_spec(processing, data, spec, int(given_tl - spec['tl']))
        if given_tl and given_tl < spec['tl']:
            if not cls._allow_proto:
                raise ValueError(f'Proto-tech not supported for {cls.__name__}')
            return cls.proto_spec(processing, data, spec, int(spec['tl'] - given_tl))
        part = ComputerPart(processing=processing, tl=int(spec['tl']))
        data.setdefault('parts', [part])
        data.setdefault('tl', int(spec['tl']))
        data.setdefault('cost', float(spec['cost']))
        data.setdefault('mass_kg', float(spec['mass_kg']))
        return data

    @staticmethod
    def retro_spec(processing: int, data: dict, spec: dict, levels: int):
        factor = min(2**levels, 1_000)  # Don't be silly
        part = ComputerPart(processing=processing, tl=int(spec['tl']))
        data.setdefault('parts', [part])
        data.setdefault('tl', int(spec['tl']))
        data.setdefault('cost', float(spec['cost']) / factor)
        data.setdefault('mass_kg', float(spec['mass_kg']) / factor)
        return data

    def proto_spec(processing: int, data: dict, spec: dict, levels: int):
        if levels > MAX_PROTO_LEVELS:
            raise ValueError(f'Proto tech not available for {levels} TLs')
        factor = 10**levels
        part = ComputerPart(processing=processing, tl=int(spec['tl']))
        data.setdefault('parts', [part])
        data.setdefault('tl', int(spec['tl']))
        data.setdefault('cost', float(spec['cost']) * factor)
        data.setdefault('mass_kg', float(spec['mass_kg']) * factor)
        return data

    def item_description(self) -> str:
        return f'{self._label}/{self.parts[0].processing}'


class PortableComputerOption(CeresPart):
    kind: str
    label: ClassVar[str]

    @property
    def description(self) -> str:
        return type(self).label


class CameraOption(PortableComputerOption):
    kind: Literal['camera'] = 'camera'
    tl: int = 8
    cost: float = 0.0
    label: ClassVar[str] = 'Camera'


class CommsOption(PortableComputerOption):
    kind: Literal['comms'] = 'comms'
    tl: int = 8
    cost: float = 0.0
    label: ClassVar[str] = 'Comms'


class DataDisplayRecorderOption(PortableComputerOption):
    kind: Literal['data_display_recorder'] = 'data_display_recorder'
    tl: int = 13
    cost: float = 500.0
    label: ClassVar[str] = 'Data Display/Recorder'


class DataWaferOption(PortableComputerOption):
    kind: Literal['data_wafer'] = 'data_wafer'
    tl: int = 8
    cost: float = 5.0
    bandwidth: int = 0
    label: ClassVar[str] = 'Data Wafer'

    @field_validator('bandwidth')
    @classmethod
    def validate_bandwidth(cls, value: int) -> int:
        if value not in {0, 1}:
            raise ValueError('Data Wafer bandwidth must be 0 or 1')
        return value

    @property
    def description(self) -> str:
        return f'{self.label} (Bandwidth {self.bandwidth})'


class PhysicalUserInterfaceOption(PortableComputerOption):
    kind: Literal['physical_user_interface'] = 'physical_user_interface'
    interface: Literal['keyboard_screen', 'voice', 'holographic'] = 'voice'
    cost: float = 0.0
    label: ClassVar[str] = 'Physical User Interface'
    _INTERFACE_TL: ClassVar[dict[str, int]] = {
        'keyboard_screen': 7,
        'voice': 8,
        'holographic': 12,
    }
    _INTERFACE_LABEL: ClassVar[dict[str, str]] = {
        'keyboard_screen': 'Keyboard/Screen',
        'voice': 'Voice',
        'holographic': 'Holographic',
    }

    @model_validator(mode='before')
    @classmethod
    def _resolve_tl(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        interface = data.get('interface', 'voice')
        if interface in cls._INTERFACE_TL:
            data.setdefault('tl', cls._INTERFACE_TL[interface])
        return data

    @property
    def description(self) -> str:
        return f'{self.label} ({self._INTERFACE_LABEL[self.interface]})'


PortableComputerOptionUnion = Annotated[
    CameraOption | CommsOption | DataDisplayRecorderOption | DataWaferOption | PhysicalUserInterfaceOption,
    Field(discriminator='kind'),
]


# ---------------------------------------------------------------------------
# Computer Terminal / Interface Device (CSC p.66)
# Computer/0 only; can only run Interface software.
# ---------------------------------------------------------------------------


class ComputerTerminal(ComputerEquipment):
    _label = 'Computer Terminal'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 6, 'mass_kg': 2.0, 'cost': 200.0},
    }


class InterfaceDevice(ComputerEquipment):
    _label = 'Interface Device'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 8, 'mass_kg': 0.0, 'cost': 100.0},
    }


# ---------------------------------------------------------------------------
# Mainframe Computer (CSC p.66)
# ---------------------------------------------------------------------------


class MainframeComputer(ComputerEquipment):
    _label = 'Mainframe Computer'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 5, 'mass_kg': 5_000.0, 'cost': 2_000_000.0},
        1: {'tl': 6, 'mass_kg': 4_000.0, 'cost': 4_000_000.0},
        2: {'tl': 7, 'mass_kg': 1_000.0, 'cost': 5_000_000.0},
    }


# ---------------------------------------------------------------------------
# Mid-Sized Computer (CSC p.67)
# ---------------------------------------------------------------------------


class MidSizedComputer(ComputerEquipment):
    _label = 'Mid-Sized Computer'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 6, 'mass_kg': 500.0, 'cost': 500_000.0},
        1: {'tl': 7, 'mass_kg': 50.0, 'cost': 50_000.0},
        2: {'tl': 8, 'mass_kg': 10.0, 'cost': 10_000.0},
        3: {'tl': 9, 'mass_kg': 5.0, 'cost': 10_000.0},
        4: {'tl': 10, 'mass_kg': 5.0, 'cost': 10_000.0},
    }


# ---------------------------------------------------------------------------
# Portable Computer and size variants (CSC p.67)
# Mobile Comm is NOT a computer size variant — it is a telecommunications
# device and belongs in gear/communication.py (CommunicationEquipment).
# ---------------------------------------------------------------------------


class PortableComputer(ComputerEquipment):
    _label = 'Portable Computer'
    _allow_retro: ClassVar[bool] = False
    options: list[PortableComputerOptionUnion] = Field(default_factory=list)
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 7, 'mass_kg': 5.0, 'cost': 500.0},
        1: {'tl': 8, 'mass_kg': 2.0, 'cost': 250.0},
        2: {'tl': 10, 'mass_kg': 0.5, 'cost': 500.0},
        3: {'tl': 12, 'mass_kg': 0.5, 'cost': 1_000.0},
        4: {'tl': 13, 'mass_kg': 0.5, 'cost': 1_500.0},
        5: {'tl': 14, 'mass_kg': 0.5, 'cost': 5_000.0},
    }

    @model_validator(mode='after')
    def _validate_options(self):
        for option in self.options:
            if option.tl > self.tl:
                raise ValueError(f'{option.description} requires TL{option.tl}')
        processing = self.parts[0].processing
        spec = type(self)._specs[processing]
        proto_levels = max(0, int(spec['tl']) - self.tl)
        base_cost = float(spec['cost']) * (10**proto_levels)
        object.__setattr__(self, 'cost', base_cost + sum(option.cost for option in self.options))
        return self

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        for option in self.options:
            notes.content(option.description)
        return notes


class Tablet(ComputerEquipment):
    _label = 'Tablet'
    _allow_retro: ClassVar[bool] = False
    _allow_proto: ClassVar[bool] = False
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 8, 'mass_kg': 0.25, 'cost': 250.0},
        1: {'tl': 9, 'mass_kg': 0.25, 'cost': 125.0},
        2: {'tl': 11, 'mass_kg': 0.25, 'cost': 250.0},
        3: {'tl': 13, 'mass_kg': 0.25, 'cost': 500.0},
        4: {'tl': 14, 'mass_kg': 0.25, 'cost': 750.0},
        5: {'tl': 15, 'mass_kg': 0.25, 'cost': 2_500.0},
    }


class ComputerChip(ComputerEquipment):
    _label = 'Computer Chip'
    _allow_retro: ClassVar[bool] = False
    _allow_proto: ClassVar[bool] = False
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 10, 'mass_kg': 0.0, 'cost': 62.5},
        1: {'tl': 11, 'mass_kg': 0.0, 'cost': 31.25},
        2: {'tl': 13, 'mass_kg': 0.0, 'cost': 62.5},
        3: {'tl': 15, 'mass_kg': 0.0, 'cost': 125.0},
        4: {'tl': 16, 'mass_kg': 0.0, 'cost': 187.5},
    }


class MicroscopicChip(ComputerEquipment):
    _label = 'Microscopic Chip'
    _allow_retro: ClassVar[bool] = False
    _allow_proto: ClassVar[bool] = False
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 11, 'mass_kg': 0.0, 'cost': 31.25},
        1: {'tl': 12, 'mass_kg': 0.0, 'cost': 15.625},
        2: {'tl': 14, 'mass_kg': 0.0, 'cost': 31.25},
        3: {'tl': 16, 'mass_kg': 0.0, 'cost': 62.5},
    }


# ---------------------------------------------------------------------------
# Specialised Computer (CSC p.67)
#
# A portable computer hardwired for a single Expert skill package.
# All bandwidth is available for the Expert skill; cannot be reprogrammed.
#
# Cost = portable_computer_cost × variant_multiplier + expert_package_cost
# TL   = max(portable computer TL, variant TL, expert package TL)
#
# Intelligent Interface variant (x5): requires at least skill 0 → DM+1
# Intellect variant (x10): allows unskilled use as if having skill Expert-1
# ---------------------------------------------------------------------------

_VARIANT_MULTIPLIER: dict[str, int] = {
    'intelligent_interface': 5,
    'intellect': 10,
}

_VARIANT_TL: dict[str, int] = {
    'intelligent_interface': 8,
    'intellect': 9,
}

_VARIANT_FULL_NAME: dict[str, str] = {
    'intelligent_interface': 'Intelligent Interface',
    'intellect': 'Intellect',
}

_EXPERT_DIFFICULTY: dict[int, str] = {
    1: 'Average (8+)',
    2: 'Difficult (10+)',
    3: 'Very Difficult (12+)',
}


class SpecialisedComputer(Equipment):
    processing: int | None = Field(default=None, exclude=True)
    parts: list[ComputerPart] = Field(default_factory=list)
    expert: Expert
    variant: Literal['intelligent_interface', 'intellect']
    invalid_processing: int | None = None

    _BASE_SPECS: ClassVar[dict[int, dict[str, int | float]]] = PortableComputer._specs
    _FORM_LABEL: ClassVar[str] = 'Portable Computer'

    @model_validator(mode='before')
    @classmethod
    def _resolve_processing(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        processing = data.get('processing')
        if processing is None or 'parts' in data:
            return data
        base_specs = cls._BASE_SPECS
        if processing not in base_specs:
            data.setdefault('invalid_processing', processing)
            return data
        spec = base_specs[processing]
        part = ComputerPart(processing=processing, tl=int(spec['tl']), cost=float(spec['cost']))
        multiplier = _VARIANT_MULTIPLIER[data['variant']]
        raw_expert = data['expert']
        expert = raw_expert if isinstance(raw_expert, Expert) else Expert.model_validate(raw_expert)
        total_cost = float(spec['cost']) * multiplier + expert.cost
        data.setdefault('parts', [part])
        data.setdefault('tl', max(part.tl, expert.tl, _VARIANT_TL[data['variant']]))
        data.setdefault('cost', total_cost)
        data.setdefault('mass_kg', float(spec['mass_kg']))
        return data

    def item_description(self) -> str:
        if self.invalid_processing is not None:
            return ''
        p = self.parts[0].processing
        variant_name = _VARIANT_FULL_NAME.get(self.variant, self.variant)
        return f'Specialised {type(self)._FORM_LABEL} {self.expert.skill_name}/{p} {variant_name}'

    def build_notes(self) -> list[_Note]:
        if self.invalid_processing is not None:
            allowed = ', '.join(str(v) for v in sorted(type(self)._BASE_SPECS))
            notes = NoteList()
            notes.error(
                f'Unsupported {type(self).__name__} processing {self.invalid_processing}; expected one of: {allowed}'
            )
            return notes
        part = self.parts[0]
        if part.processing < self.expert.bandwidth:
            notes = NoteList()
            notes.error(
                f'Processing {part.processing} insufficient for '
                f'Expert {self.expert.skill_name}/{self.expert.rating} '
                f'(requires bandwidth {self.expert.bandwidth})'
            )
            return notes
        difficulty = _EXPERT_DIFFICULTY.get(self.expert.rating, f'rating {self.expert.rating}')
        skill = self.expert.skill_name
        notes = NoteList()
        notes.info(f'DM+1 on {skill}, up to {difficulty}')
        if self.variant == 'intellect':
            notes.info(f'{skill}-{self.expert.rating - 1} for unskilled, up to {difficulty}')
        return notes


class SpecialisedTablet(SpecialisedComputer):
    _BASE_SPECS: ClassVar[dict[int, dict[str, int | float]]] = Tablet._specs
    _FORM_LABEL: ClassVar[str] = 'Tablet'
