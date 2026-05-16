"""Gear equipment catalog — builds report context and renders HTML/PDF."""

from pathlib import Path
from typing import Literal

from ceres.report.render import render_html, render_pdf, render_typst_source
from ceres.shared import NoteList

from .comm import (
    LaserTransceiverEquipment,
    MesonTransceiverEquipment,
    RadioTransceiverEquipment,
    SatelliteUplinkPart,
    TransceiverEncryptionPart,
    TransceiverEquipment,
)
from .computer import (
    ComputerChip,
    ComputerEquipment,
    ComputerPart,
    ComputerTerminal,
    InterfaceDevice,
    MainframeComputer,
    MicroscopicChip,
    MidSizedComputer,
    PortableComputer,
    SpecialisedComputer,
    SpecialisedTablet,
    Tablet,
)
from .software import Expert

ReportTheme = Literal['light', 'dark']

__all__ = [
    'render_computer_catalog_html',
    'render_computer_catalog_pdf',
    'render_computer_catalog_typst',
    'render_communication_catalog_html',
    'render_communication_catalog_pdf',
    'render_communication_catalog_typst',
    'render_gear_catalog_html',
    'render_gear_catalog_pdf',
    'render_gear_catalog_typst',
]

_TEMPLATES = Path(__file__).parent / 'templates'

_COMPUTER_TYPES: list[type[ComputerEquipment]] = [
    ComputerTerminal,
    InterfaceDevice,
    MainframeComputer,
    MidSizedComputer,
    PortableComputer,
    Tablet,
    ComputerChip,
    MicroscopicChip,
]

_SPECIALISED_EXAMPLES: list[SpecialisedComputer] = [
    SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Admin'), variant='intelligent_interface'),
    SpecialisedComputer(processing=2, expert=Expert(rating=2, skill='Astrogation'), variant='intelligent_interface'),
    SpecialisedComputer(processing=1, expert=Expert(rating=1, skill='Medic'), variant='intelligent_interface'),
    SpecialisedTablet(processing=1, expert=Expert(rating=1, skill='Steward'), variant='intelligent_interface'),
    SpecialisedTablet(processing=2, expert=Expert(rating=2, skill='Medic'), variant='intelligent_interface'),
    SpecialisedComputer(processing=3, expert=Expert(rating=3, skill='Broker'), variant='intellect'),
    SpecialisedComputer(processing=2, expert=Expert(rating=2, skill='Engineer (M-Drive)'), variant='intellect'),
    SpecialisedTablet(processing=2, expert=Expert(rating=2, skill='Broker'), variant='intellect'),
]


def _fmt_cost(cost: float) -> str:
    if cost < 1:
        return f'Cr{cost:.2f}'
    return f'Cr{cost:,.0f}'


def _fmt_mass(mass: float) -> str:
    return f'{round(mass, 3):g}' if mass > 0 else '—'


def _fmt_range(range_km: int) -> str:
    return f'{range_km:,}km'


def _notes_for_display(item) -> list[dict]:
    return NoteList(getattr(item, 'notes', [])).detail_entries


def _standard_section(cls: type[ComputerEquipment]) -> dict:
    rows = []
    for p in sorted(cls._specs):
        item = cls(processing=p)
        rows.append(
            {
                'cells': [str(p), str(item.tl), _fmt_mass(item.mass_kg), _fmt_cost(item.cost)],
                'notes': _notes_for_display(item),
            }
        )
    return {
        'heading': cls(processing=min(cls._specs))._label,
        'headers': ['Processing', 'TL', 'Mass (kg)', 'Cost'],
        'alignments': ['left', 'right', 'right', 'right'],
        'rows': rows,
    }


