"""
Only Computer Hardware Parts and Equipment in this file.
All software in software.py

TODO: Portable Computer Options not yet implemented:
  - Camera (TL8+, built-in still/video camera)
  - Comms (TL8+, short-range comm unit, no extra cost)
  - Data Display/Recorder (TL13, heads-up display, Cr500)
  - Data Wafer (TL8+, stores Bandwidth 0 or 1 programs, Cr5)
  - Physical User Interface (keyboard/screen at TL7, voice at TL8, holographic at TL12)

TODO: Specialised Computers not yet implemented:
  - Intelligent Interface variant: TL8, cost x5 of standard computer
  - Intellect variant: TL9, cost x10 of standard computer
"""

from typing import Any, ClassVar, Literal

from pydantic import Field, model_validator

from ceres.gear.software import Expert, SoftwarePackage
from ceres.shared import CeresPart, Equipment, Note, NoteCategory


class ComputerPart(CeresPart):
    processing: int

    def can_run(self, *packages: SoftwarePackage) -> bool:
        return sum(p.bandwidth for p in packages) <= self.processing


class ComputerEquipment(Equipment):
    processing: int | None = Field(default=None, exclude=True)
    parts: list[ComputerPart] = Field(default_factory=list)
    _label: ClassVar[str]
    _specs: ClassVar[dict[int, dict[str, int | float]]]

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
        part = ComputerPart(processing=processing, tl=int(spec['tl']), cost=float(spec['cost']))
        data.setdefault('parts', [part])
        data.setdefault('tl', part.tl)
        data.setdefault('cost', part.cost)
        data.setdefault('mass_kg', float(spec['mass_kg']))
        return data

    def can_run(self, *packages: SoftwarePackage) -> bool:
        return self.parts[0].can_run(*packages)

    def build_item(self) -> str | None:
        return f'{self._label}/{self.parts[0].processing}'


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
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 7, 'mass_kg': 5.0, 'cost': 500.0},
        1: {'tl': 8, 'mass_kg': 2.0, 'cost': 250.0},
        2: {'tl': 10, 'mass_kg': 0.5, 'cost': 500.0},
        3: {'tl': 12, 'mass_kg': 0.5, 'cost': 1_000.0},
        4: {'tl': 13, 'mass_kg': 0.5, 'cost': 1_500.0},
        5: {'tl': 14, 'mass_kg': 0.5, 'cost': 5_000.0},
    }


class Tablet(ComputerEquipment):
    _label = 'Tablet'
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
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: {'tl': 10, 'mass_kg': 0.0, 'cost': 62.5},
        1: {'tl': 11, 'mass_kg': 0.0, 'cost': 31.25},
        2: {'tl': 13, 'mass_kg': 0.0, 'cost': 62.5},
        3: {'tl': 15, 'mass_kg': 0.0, 'cost': 125.0},
        4: {'tl': 16, 'mass_kg': 0.0, 'cost': 187.5},
    }


class MicroscopicChip(ComputerEquipment):
    _label = 'Microscopic Chip'
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
# TL   = portable computer TL for that processing level
#
# Intelligent Interface variant (x5): requires at least skill 0 → DM+1
# Intellect variant (x10): allows unskilled use as if having skill Expert-1
# ---------------------------------------------------------------------------

_VARIANT_MULTIPLIER: dict[str, int] = {
    'intelligent_interface': 5,
    'intellect': 10,
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
        data.setdefault('tl', max(part.tl, expert.tl))
        data.setdefault('cost', total_cost)
        data.setdefault('mass_kg', float(spec['mass_kg']))
        return data

    def can_run(self, *packages: SoftwarePackage) -> bool:
        return self.parts[0].can_run(*packages)

    def build_item(self) -> str | None:
        if self.invalid_processing is not None:
            return None
        p = self.parts[0].processing
        variant_name = _VARIANT_FULL_NAME.get(self.variant, self.variant)
        return f'Specialised {type(self)._FORM_LABEL} {self.expert.skill}/{p} {variant_name}'

    def build_notes(self) -> list[Note]:
        if self.invalid_processing is not None:
            allowed = ', '.join(str(v) for v in sorted(type(self)._BASE_SPECS))
            return [
                Note(
                    category=NoteCategory.ERROR,
                    message=(
                        f'Unsupported {type(self).__name__} processing {self.invalid_processing}; '
                        f'expected one of: {allowed}'
                    ),
                )
            ]
        part = self.parts[0]
        if not part.can_run(self.expert):
            return [
                Note(
                    category=NoteCategory.ERROR,
                    message=(
                        f'Processing {part.processing} insufficient for '
                        f'Expert {self.expert.skill}/{self.expert.rating} '
                        f'(requires bandwidth {self.expert.bandwidth})'
                    ),
                )
            ]
        difficulty = _EXPERT_DIFFICULTY.get(self.expert.rating, f'rating {self.expert.rating}')
        skill = self.expert.skill
        notes = [Note(category=NoteCategory.INFO, message=f'DM+1 on {skill}, up to {difficulty}')]
        if self.variant == 'intellect':
            notes.append(
                Note(
                    category=NoteCategory.INFO,
                    message=f'{skill}-{self.expert.rating - 1} for unskilled, up to {difficulty}',
                )
            )
        return notes


class SpecialisedTablet(SpecialisedComputer):
    _BASE_SPECS: ClassVar[dict[int, dict[str, int | float]]] = Tablet._specs
    _FORM_LABEL: ClassVar[str] = 'Tablet'