def _retro_section(cls: type[ComputerEquipment]) -> dict:
    rows = []
    for tl in range(7, 17):
        for p in sorted(cls._specs):
            item = cls(processing=p)
            if item.tl < tl:
                item = cls(processing=p, tl=tl)
                rows.append(
                    {
                        'cells': [str(p), str(tl), _fmt_mass(item.mass_kg), _fmt_cost(item.cost)],
                        'notes': _notes_for_display(item),
                    }
                )
    return {
        'heading': 'Retrotech ' + cls(processing=min(cls._specs))._label,
        'headers': ['Processing', 'TL', 'Mass (kg)', 'Cost'],
        'alignments': ['left', 'right', 'right', 'right'],
        'rows': rows,
    }


def _proto_section(cls: type[ComputerEquipment]) -> dict:
    rows = []
    for tl in range(4, 15):
        for p in sorted(cls._specs):
            item = cls(processing=p)
            if item.tl > tl and item.tl < tl + 3:
                item = cls(processing=p, tl=tl)
                rows.append(
                    {
                        'cells': [str(p), str(tl), _fmt_mass(item.mass_kg), _fmt_cost(item.cost)],
                        'notes': _notes_for_display(item),
                    }
                )
    return {
        'heading': 'Prototech ' + cls(processing=min(cls._specs))._label,
        'headers': ['Processing', 'TL', 'Mass (kg)', 'Cost'],
        'alignments': ['left', 'right', 'right', 'right'],
        'rows': rows,
    }


def _specialised_section() -> dict:
    rows = []
    for sc in _SPECIALISED_EXAMPLES:
        name = sc.notes[0].message if sc.notes else ''
        rows.append(
            {
                'cells': [name, _fmt_mass(sc.mass_kg), str(sc.tl), _fmt_cost(sc.cost)],
                'notes': _notes_for_display(sc),
            }
        )
    return {
        'heading': 'Specialised Computer (examples)',
        'headers': ['Item', 'Mass (kg)', 'TL', 'Cost'],
        'alignments': ['left', 'right', 'right', 'right'],
        'rows': rows,
    }


def _transceiver_section(cls: type[TransceiverEquipment], heading: str) -> dict:
    rows = []
    specs = sorted(cls._specs, key=lambda key: (key[0], key[1]))
    for tl, range_km in specs:
        item = cls(range_km=range_km, tl=tl)
        computer = next((part.processing for part in item.parts if isinstance(part, ComputerPart)), None)
        rows.append(
            {
                'cells': [
                    str(tl),
                    _fmt_range(range_km),
                    _fmt_mass(item.mass_kg),
                    _fmt_cost(item.cost),
                    f'Computer/{computer}' if computer is not None else '—',
                ],
                'notes': _notes_for_display(item),
            }
        )
    return {
        'heading': heading,
        'headers': ['TL', 'Range', 'Mass (kg)', 'Cost', 'Integral Computer'],
        'alignments': ['right', 'left', 'right', 'right', 'left'],
        'rows': rows,
    }


def _radio_transceiver_section() -> dict:
    return _transceiver_section(RadioTransceiverEquipment, 'Radio Transceiver')


def _laser_transceiver_section() -> dict:
    return _transceiver_section(LaserTransceiverEquipment, 'Laser Transceiver')


def _meson_transceiver_section() -> dict:
    return _transceiver_section(MesonTransceiverEquipment, 'Meson Transceiver')


def _transceiver_options_section() -> dict:
    encryption = TransceiverEncryptionPart()
    standard_uplink = SatelliteUplinkPart(tl=6, cost=1_000.0, mass_kg=2.0)
    static_uplink = SatelliteUplinkPart(tl=6, cost=0.0, mass_kg=2.0, static=True)
    return {
        'heading': 'Transceiver Options',
        'headers': ['Option', 'TL', 'Effect/Limitation', 'Mass (kg)', 'Cost'],
        'alignments': ['left', 'right', 'left', 'right', 'right'],
        'rows': [
            {
                'cells': [
                    encryption.description,
                    str(encryption.tl),
                    'TL specific',
                    '—',
                    f'+{_fmt_cost(encryption.cost)}',
                ],
                'notes': [],
            },
            {
                'cells': [
                    standard_uplink.description,
                    str(standard_uplink.tl),
                    'x100 range, radio only, minimum 500km transceiver range',
                    '+100% or 2',
                    '+50% or Cr1,000',
                ],
                'notes': [],
            },
            {
                'cells': [
                    static_uplink.description,
                    str(static_uplink.tl),
                    'x100 range to fixed geostationary targets or satellite constellations',
                    '+100% or 2',
                    '+50%',
                ],
                'notes': [],
            },
        ],
    }


def _communication_sections() -> list[dict]:
    return [
        _laser_transceiver_section(),
        _radio_transceiver_section(),
        _meson_transceiver_section(),
        _transceiver_options_section(),
    ]


def _computer_sections() -> list[dict]:
    sections = [_standard_section(cls) for cls in _COMPUTER_TYPES]
    sections.extend(_retro_section(cls) for cls in _COMPUTER_TYPES if cls._allow_retro)
    sections.extend(_proto_section(cls) for cls in _COMPUTER_TYPES if cls._allow_proto)
    sections.append(_specialised_section())
    return sections


def _build_computer_context(*, theme: ReportTheme = 'light', page_size: str = 'a4') -> dict:
    return {
        'title': 'Computer Equipment',
        'eyebrow': 'Central Supply Catalogue',
        'theme': theme,
        'page_size': page_size,
        'sections': _computer_sections(),
    }


def _build_gear_context(*, theme: ReportTheme = 'light', page_size: str = 'a4') -> dict:
    return {
        'title': 'Gear Equipment',
        'eyebrow': 'Central Supply Catalogue',
        'theme': theme,
        'page_size': page_size,
        'sections': [*_computer_sections(), *_communication_sections()],
    }


def _build_communication_context(*, theme: ReportTheme = 'light', page_size: str = 'a4') -> dict:
    return {
        'title': 'Communication Equipment',
        'eyebrow': 'Central Supply Catalogue',
        'theme': theme,
        'page_size': page_size,
        'sections': _communication_sections(),
    }


def render_computer_catalog_html(*, theme: ReportTheme = 'light') -> str:
    return render_html(_TEMPLATES / 'computer_catalog.html.j2', _build_computer_context(theme=theme))


def render_computer_catalog_typst(*, page_size: str = 'a4') -> str:
    return render_typst_source(_TEMPLATES / 'computer_catalog.typ', _build_computer_context(page_size=page_size))


def render_computer_catalog_pdf(*, page_size: str = 'a4') -> bytes:
    return render_pdf(_TEMPLATES / 'computer_catalog.typ', _build_computer_context(page_size=page_size))


def render_communication_catalog_html(*, theme: ReportTheme = 'light') -> str:
    return render_html(_TEMPLATES / 'computer_catalog.html.j2', _build_communication_context(theme=theme))


def render_communication_catalog_typst(*, page_size: str = 'a4') -> str:
    return render_typst_source(_TEMPLATES / 'computer_catalog.typ', _build_communication_context(page_size=page_size))


def render_communication_catalog_pdf(*, page_size: str = 'a4') -> bytes:
    return render_pdf(_TEMPLATES / 'computer_catalog.typ', _build_communication_context(page_size=page_size))


def render_gear_catalog_html(*, theme: ReportTheme = 'light') -> str:
    return render_html(_TEMPLATES / 'computer_catalog.html.j2', _build_gear_context(theme=theme))


def render_gear_catalog_typst(*, page_size: str = 'a4') -> str:
    return render_typst_source(_TEMPLATES / 'computer_catalog.typ', _build_gear_context(page_size=page_size))


def render_gear_catalog_pdf(*, page_size: str = 'a4') -> bytes:
    return render_pdf(_TEMPLATES / 'computer_catalog.typ', _build_gear_context(page_size=page_size))
